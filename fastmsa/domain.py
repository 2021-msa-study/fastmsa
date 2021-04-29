from typing import Any, Generic, Protocol, TypeVar

from fastmsa.core import Message


class Entity(Protocol):
    """Entity 프로토콜 명세."""

    id: Any  # PK 컬럼으로 id 라는 필드를 제공해야 합니다.


E = TypeVar("E", bound=Entity)


class Aggregate(Entity, Generic[E]):
    """Aggregate 프로토콜 명세."""

    items: list[E]
    _messages: list[Message]

    def add_message(self, e: Message):
        if not hasattr(self, "_messages"):
            self._messages = list[Message]()

        self._messages.append(e)

    @property
    def messages(self) -> list[Message]:
        if not hasattr(self, "_messages"):
            self._messages = list[Message]()
        return self._messages
