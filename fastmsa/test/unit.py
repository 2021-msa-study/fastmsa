"""Test 헬퍼를 제공하는 모듈.

- FakeRepository 나 FakeUoW 를 기본 제공합니다.

"""


"""서비스 레이어 단위 테스트.

Low Gear(고속 기어) 테스트입니다.
"""
from typing import Any, Callable, Optional, Type, TypeVar

from fastmsa.core import Event, FastMSA, FastMSAError
from fastmsa.domain import Aggregate, Entity
from fastmsa.event import HANDLERS, EventHandlerMap, MessageBus
from fastmsa.orm import AbstractSession
from fastmsa.repo import AbstractRepository
from fastmsa.uow import AbstractUnitOfWork

E = TypeVar("E", bound=Entity)
A = TypeVar("A", bound=Aggregate)


class FakeConfig(FastMSA):
    """단위 테스트를 위한 Fake 설정."""

    def __init__(self):
        super().__init__(__name__)

    def get_db_url(self):
        return "sqlite://"

    def init_mappers(self):
        pass

    def validate(self):
        pass


class FakeRepository(AbstractRepository[E]):
    """단위 테스트를 위한 Fake 레포지터리."""

    def __init__(self, id_field: str, items: Optional[list[E]] = None):
        super().__init__()
        self.id_field = id_field
        self._items = set(items) if items else set()

    def _add(self, item: E) -> None:
        self._items.add(item)

    def _get(self, id: str = "", **kwargs: str) -> Optional[E]:
        if not kwargs:
            item = next(
                (it for it in self._items if getattr(it, self.id_field) == id), None
            )
        else:
            check = lambda it: all(getattr(it, k) == v for k, v in kwargs.items())
            item = next((it for it in self._items if check(it)), None)

        return item

    def delete(self, batch: E) -> None:
        self._items.remove(batch)

    def all(self) -> list[E]:
        return list(self._items)

    def close(self) -> None:
        pass

    def clear(self) -> None:
        self._bacthes = set[E]()


class FakeSession(AbstractSession):
    """단위 테스트를 위한 Fake Session."""

    committed = False

    def commit(self) -> None:
        self.committed = True


R = TypeVar("R", bound=AbstractRepository)


class FakeUnitOfWork(AbstractUnitOfWork[A]):
    """단위 테스트를 위한 Fake UoW.

    Params:
        - agg_class: 사용되지는 않지만 타입 추론을 위해 필요 (지우지 말것)
    """

    def __init__(
        self,
        agg_class: Type[A],
        id_field: Optional[str] = None,
        items: Optional[list[A]] = None,
        repo: Optional[R] = None,
    ) -> None:
        super().__init__()
        if repo:
            self.repo = repo
        elif id_field is not None:
            self.repo = FakeRepository(id_field, items)
        else:
            raise FastMSAError("id_field or repo should be given!")
        self.committed = False

    def _commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        pass


class FakeMessageBus(MessageBus):
    def __init__(self, handlers: EventHandlerMap, fake_events: set[Type[Event]] = None):
        self.events_published = list[Event]()

        def get_fake_handler(
            e: Type[Event], handlers: list[Callable]
        ) -> list[Callable]:
            if fake_events and e in fake_events:
                # Fake 이벤트라면 이벤트를 실행하지 않고
                # events_published 에 추가하는 Fake 핸들러를 만들어 리턴한다.
                def fake_handler(e: Event, uow: Any = None):
                    self.events_published.append(e)

                return [fake_handler]
            return handlers

        self.fake_handlers = {k: get_fake_handler(k, v) for k, v in handlers.items()}
        super().__init__(self.fake_handlers)
