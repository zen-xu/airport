from decimal import Decimal

import pytest

from airport.kube.api import KubeModel
from airport.kube.api import ResourceQuantity


parametrize = pytest.mark.parametrize


@parametrize(
    "resource_quantity,excepted",
    [
        (ResourceQuantity("1"), "1"),
        (ResourceQuantity("1.1"), "1.1"),
        (ResourceQuantity("10m"), "0.01"),
        (ResourceQuantity("10M"), str(10 * 1000 * 1000)),
        (ResourceQuantity("10Mi"), str(10 * 1024 * 1024)),
    ],
)
def test_resource_quantity(resource_quantity, excepted):
    assert resource_quantity == Decimal(excepted)


@parametrize(
    "name,op,excepted",
    [
        ("add", ResourceQuantity(100) + 2, ResourceQuantity("102")),
        ("sub", ResourceQuantity(100) - 2, ResourceQuantity("98")),
        ("mul", ResourceQuantity(100) * 2, ResourceQuantity("200")),
        (
            "truediv",
            ResourceQuantity(100) / 3,
            ResourceQuantity("33.33333333333333333333333333"),
        ),
        ("floordiv", ResourceQuantity(100) // 3, ResourceQuantity("33")),
        ("mod", ResourceQuantity(100) % 3, ResourceQuantity("1")),
        (
            "divmod",
            divmod(ResourceQuantity(100), 3),
            (ResourceQuantity("33"), ResourceQuantity("1")),
        ),
        ("pow", ResourceQuantity(100) ** 2, ResourceQuantity("10000")),
        ("neg", -ResourceQuantity(100), ResourceQuantity("-100")),
        ("abs", abs(ResourceQuantity(-100)), ResourceQuantity("100")),
    ],
)
def test_resource_quantity_ops(name, op, excepted):
    assert op == excepted
    if name == "divmod":
        assert excepted[0].__class__ == ResourceQuantity
        assert excepted[1].__class__ == ResourceQuantity
    else:
        assert op.__class__ == ResourceQuantity


@parametrize("subclass", KubeModel.__subclasses__())
def test_all_kube_models_have_default_value(subclass):
    subclass()
