from __future__ import annotations

import abc
import asyncio
from contextlib import AbstractContextManager, ContextDecorator
from dataclasses import dataclass
from inspect import Parameter, signature
from pathlib import Path
from typing import (
    Any,
    Callable,
    Generator,
    Generic,
    List,
    Literal,
    Mapping,
    Optional,
    Protocol,
    Sequence,
    Type,
    TypeVar,
    Union,
)

from fastmsa.core.errors import FastMSAError


class Entity(Protocol):
    """Entity 프로토콜 명세."""

    id: Any  # PK 컬럼으로 id 라는 필드를 제공해야 합니다.


E = TypeVar("E", bound=Entity)


class Aggregate(Entity, Generic[E]):
    """Aggregate 프로토콜 명세."""

    items: list[E] = []
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


T = TypeVar("T")
A = TypeVar("A", bound=Aggregate)


class Event:
    """이벤트 객체.

    Events are broadcast by an actor to all interested listeners. When we
    publish BatchQuantityChanged, we don’t know who’s going to pick it up.
    We name events with past-tense verb phrases like “order allocated to stock”
    or “shipment delayed.”

    We often use events to spread the knowledge about successful commands.

    Events capture facts about things that happened in the past. Since we don’t
    know who’s handling an event, senders should not care whether the receivers
    succeeded or failed.
    """


class Command:
    """Command 객체.

    Commands are a type of message—instructions sent by one part of a system
    to another. We usually represent commands with dumb data structures and
    can handle them in much the same way as events

    Commands are sent by one actor to another specific actor with the expectation
    that a particular thing will happen as a result. When we post a form to an
    API handler, we are sending a command. We name commands with imperative mood
    verb phrases like “allocate stock” or “delay shipment.”

    Commands capture intent. They express our wish for the system to do something.
    As a result, when they fail, the sender needs to receive error information.
    """


Message = Union[Command, Event]

AnyMessageType = Union[Type[Event], Type[Command]]
MessageHandlerMap = dict[AnyMessageType, list[Callable]]


class AbstractPubsub(Protocol):
    def listen(self) -> Generator[Any, None, None]:
        ...

    def get_message(self, timeout: Optional[int] = None) -> Optional[dict[str, Any]]:
        ...


class AbstractPubsubClient(Protocol):
    async def subscribe_to(
        self, *channels: Union[str, Type]
    ) -> AbstractChannelListener:
        ...

    async def publish_message(self, channel: Union[str, Type], message: Any):
        ...

    def publish_message_sync(self, channel: Union[str, Type], message: Any):
        ...

    async def wait_closed(self):
        ...


class AbstractAPI(Protocol):
    def get(self):
        ...

    def put(self):
        ...

    def post(self):
        ...

    def delete(self):
        ...


class AbstractMessageHandler(Protocol):
    handlers: MessageHandlerMap = {}  # Dependency Injection
    params_cache: dict[Callable, Mapping[str, Parameter]] = {}
    """핸들러 파라메터 캐시. 이름이 따른 Dependency Injection을 위해 사용합니다."""
    msa: Optional[AbstractFastMSA] = None  # Dependency Injection
    uow: Optional[AbstractUnitOfWork] = None  # Dependency Injection
    pubsub: Optional[AbstractPubsubClient] = None  # Dependency Injection

    def register(self, etype: AnyMessageType, func: Callable):
        self.params_cache[func] = signature(func).parameters
        self.handlers[etype].append(func)


class AbstractChannelListener(Protocol):
    async def listen(self, *args, **kwargs) -> list[asyncio.Task]:
        ...


class AbstractMessageBroker(AbstractMessageHandler):

    client: AbstractPubsubClient

    @property
    async def listener(self) -> AbstractChannelListener:
        raise NotImplemented

    async def main(self, wait_until_close=True):
        raise NotImplemented


@dataclass
class AbstractFastMSA(abc.ABC):
    """FastMSA App 설정."""

    name: str
    title: str
    module_path: Path
    module_name: str
    allow_external_event = False

    """외부 메세지 브로커를 사용할지 여부."""
    is_implicit_name: bool = True
    """setup.cfg 없이 암시적으로 부여된 이름인지 여부."""

    @property
    def api(self) -> AbstractAPI:
        raise NotImplemented

    def get_api_host(self) -> str:
        """Get API server's host address."""
        return "127.0.0.1"

    def get_api_port(self) -> int:
        """Get API server's host port."""
        return 5000

    def get_api_url(self) -> str:
        """Get API server's full url."""
        return f"http://{self.get_api_host()}:{self.get_api_port()}"

    def get_db_url(self) -> str:
        """SqlAlchemy 에서 사용 가능한 형식의 DB URL을 리턴합니다.

        다음처럼 OS 환경변수를 이용할 수도 있씁니다.

        if self.mode == "prod":
            db_host = os.environ.get("DB_HOST", "localhost")
            db_user = os.environ.get("DB_USER", "postgres")
            db_pass = os.environ.get("DB_PASS", "password")
            db_name = os.environ.get("DB_NAME", db_user)
            return f"postgresql://{db_user}:{db_pass}@{db_host}/{db_name}"
        else:
            return f"sqlite://"
        """

        raise NotImplementedError

    def get_db_connect_args(self) -> dict[str, Any]:
        """Get db connection arguments for SQLAlchemy's engine creation.

        Example:
            For SQLite dbs, it could be: ::

                {'check_same_thread': False}
        """
        return {}

    @property
    def uow(self) -> AbstractUnitOfWork:
        raise NotImplemented

    @property
    def broker(self) -> Optional[AbstractMessageBroker]:
        raise NotImplemented

    def init_fastapi(self):
        """FastMSA 설정을 FastAPI 앱에 적용합니다."""
        from fastmsa.api import app

        app.title = self.title


class AbstractRepository(Generic[E], abc.ABC, ContextDecorator):
    """Repository 패턴의 추상 인터페이스 입니다."""

    entity_class: Type[E]

    def __init__(self):
        self.seen = set[E]()

    def __enter__(self) -> AbstractRepository[E]:
        """`module`:contextmanager`의 필수 인터페이스 구현."""
        return self

    def __exit__(
        self, typ: Any = None, value: Any = None, traceback: Any = None
    ) -> Literal[False]:
        self.close()
        return False

    def close(self) -> None:
        """레포지터리와 연결된 저장소 객체를 종료합니다."""
        return

    def add(self, item: E) -> None:
        """레포지터리에 :class:`T` 객체를 추가합니다."""
        self._add(item)
        self.seen.add(item)

    @abc.abstractmethod
    def _add(self, item: E) -> None:
        """레포지터리에 :class:`T` 객체를 추가합니다."""
        raise NotImplementedError

    def get(self, id: Any = "", **kwargs: str) -> Optional[E]:
        """주어진 레퍼런스 문자열에 해당하는 :class:`T` 객체를 조회합니다.

        객체를 찾았을 경우 `seen` 컬렉셔에 추가합니다.
        못 찾을 경우 ``None`` 을 리턴합니다.
        """
        item: Optional[E] = None

        if not kwargs:
            item = self._get(id)
        else:
            # get(by_field=value) 처럼 이름있는 파라메터에 `by_` 가 붙어있는 경우
            # _get_by_field 메소드를 호출하도록 라우팅 합니다.
            k, v = next((k, v) for k, v in kwargs.items())
            if k.startswith("by_"):
                method_name = "_get_" + k
                item = getattr(self, method_name)(v)
            else:
                item = self._get(id="", **kwargs)

        if item:
            self.seen.add(item)

        return item

    @abc.abstractmethod
    def _get(self, id: str = "", **kwargs: str) -> Optional[E]:
        """주어진 레퍼런스 문자열에 해당하는 :class:`T` 객체를 조회합니다.

        해당하는 배치를 못 찾을 경우 ``None`` 을 리턴합니다.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def all(self) -> List[E]:
        """모든 배치 객체 리스트를 조회합니다."""
        raise NotImplementedError

    @abc.abstractmethod
    def delete(self, item: E) -> None:
        """레포지터리에서 :class:`T` 객체를 삭제합니다."""
        raise NotImplementedError

    @abc.abstractmethod
    def clear(self) -> None:
        """레포지터리 내의 모든 엔티티 데이터를 지웁니다."""
        raise NotImplementedError


class AbstractSession(abc.ABC):
    """세션의 일반적인 작업(`commit`, `rollback`) 을 추상화한 클래스."""

    @abc.abstractmethod
    def commit(self) -> None:
        """트랜잭션을 커밋합니다."""
        raise NotImplementedError


AggregateReposMap = dict[Type[Aggregate], AbstractRepository]


class AbstractUowProtocol(Protocol):
    repos: AggregateReposMap
    agg_classes: Sequence[Type[Aggregate]]


class AbstractUnitOfWork(
    AbstractUowProtocol, AbstractContextManager["AbstractUnitOfWork"]
):
    """UnitOfWork 패턴의 추상 인터페이스입니다.

    UnitOfWork(UoW)는 영구 저장소의 유일한 진입점이며, 로드된 객체의
    최신 상태를 계속 트래킹 합니다.
    """

    repos: AggregateReposMap

    def __enter__(self) -> AbstractUnitOfWork:
        """``with`` 블록에 진입했을때 실행되는 메소드입니다."""
        return self

    def __exit__(self, *args: Any) -> None:
        """``with`` 블록에서 빠져나갈 때 실행되는 메소드입니다."""
        self.rollback()  # commit() 안되었을때 변경을 롤백합니다.
        # (이미 커밋 되었을 경우 rollback은 아무 효과도 없음)

    def __getitem__(self, key: Type[A]) -> AbstractRepository[A]:
        if key not in self.repos:
            raise FastMSAError("repostory not found for: %r" % key)
        return self.repos[key]

    def commit(self) -> None:
        """세션을 커밋합니다."""
        self._commit()

    def collect_new_messages(self):
        """처리된 Aggregate 객체에 추가된 이벤트를 수집합니다."""
        for repo in self.repos.values():
            for agg in repo.seen:
                while agg.messages:
                    yield agg.messages.pop(0)

    @abc.abstractmethod
    def _commit(self) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def rollback(self) -> None:
        """세션을 롤백합니다."""
        raise NotImplementedError
