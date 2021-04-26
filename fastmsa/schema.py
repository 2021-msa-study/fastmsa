"""스키마 변환, 검증 조작등의 기능을 담당하는 모듈입니다."""
import collections
from dataclasses import Field as DataClassField
from inspect import getmembers
from types import GenericAlias
from typing import Any, Callable, Optional, Type, TypeVar, Union, cast

from pydantic import BaseModel, Field  # noqa
from pydantic.fields import FieldInfo  # noqa
from pydantic.main import ModelMetaclass

AnyType = Type[Any]

D = TypeVar("D")
T = TypeVar("T")

SCHEMAS = dict[Type, AnyType]()


def schema_from(
    DataClass: Type[D],
    excludes: Optional[list[str]] = None,
    orm_mode=False,
) -> Callable[[Type[T]], Type[Union[BaseModel, Type[D], Type[T]]]]:
    """`dataclasses.dataclass` 모델을 Pydantic `BaseModel` 로 변환합니다."""

    class ModelSchema(BaseModel):
        Config = collections.namedtuple(
            "Config",
            ["orm_mode"],
            defaults=[orm_mode],
        )

    members = dict[str, Any]()
    dataclass_fields = getattr(DataClass, "__dataclass_fields__", {})
    for name, field in dataclass_fields.items():
        members[name] = field

    def _wrapper(TargetClass: Type[T]):
        # 타겟 클래스의 필드 속성을 가져옵니다.
        for name, field in getmembers(TargetClass):
            if name.startswith("_"):
                continue
            if not isinstance(field, (FieldInfo,)):
                continue
            members[name] = field

        def _get_model(
            DataClass: Type[D], excludes=[]
        ) -> Type[Union[BaseModel, Type[D], Type[T]]]:
            from dataclasses import is_dataclass

            annotations = (
                dict(
                    (name, SCHEMAS.get(type, type))
                    for name, type in DataClass.__annotations__.items()
                    if not excludes or name not in excludes
                )
                if hasattr(DataClass, "__annotations__")
                else {}
            )

            for field_name, field_type in annotations.items():
                if type(field_type) == GenericAlias and field_type.__mro__[0] in [  # type: ignore
                    list,
                    set,
                ]:
                    gen_type = field_type.__mro__[0]
                    arg_type = field_type.__args__[0]
                    arg_type = SCHEMAS.get(arg_type, arg_type)
                    field_type.__args__[0]
                    annotations[field_name] = GenericAlias(gen_type, (arg_type,))  # type: ignore
                if is_dataclass(field_type):
                    field = _get_model(field_type)
                    annotations[field_name] = field

            namespace = {
                "__annotations__": annotations,
                "__module__": TargetClass.__module__,
                "__qualname__": TargetClass.__qualname__,
            }

            model = cast(
                AnyType,
                ModelMetaclass(TargetClass.__name__, (ModelSchema,), namespace),
            )

            for field_name, field_type in annotations.items():
                member = members.get(field_name)
                field = model.__dict__["__fields__"].get(field_name)
                if not field:
                    continue
                if isinstance(member, (DataClassField,)):
                    setattr(field, "field_info", Field(..., **member.metadata))
                elif isinstance(member, (FieldInfo,)):
                    setattr(field, "field_info", member)
            return model

        schema_class = _get_model(DataClass, excludes=excludes)
        SCHEMAS[DataClass] = schema_class
        return schema_class

    return _wrapper
