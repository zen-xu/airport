from dataclasses import dataclass
from dataclasses import field
from typing import TypeVar

from pydantic import BaseModel

from airport.kube.api import ResourceQuota
from airport.utils.cache import Heap
from airport.utils.cache import HeapError
from airport.utils.cache import HeapObjectNotFound


NamespaceWeightKey = "volcano.sh/namespace.weight"
DefaultNamespaceWeight = 1

T = TypeVar("T")


class NamespaceInfo(BaseModel):
    name: str = ""
    weight: int = 1


class QuotaItem(BaseModel):
    name: str = ""
    weight: int = 1

    @classmethod
    def new_from_resource_quota(cls, quota: ResourceQuota) -> "QuotaItem":
        weight: int
        try:
            quantity = quota.spec.hard[NamespaceWeightKey]
            weight = int(quantity)
        except KeyError:
            weight = DefaultNamespaceWeight

        assert quota.metadata is not None
        return cls(name=quota.metadata.name, weight=weight)


def quota_item_key_func(obj: QuotaItem) -> str:
    return obj.name


def quota_item_less_func(item1: QuotaItem, item2: QuotaItem) -> bool:
    return item1.weight > item2.weight


@dataclass
class NamespaceCollection:
    name: str = ""
    quota_weight: Heap = field(init=False)

    def __post_init__(self):
        heap = Heap.new(quota_item_key_func, quota_item_less_func)
        self.quota_weight = heap

        self.update_weight(
            QuotaItem(name=NamespaceWeightKey, weight=DefaultNamespaceWeight)
        )

    def update_weight(self, item: QuotaItem):
        self.quota_weight.update(item)

    def delete_weight(self, item: QuotaItem):
        self.quota_weight.delete(item)

    def update(self, quota: ResourceQuota):
        self.update_weight(QuotaItem.new_from_resource_quota(quota))

    def delete(self, quota: ResourceQuota):
        try:
            self.delete_weight(QuotaItem.new_from_resource_quota(quota))
        except HeapObjectNotFound:
            # ignore exception if quota not found
            pass

    def snapshot(self) -> "NamespaceInfo":
        try:
            quota_item: QuotaItem = self.quota_weight.pop()
            weight = quota_item.weight
            self.quota_weight.add(quota_item)
        except HeapError as e:
            print(f"namespace {self.name}, quota weight meets error {e} when pop")
            weight = DefaultNamespaceWeight

        return NamespaceInfo(name=self.name, weight=weight)
