"""Test 헬퍼를 제공하는 모듈.

- FakeRepository 나 FakeUoW 를 기본 제공합니다.

"""


"""서비스 레이어 단위 테스트.

Low Gear(고속 기어) 테스트입니다.
"""
from typing import Any, Callable, Optional, Type, TypeVar, Union

from fastmsa.core import (
    AbstractPubsubClient,
    AbstractRepository,
    AbstractSession,
    AbstractUnitOfWork,
    Aggregate,
    AggregateReposMap,
    Entity,
    Event,
    FastMSAError,
    Message,
)
from fastmsa.event import AnyMessageType, MessageBus

E = TypeVar("E", bound=Entity)
A = TypeVar("A", bound=Aggregate)


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


class FakeUnitOfWork(AbstractUnitOfWork):
    """단위 테스트를 위한 Fake UoW.

    Params:
        - agg_class: 사용되지는 않지만 타입 추론을 위해 필요 (지우지 말것)
    """

    def __init__(
        self,
        id_fields: Optional[dict[Type[Aggregate], str]] = None,
        items: Optional[list[Aggregate]] = None,
        repos: Optional[AggregateReposMap] = None,
    ) -> None:
        super().__init__()

        self.repos = {}
        if id_fields:
            for agg_class, id_field in id_fields.items():
                self.repos[agg_class] = FakeRepository(id_field, items)
        elif repos:
            self.repos = repos
        else:
            raise FastMSAError("id_fields or repos should be given!")
        self.committed = False

    def _commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        pass


class FakePubsubCilent(AbstractPubsubClient):
    def __init__(self, message_published: list[Message]):
        self.message_published = message_published

    def publish_message_sync(self, channel: Union[str, Type], message: Any):
        self.message_published.append(message)


class FakeMessageBus(MessageBus):
    def make_fake_handlers(
        self,
        messagebus: MessageBus,
        fake_messages: set[Type[Message]] = None,
    ):
        # Fake 이벤트라면 이벤트를 실행하지 않고
        # events_published 에 추가하는 Fake 핸들러를 만들어 리턴한다.
        def get_fake_handler(
            e: AnyMessageType, handlers: list[Callable]
        ) -> list[Callable]:
            if fake_messages and e in fake_messages:

                def fake_handler(e: Event, uow: Any = None):
                    self.message_published.append(e)

                return [fake_handler]
            return handlers

        return {k: get_fake_handler(k, v) for k, v in messagebus.handlers.items()}

    def __init__(
        self,
        messagebus: MessageBus,
        fake_messages: set[Type[Message]] = None,
        pubsub: Optional[AbstractPubsubClient] = None,
    ):

        self.message_published = list[Message]()

        super().__init__(
            self.make_fake_handlers(messagebus, fake_messages),
            pubsub=pubsub or FakePubsubCilent(self.message_published),
            uow=messagebus.uow,
        )
