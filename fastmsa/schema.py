"""스키마 변환, 검증 조작등의 기능을 담당하는 모듈입니다."""
from typing import Any, Type, cast, Callable, Optional
from dataclasses import is_dataclass

from pydantic import BaseModel
from pydantic.main import ModelMetaclass


AnyType = Type[Any]


def from_dataclass(
    DataClass: AnyType, excludes: Optional[list[str]] = None
) -> Callable[[AnyType], Type[Any]]:
    """`dataclasses.dataclass` 모델을 Pydantic `BaseModel` 로 변환합니다."""

    def _wrapper(TargetClass: AnyType):
        def _get_model(DataClass: AnyType) -> Type[Any]:
            annotations = list(
                (name, type)
                for name, type in DataClass.__annotations__.items()
                if excludes and name not in excludes
            )
            for field_name, field_type in annotations:
                if excludes and field_name in excludes:
                    continue

                if is_dataclass(field_type):
                    field = _get_model(field_type)
                    DataClass.__annotations__[field_name] = field

            namespace = {
                "__annotations__": dict(annotations),
                "__module__": TargetClass.__module__,
                "__qualname__": TargetClass.__qualname__,
            }
            return cast(
                Type[Any],
                ModelMetaclass(
                    TargetClass.__name__, (BaseModel, TargetClass), namespace
                ),
            )

        return _get_model(DataClass)

    return _wrapper
