from __future__ import annotations

from typing import Any, Generic, Protocol, TypeVar


class Entity(Protocol):
    """Entity 프로토콜 명세."""

    id: Any  # PK 컬럼으로 id 라는 필드를 제공해야 합니다.


E = TypeVar("E", bound=Entity)


class Aggregate(Entity, Generic[E]):
    """Aggregate 프로토콜 명세."""

    items: list[E]
    _events: list[Event]

    def add_event(self, e: Event):
        if not hasattr(self, "_events"):
            self._events = list[Event]()

        self._events.append(e)

    @property
    def events(self) -> list[Event]:
        if not hasattr(self, "_events"):
            self._events = list[Event]()
        return self._events


class Event:
    pass
