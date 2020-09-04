from typing import Generic
from typing import List
from typing import Optional
from typing import TypeVar

from pydantic import BaseModel
from pydantic import ValidationError
from pydantic import validator
from pydantic.generics import GenericModel


DataT = TypeVar("DataT")


class Error(BaseModel):
    code: int
    message: str


class DataModel(BaseModel):
    numbers: List[int]
    people: List[str]


class Response(GenericModel, Generic[DataT]):
    data: Optional[DataT]
    error: Optional[Error]

    @validator("error", always=True)
    def check_consistency(cls, v, values):
        if v is not None and values["data"] is not None:
            raise ValueError("must not provide both data and error")
        if v is None and values.get("data") is None:
            raise ValueError("must provide data or error")
        return v
