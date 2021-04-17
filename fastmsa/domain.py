from __future__ import annotations

from typing import Any, Generic, Sequence, Type, TypeVar, Protocol
from tests.app.domain.models import Batch, OrderLine, OutOfStock


class Entity(Protocol):
    """Entity 프로토콜 명세."""

    id: Any  # PK 컬럼으로 id 라는 필드를 제공해야 합니다.


T = TypeVar("T", bound=Entity)


class Aggregate(Generic[T]):
    items: list[T]

    class Meta:
        entity_class: Type
