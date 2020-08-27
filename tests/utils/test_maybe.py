from returns.maybe import Nothing
from returns.maybe import Some

from airport.utils import BaseModel  # type: ignore
from airport.utils import Maybe  # type: ignore


class Point(BaseModel):
    x: int
    y: int


class DemoModel(BaseModel):
    value1: Maybe[int]
    value2: Maybe[Point]


def test_maybe():
    demo = DemoModel(value1=1, value2=Point(x=1, y=2))
    assert demo.value1 == Some(1)
    assert demo.value2 == Some(Point(x=1, y=2))


def test_maybe_with_default():
    demo = DemoModel()
    assert demo.value1 == demo.value2 == Nothing


def test_maybe_with_none():
    demo = DemoModel(value1=None, value2=None)
    assert demo.value1 == demo.value2 == Nothing


def test_maybe_to_json():
    demo = DemoModel(value1=1, value2=Point(x=1, y=2))
    assert demo.json() == '{"value1": 1, "value2": {"x": 1, "y": 2}}'


def test_maybe_none_to_json():
    demo = DemoModel(value1=None, value2=Point(x=1, y=2))
    assert demo.json() == '{"value1": null, "value2": {"x": 1, "y": 2}}'


def test_maybe_load_json():
    demo = DemoModel.parse_raw('{"value1": 1, "value2": {"x": 1, "y": 2}}')
    assert demo == DemoModel(value1=1, value2=Point(x=1, y=2))


def test_maybe_load_json_with_none():
    demo = DemoModel.parse_raw('{"value1": null, "value2": {"x": 1, "y": 2}}')
    assert demo == DemoModel(value1=None, value2=Point(x=1, y=2))


def test_maybe_load_dict():
    demo = DemoModel.parse_obj({"value1": 1, "value2": {"x": 1, "y": 2}})
    assert demo == DemoModel(value1=1, value2=Point(x=1, y=2))


def test_maybe_load_dict_with_none():
    demo = DemoModel.parse_obj({"value1": None, "value2": {"x": 1, "y": 2}})
    assert demo == DemoModel(value1=None, value2=Point(x=1, y=2))
