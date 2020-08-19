from dataclasses import asdict
from dataclasses import dataclass

from airport.traits import Clone


def test_clone():
    @dataclass
    class Data(Clone):
        number: int
        string: str
        dictory: dict

    data = Data(number=1, string="a", dictory={"list": [1, 2, 3]})
    cloned_data = data.clone()

    assert data == cloned_data

    cloned_data.number += 1
    cloned_data.string = "b"
    cloned_data.dictory["list"].append(4)
    assert asdict(data) == {"number": 1, "string": "a", "dictory": {"list": [1, 2, 3]}}
