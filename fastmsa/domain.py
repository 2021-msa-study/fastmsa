from __future__ import annotations

from typing import Any, Generic, Protocol, Type, TypeVar


class Entity(Protocol):
    """Entity 프로토콜 명세."""

    id: Any  # PK 컬럼으로 id 라는 필드를 제공해야 합니다.


E = TypeVar("E", bound=Entity)


class Aggregate(Entity, Generic[E]):
    items: list[E]
    type: Type[E]

    class Meta:
        entity_class: Type
