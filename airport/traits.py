from copy import deepcopy
from typing import TypeVar


T = TypeVar("T")


class Clone:
    def clone(self: T) -> T:
        return deepcopy(self)
