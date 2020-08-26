from decimal import Decimal

import pytest

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
