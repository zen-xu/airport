# type: ignore

from typing import get_origin

from pydantic import BaseModel as _BaseModel
from pydantic import ValidationError
from pydantic import validator
from pydantic.fields import ModelField
from returns.maybe import Maybe
from returns.maybe import Nothing
from returns.maybe import Some
from returns.maybe import _Nothing  # noqa
from returns.maybe import _Some  # noqa


@classmethod  # noqa
def __get_validators__(cls):
    yield cls.validate


@classmethod  # noqa
def validate(cls, v, field: ModelField):
    if v in [None, Nothing]:
        return Nothing

    if isinstance(v, Maybe):
        v = v.unwrap()

    inner_field = field.sub_fields[0]
    valid_value, error = inner_field.validate(v, {}, loc=field.alias)
    if error:
        raise ValidationError([error], cls)
    return Some(valid_value)


def pre_root_validate(cls, input_data):
    for key, data in input_data.items():
        if data is None:
            input_data[key] = Nothing
    return input_data


def __repr__(self):
    return str(self)


Maybe.__get_validators__ = __get_validators__
Maybe.validate = validate
Maybe.__pre_root_validators__ = [pre_root_validate]
Maybe.pre_root_validate = pre_root_validate
Maybe.__repr__ = __repr__


class BaseModel(_BaseModel):
    class Config:
        @classmethod
        def prepare_field(cls, field: ModelField):
            if get_origin(field.type_) == Maybe:
                field.default = Nothing
                field.required = False
                field.allow_none = True

        json_encoders = {_Some: lambda v: v.unwrap(), _Nothing: lambda _: None}

    @validator("*", pre=True)
    def _convert_none_to_nothing(cls, value, field):  # noqa
        if field.type_ == Maybe and value is None:
            return Nothing
        return value
