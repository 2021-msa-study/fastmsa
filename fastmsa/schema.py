"""스키마 변환, 검증 조작등의 기능을 담당하는 모듈입니다."""
import collections
from typing import Any, NamedTuple, Type, cast, Callable, Optional, TypeVar, Union

from pydantic import BaseModel
from pydantic.main import ModelMetaclass


AnyType = Type[Any]

D = TypeVar("D")
T = TypeVar("T")


def schema_from(
    DataClass: Type[D],
    excludes: Optional[list[str]] = None,
    orm_mode=False,
) -> Callable[[Type[T]], Type[Union[BaseModel, D, T]]]:
    """`dataclasses.dataclass` 모델을 Pydantic `BaseModel` 로 변환합니다."""

    class ModelSchema(BaseModel):
        Config = collections.namedtuple(
            "Config",
            ["orm_mode"],
            defaults=[orm_mode],
        )

    def _wrapper(TargetClass: Type[T]):
        def _get_model(DataClass: Type[D], excludes=[]) -> AnyType:
            from dataclasses import is_dataclass

            annotations = dict(
                (name, type)
                for name, type in DataClass.__annotations__.items()
                if not excludes or name not in excludes
            )

            for field_name, field_type in annotations.items():
                if is_dataclass(field_type):
                    field = _get_model(field_type)
                    annotations[field_name] = field

            namespace = {
                "__annotations__": annotations,
                "__module__": TargetClass.__module__,
                "__qualname__": TargetClass.__qualname__,
            }
            return cast(
                AnyType,
                ModelMetaclass(TargetClass.__name__, (ModelSchema,), namespace),
            )

        model = _get_model(DataClass, excludes=excludes)
        model.Config.orm_mode = orm_mode
        return model

    return _wrapper
