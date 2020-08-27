from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Type
from typing import Union

from pydantic import BaseModel
from returns.result import Failure
from returns.result import Result
from returns.result import Success

from airport.kube import helper
from airport.kube.api import ResourceList
from airport.kube.api import ResourceQuantity


MinMilliCpu: int = 10
MinMilliScalarResources: int = 10
MinMemory: int = 10 * 1024 * 1024


class Resource(BaseModel):
    milli_cpu: ResourceQuantity = ResourceQuantity(0)
    memory: ResourceQuantity = ResourceQuantity(0)
    scalar_resources: Dict[str, ResourceQuantity] = {}
    max_task_num: Optional[int] = None

    @property
    def resource_names(self) -> List[str]:
        return ["cpu", "memory", *self.scalar_resources.keys()]

    @classmethod
    def from_resource_list(
        cls: Type["Resource"], resource_list: Union[ResourceList, Dict[str, str]]
    ) -> "Resource":
        resource = cls()

        for resource_name, value in resource_list.items():
            if not value:
                continue

            value = ResourceQuantity(value)
            if resource_name == "cpu":
                resource.milli_cpu += value * 1000
            elif resource_name == "memory":
                resource.memory += value
            elif resource_name == "pods":
                resource.max_task_num = int(value)
            elif helper.is_scalar_resource_name(resource_name):
                resource.scalar_resources[resource_name] = value * 1000

        return resource

    def get(self, resource_name: str) -> Result[ResourceQuantity, ValueError]:
        if resource_name == "cpu":
            return Success(self.milli_cpu)
        elif resource_name == "memory":
            return Success(self.memory)
        else:
            try:
                return Success(self.scalar_resources[resource_name])
            except KeyError:
                return Failure(ValueError(f"Unknown resource {resource_name}"))

    def set_scalar_resource(
        self, resource_name: str, quantity: Union[float, ResourceQuantity]
    ):
        self.scalar_resources[resource_name] = ResourceQuantity(quantity)

    def is_empty(self) -> bool:
        """
        Returns bool after checking any of resource is less than min possible value
        """

        if self.milli_cpu >= MinMilliCpu or self.memory >= MinMemory:
            return False

        for quant in self.scalar_resources.values():
            if quant >= MinMilliScalarResources:
                return False

        return True

    def is_zero(self, resource_name: str) -> Result[bool, ValueError]:
        """
        Checks whether that resource is less than min possible value
        """

        if resource_name == "cpu":
            return Success(self.milli_cpu < MinMilliCpu)
        elif resource_name == "memory":
            return Success(self.memory < MinMemory)
        else:
            try:
                quantity = self.scalar_resources[resource_name]
                return Success(quantity < MinMilliScalarResources)
            except KeyError:
                return Failure(ValueError(f"Unknown resource {resource_name}"))

    def set_max_resource(self, other: "Resource") -> "Resource":
        self.milli_cpu = max(self.milli_cpu, other.milli_cpu)
        self.memory = max(self.memory, other.memory)

        for resource_name, other_quant in other.scalar_resources.items():
            self.scalar_resources[resource_name] = max(
                self.scalar_resources[resource_name], other_quant
            )

        return self

    def fit_delta(self, other: "Resource") -> "Resource":
        if other.milli_cpu > 0:
            self.milli_cpu -= other.milli_cpu + MinMilliCpu

        if other.memory > 0:
            self.memory -= other.memory + MinMemory

        for resource_name, other_quant in other.scalar_resources.items():
            if other_quant > 0:
                self.scalar_resources.setdefault(resource_name, ResourceQuantity(0))
                self.scalar_resources[resource_name] -= (
                    other_quant + MinMilliScalarResources
                )

        return self

    def diff(self: "Resource", other: "Resource") -> Tuple["Resource", "Resource"]:
        increase_value = Resource()
        decrease_value = Resource()

        if self.milli_cpu > other.milli_cpu:
            handle_value = increase_value
        else:
            handle_value = decrease_value
        handle_value.milli_cpu += abs(self.milli_cpu - other.milli_cpu)

        if self.memory > other.memory:
            handle_value = increase_value
        else:
            handle_value = decrease_value
        handle_value.memory += abs(self.memory - other.memory)

        for resource_name, quant in self.scalar_resources.items():
            other_quant = other.scalar_resources.get(resource_name, 0)

            if quant > other_quant:
                handle_value = increase_value
            else:
                handle_value = decrease_value
            handle_value.scalar_resources.setdefault(resource_name, ResourceQuantity(0))
            handle_value.scalar_resources[resource_name] += abs(quant - other_quant)

        return increase_value, decrease_value

    def less_equal_strict(self, other: "Resource") -> bool:
        if self.milli_cpu > other.milli_cpu or self.memory > other.memory:
            return False

        for resource_name, quant in self.scalar_resources.items():
            if (
                other_quant := other.scalar_resources.get(resource_name)
            ) is None or quant > other_quant:
                return False

        return True

    def greater_equal_strict(self, other: "Resource") -> bool:
        return other.less_equal_strict(self)

    def __eq__(self, other) -> bool:
        if abs(self.milli_cpu - other.milli_cpu) >= MinMilliCpu:
            return False

        if abs(self.memory - other.memory) >= MinMemory:
            return False

        resources_only_in_self = set(self.scalar_resources.keys()) - set(
            other.scalar_resources.keys()
        )
        for resource_name in resources_only_in_self:
            if self.scalar_resources[resource_name] >= MinMilliScalarResources:
                return False

        resources_only_in_other = set(other.resource_names) - set(self.resource_names)
        for resource_name in resources_only_in_other:
            if other.scalar_resources[resource_name] >= MinMilliScalarResources:
                return False

        resources_in_both = set(self.scalar_resources.keys()) & set(
            other.scalar_resources.keys()
        )
        for resource_name in resources_in_both:
            if (
                abs(
                    self.scalar_resources[resource_name]
                    - other.scalar_resources[resource_name]
                )
                >= MinMilliScalarResources
            ):
                return False

        return True

    def __lt__(self, other: "Resource") -> bool:
        if self.milli_cpu > other.milli_cpu or self.memory > other.memory:
            return False

        if not self.scalar_resources:
            return True

        if not other.scalar_resources:
            return False

        for resource_name, quant in self.scalar_resources.items():
            if quant > other.scalar_resources.get(resource_name, 0):
                return False

        return True

    def __le__(self, other: "Resource") -> bool:
        return self == other or self < other

    def __add__(self, other: "Resource") -> "Resource":
        resource: Resource = self.copy(deep=True)
        resource.milli_cpu += other.milli_cpu
        resource.memory += other.memory

        for resource_name, quant in other.scalar_resources.items():
            resource.scalar_resources.setdefault(resource_name, ResourceQuantity(0))
            resource.scalar_resources[resource_name] += quant

        return resource

    def __sub__(self, other: "Resource") -> "Resource":
        assert (
            self >= other
        ), f"resource is not sufficient to do operation: {self} sub {other}"

        resource: Resource = self.copy(deep=True)
        resource.milli_cpu -= other.milli_cpu
        resource.memory -= other.memory

        for resource_name, quant in other.scalar_resources.items():
            resource.scalar_resources.setdefault(resource_name, ResourceQuantity(0))
            resource.scalar_resources[resource_name] -= quant

        return resource

    def __mul__(self, ratio: int) -> "Resource":
        resource: Resource = self.copy(deep=True)

        resource.milli_cpu += ResourceQuantity(1)
        resource.milli_cpu *= ratio
        resource.memory *= ratio
        for resource_name, quant in resource.scalar_resources.items():
            resource.scalar_resources.setdefault(resource_name, ResourceQuantity(0))
            resource.scalar_resources[resource_name] *= ratio

        return resource
