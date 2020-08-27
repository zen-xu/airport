from typing import Tuple

import pytest

from returns.result import Failure
from returns.result import Result
from returns.result import Success

from airport.kube.api import ResourceQuantity
from airport.scheduler.api import Resource
from airport.scheduler.api._resource_info import MinMemory
from airport.scheduler.api._resource_info import MinMilliCpu
from airport.scheduler.api._resource_info import MinMilliScalarResources


parametrize = pytest.mark.parametrize


class TestResourceInfo:
    def test_resource_names(self):
        resource = Resource.new(
            {"cpu": "10m", "memory": "10Mi", "nvidia.com/gpu": "1Gi"}
        )
        assert resource.resource_names == ["cpu", "memory", "nvidia.com/gpu"]

    @parametrize(
        "resource_list,resource",
        [
            (
                {"cpu": "2000m", "memory": "1G", "pods": 20, "nvidia.com/gpu": "1G"},
                Resource(
                    milli_cpu=ResourceQuantity(2000),
                    memory=ResourceQuantity(1e9),
                    max_task_num=20,
                    scalar_resources={"nvidia.com/gpu": ResourceQuantity(1e12)},
                ),
            ),
            (
                {"cpu": "2000m", "memory": "1G", "pods": 20, "nvidia.com/gpu": ""},
                Resource(
                    milli_cpu=ResourceQuantity(2000),
                    memory=ResourceQuantity(1e9),
                    max_task_num=20,
                    scalar_resources={},
                ),
            ),
        ],
    )
    def test_new_resource(self, resource_list: dict, resource: Resource):
        assert Resource.new(resource_list) == resource

    @parametrize(
        "resource_name,quantity",
        [
            ("cpu", Success(100)),
            ("memory", Success(100)),
            ("nvidia.com/gpu", Success(100)),
            ("nvidia.com/cpu", Failure(ValueError("Unknown resource nvidia.com/cpu"))),
        ],
    )
    def test_get(
        self, resource_name: str, quantity: Result[ResourceQuantity, ValueError]
    ):
        resource = Resource(
            milli_cpu=ResourceQuantity(100),
            memory=ResourceQuantity(100),
            scalar_resources={"nvidia.com/gpu": ResourceQuantity(100)},
        )
        result = resource.get(resource_name)
        assert result.alt(lambda exception: exception.args) == quantity.alt(
            lambda exception: exception.args
        )

    def test_set_scalar_resource(self):
        empty_resource = Resource()
        empty_resource.set_scalar_resource("nvidia.com/gpu", 100)
        assert empty_resource == Resource(
            scalar_resources={"nvidia.com/gpu": ResourceQuantity(100)}
        )

    @parametrize(
        "resource_list,is_empty",
        [
            ({"cpu": "10m"}, False),
            ({"memory": "10Mi"}, False),
            ({"nvidia.com/gpu": "10m"}, False),
            ({"cpu": "9m", "memory": "10Mi"}, False),
            ({"cpu": "10m", "memory": "9Mi"}, False),
            ({"cpu": "9m", "memory": "9Mi"}, True),
        ],
    )
    def test_is_empty(self, resource_list: dict, is_empty: bool):
        resource = Resource.new(resource_list)
        assert resource.is_empty() == is_empty

    @parametrize(
        "resource_list,resource_name,is_zero",
        [
            ({"cpu": "9m", "memory": "9Mi"}, "cpu", Success(True)),
            ({"cpu": "10m", "memory": "10Mi"}, "cpu", Success(False)),
            ({"cpu": "9m", "memory": "9Mi"}, "memory", Success(True)),
            ({"cpu": "10m", "memory": "10Mi"}, "memory", Success(False)),
            ({"nvidia.com/gpu": "9m"}, "nvidia.com/gpu", Success(True)),
            ({"nvidia.com/gpu": "10m"}, "nvidia.com/gpu", Success(False)),
            (
                {"cpu": "10m", "memory": "10Mi"},
                "nvidia.com/gpu",
                Failure(ValueError("Unknown resource nvidia.com/gpu")),
            ),
        ],
    )
    def test_is_zero(
        self, resource_list: dict, resource_name: str, is_zero: Result[bool, ValueError]
    ):
        resource = Resource.new(resource_list)

        resource.is_zero(resource_name).alt(
            lambda exception: exception.args
        ) == is_zero.alt(lambda exception: exception.args)

    @parametrize(
        "left_resource_list,right_resource_list,excepted",
        [
            (
                {"cpu": "10m", "memory": "10Gi"},
                {"cpu": "1", "memory": "1Gi"},
                {"cpu": "1", "memory": "10Gi"},
            ),
            (
                {"cpu": "20m", "nvidia.com/gpu": "1Gi"},
                {"cpu": "10m", "nvidia.com/gpu": "10Gi"},
                {"cpu": "20m", "nvidia.com/gpu": "10Gi"},
            ),
        ],
    )
    def test_set_max_resource(
        self, left_resource_list: dict, right_resource_list: dict, excepted: dict
    ):
        left_resource = Resource.new(left_resource_list)
        right_resource = Resource.new(right_resource_list)
        excepted_resource = Resource.new(excepted)
        assert excepted_resource == left_resource.set_max_resource(right_resource)

    @parametrize(
        "left_resource,right_resource,excepted",
        [
            (
                Resource(
                    milli_cpu=ResourceQuantity(1000),
                    memory=ResourceQuantity(20 * 1024 * 1024),
                    scalar_resources={"nvidia.com/gpu": ResourceQuantity(200)},
                ),
                Resource(
                    milli_cpu=ResourceQuantity(100),
                    memory=ResourceQuantity(1024),
                    scalar_resources={
                        "nvidia.com/gpu": ResourceQuantity(100),
                        "nvidia.com/gpu-tesla-p100-16GB": ResourceQuantity(200),
                    },
                ),
                Resource(
                    milli_cpu=ResourceQuantity(1000 - (100 + MinMilliCpu)),
                    memory=ResourceQuantity(20 * 1024 * 1024 - (1024 + MinMemory)),
                    scalar_resources={
                        "nvidia.com/gpu": ResourceQuantity(
                            200 - (100 + MinMilliScalarResources)
                        ),
                        "nvidia.com/gpu-tesla-p100-16GB": ResourceQuantity(
                            0 - (200 + MinMilliScalarResources)
                        ),
                    },
                ),
            ),
        ],
    )
    def test_fit_deta(
        self, left_resource: Resource, right_resource: Resource, excepted: Resource
    ):
        assert left_resource.fit_delta(right_resource) == excepted

    @parametrize(
        "left_resource,right_resource,excepted",
        [
            (
                Resource(
                    milli_cpu=ResourceQuantity(1000),
                    memory=ResourceQuantity(200),
                    scalar_resources={"nvidia.com/gpu": ResourceQuantity(200)},
                ),
                Resource(
                    milli_cpu=ResourceQuantity(100),
                    memory=ResourceQuantity(1000),
                    scalar_resources={
                        "nvidia.com/gpu": ResourceQuantity(100),
                        "nvidia.com/gpu-tesla-p100-16GB": ResourceQuantity(200),
                    },
                ),
                (
                    Resource(
                        milli_cpu=ResourceQuantity(900),
                        scalar_resources={"nvidia.com/gpu": ResourceQuantity(100)},
                    ),
                    Resource(memory=ResourceQuantity(800)),
                ),
            ),
            (
                Resource(
                    milli_cpu=ResourceQuantity(100),
                    memory=ResourceQuantity(1000),
                    scalar_resources={
                        "nvidia.com/gpu": ResourceQuantity(100),
                        "nvidia.com/gpu-tesla-p100-16GB": ResourceQuantity(200),
                    },
                ),
                Resource(
                    milli_cpu=ResourceQuantity(1000),
                    memory=ResourceQuantity(200),
                    scalar_resources={"nvidia.com/gpu": ResourceQuantity(200)},
                ),
                (
                    Resource(
                        memory=ResourceQuantity(800),
                        scalar_resources={
                            "nvidia.com/gpu-tesla-p100-16GB": ResourceQuantity(200)
                        },
                    ),
                    Resource(
                        milli_cpu=ResourceQuantity(900),
                        scalar_resources={"nvidia.com/gpu": ResourceQuantity(100)},
                    ),
                ),
            ),
        ],
    )
    def test_diff(
        self,
        left_resource: Resource,
        right_resource: Resource,
        excepted: Tuple[Resource, Resource],
    ):
        assert left_resource.diff(right_resource) == excepted

    @parametrize(
        "left_resource_list,right_resource_list,excepted",
        [
            ({"cpu": "10m"}, {"cpu": "20m"}, True),
            ({"cpu": "10m"}, {"cpu": "10m"}, True),
            ({"memory": "1Gi"}, {"memory": "2Gi"}, True),
            ({"memory": "1Gi"}, {"memory": "1Gi"}, True),
            ({"nvidia.com/gpu": "1Gi"}, {"nvidia.com/gpu": "2Gi"}, True),
            ({"nvidia.com/gpu": "1Gi"}, {"nvidia.com/gpu": "1Gi"}, True),
            ({"cpu": "10m", "memory": "1Gi"}, {"cpu": "20m", "memory": "100Mi"}, False),
            (
                {"cpu": "10m", "nvidia.com/gpu": "1Gi"},
                {"cpu": "20m", "nvidia.com/gpu": "100Mi"},
                False,
            ),
            ({"cpu": "10m"}, {"cpu": "20m", "nvidia.com/gpu": "100Mi"}, True),
            ({"cpu": "10m", "nvidia.com/gpu": "100Mi"}, {"cpu": "20m"}, False),
            ({"cpu": "100m", "nvidia.com/gpu": ""}, {"cpu": "300m"}, True),
            ({"cpu": "100m"}, {"cpu": "300m", "nvidia.com/gpu": ""}, True),
        ],
    )
    def test_less_equal_strict(
        self, left_resource_list: dict, right_resource_list: dict, excepted: bool
    ):
        left_resource = Resource.new(left_resource_list)
        right_resource = Resource.new(right_resource_list)
        assert left_resource.less_equal_strict(right_resource) == excepted

    @parametrize(
        "left_resource_list,right_resource_list,excepted",
        [
            ({"cpu": "20m"}, {"cpu": "10m"}, True),
            ({"cpu": "10m"}, {"cpu": "10m"}, True),
            ({"memory": "2Gi"}, {"memory": "1Gi"}, True),
            ({"memory": "1Gi"}, {"memory": "1Gi"}, True),
            ({"nvidia.com/gpu": "2Gi"}, {"nvidia.com/gpu": "1Gi"}, True),
            ({"nvidia.com/gpu": "1Gi"}, {"nvidia.com/gpu": "1Gi"}, True),
            ({"cpu": "20m", "memory": "100Mi"}, {"cpu": "10m", "memory": "1Gi"}, False),
            (
                {"cpu": "20m", "nvidia.com/gpu": "100Mi"},
                {"cpu": "10m", "nvidia.com/gpu": "1Gi"},
                False,
            ),
            ({"cpu": "30m"}, {"cpu": "20m", "nvidia.com/gpu": "100Mi"}, False),
            ({"cpu": "30m", "nvidia.com/gpu": "100Mi"}, {"cpu": "20m"}, True),
            ({"cpu": "300m", "nvidia.com/gpu": ""}, {"cpu": "100m"}, True),
            ({"cpu": "300m"}, {"cpu": "100m", "nvidia.com/gpu": ""}, True),
        ],
    )
    def test_greater_equal_strict(
        self, left_resource_list: dict, right_resource_list: dict, excepted: bool
    ):
        left_resource = Resource.new(left_resource_list)
        right_resource = Resource.new(right_resource_list)
        assert left_resource.greater_equal_strict(right_resource) == excepted

    @parametrize(
        "left_resource_list,right_resource_list,excepted",
        [
            ({"cpu": "100m"}, {"cpu": "110m"}, False),
            ({"cpu": "109m"}, {"cpu": "100m"}, True),
            ({"memory": "10Mi"}, {"memory": "20Mi"}, False),
            ({"memory": "19Mi"}, {"memory": "10Mi"}, True),
            ({"nvidia.com/gpu": "100m"}, {"nvidia.com/gpu": "110m"}, False),
            ({"nvidia.com/gpu": "109m"}, {"nvidia.com/gpu": "100m"}, True),
            ({"cpu": "100m", "nvidia.com/gpu": "8m"}, {"cpu": "100m"}, True),
            ({"cpu": "100m", "nvidia.com/gpu": "11m"}, {"cpu": "100m"}, False),
            ({"cpu": "100m"}, {"cpu": "100m", "nvidia.com/gpu": "11m"}, False),
            ({"cpu": "100m", "nvidia.com/gpu": ""}, {"cpu": "100m"}, True),
            ({"cpu": "100m"}, {"cpu": "100m", "nvidia.com/gpu": ""}, True),
        ],
    )
    def test_equal(
        self, left_resource_list: dict, right_resource_list: dict, excepted: bool
    ):
        left_resource = Resource.new(left_resource_list)
        right_resource = Resource.new(right_resource_list)
        assert (left_resource == right_resource) == excepted

    @parametrize(
        "left_resource_list,right_resource_list,excepted",
        [
            ({"cpu": "100m"}, {"cpu": "101m"}, True),
            ({"cpu": "101m"}, {"cpu": "100m"}, False),
            ({"memory": "10Mi"}, {"memory": "11Mi"}, True),
            ({"memory": "11Mi"}, {"memory": "10Mi"}, False),
            ({"nvidia.com/gpu": "100m"}, {"nvidia.com/gpu": "101m"}, True),
            ({"nvidia.com/gpu": "101m"}, {"nvidia.com/gpu": "100m"}, False),
            ({"cpu": "100m", "nvidia.com/gpu": "8m"}, {"cpu": "101m"}, False),
            ({"cpu": "100m", "nvidia.com/gpu": "11m"}, {"cpu": "101m"}, False),
            ({"cpu": "100m", "nvidia.com/gpu": ""}, {"cpu": "300m"}, True),
            ({"cpu": "100m"}, {"cpu": "300m", "nvidia.com/gpu": ""}, True),
        ],
    )
    def test_less(
        self, left_resource_list: dict, right_resource_list: dict, excepted: bool
    ):
        left_resource = Resource.new(left_resource_list)
        right_resource = Resource.new(right_resource_list)
        assert (left_resource < right_resource) == excepted

    @parametrize(
        "left_resource_list,right_resource_list,excepted",
        [
            ({"cpu": "100m"}, {"cpu": "101m"}, {"cpu": "201m"}),
            ({"memory": "10Mi"}, {"memory": "11Mi"}, {"memory": "21Mi"}),
            (
                {"nvidia.com/gpu": "100m"},
                {"nvidia.com/gpu": "101m"},
                {"nvidia.com/gpu": "201m"},
            ),
            (
                {"cpu": "100m", "nvidia.com/gpu": "8m"},
                {"cpu": "101m"},
                {"cpu": "201m", "nvidia.com/gpu": "8m"},
            ),
        ],
    )
    def test_add(
        self, left_resource_list: dict, right_resource_list: dict, excepted: dict
    ):
        left_resource = Resource.new(left_resource_list)
        right_resource = Resource.new(right_resource_list)
        excpeted_resource = Resource.new(excepted)
        assert left_resource + right_resource == excpeted_resource

    @parametrize(
        "left_resource_list,right_resource_list,excepted",
        [
            ({"cpu": "200m"}, {"cpu": "101m"}, {"cpu": "99m"}),
            ({"memory": "20Mi"}, {"memory": "11Mi"}, {"memory": "9Mi"}),
            (
                {"nvidia.com/gpu": "200m"},
                {"nvidia.com/gpu": "101m"},
                {"nvidia.com/gpu": "99m"},
            ),
            (
                {"cpu": "200m", "nvidia.com/gpu": "8m"},
                {"cpu": "101m"},
                {"cpu": "99m", "nvidia.com/gpu": "8m"},
            ),
            pytest.param(
                {"cpu": "200m", "nvidia.com/gpu": "8m"},
                {"cpu": "300m"},
                {"cpu": "100m"},
                marks=pytest.mark.xfail(raises=AssertionError),
            ),
        ],
    )
    def test_sub(
        self, left_resource_list: dict, right_resource_list: dict, excepted: dict
    ):
        left_resource = Resource.new(left_resource_list)
        right_resource = Resource.new(right_resource_list)
        excpeted_resource = Resource.new(excepted)
        assert left_resource - right_resource == excpeted_resource

    @parametrize(
        "resource_list,ratio,excepted",
        [
            (
                {"cpu": "200m", "memory": "20Mi", "nvidia.com/gpu": "1Gi"},
                2,
                {"cpu": "400m", "memory": "40Mi", "nvidia.com/gpu": "2Gi"},
            )
        ],
    )
    def test_multi(self, resource_list: dict, ratio: int, excepted: dict):
        resource = Resource.new(resource_list)
        excepted_resource = Resource.new(excepted)
        assert resource * ratio == excepted_resource
