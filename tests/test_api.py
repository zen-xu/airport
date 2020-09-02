import pytest

from airport.api.batch import *
from airport.api.bus import *
from airport.api.scheduling import KubeModel
from airport.api.scheduling import *


parametrize = pytest.mark.parametrize


@parametrize("subclass", KubeModel.__subclasses__())
def test_all_kube_models_have_default_value(subclass):
    subclass()
