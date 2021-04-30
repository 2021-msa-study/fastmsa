"""이벤트 드리븐 아키텍처를 위한 메세지 버스 관리 기능을 지원합니다.

주의:

    구현된 메시지 버스는 한 번에 하나의 핸들러만 실행되므로 동시성을 제공하지 않습니다.
    우리의 목표는 병렬 스레드를 지원하는 것이 아니라 개념적으로 작업을 분리하고 각
    UoW를 가능한 한 작게 유지하는 것입니다. 각 사용 사례의 실행 방법에 대한 "레시피"가
    한 곳에 기록되어 있기 때문에 코드베이스를 이해하는 데 도움이 됩니다.
"""
import logging
from collections import defaultdict
from inspect import Parameter, signature
from typing import Any, Callable, Mapping, Optional, Type, TypeVar, Union

from tenacity import RetryError, Retrying, stop_after_attempt, wait_exponential
from uvicorn.logging import DefaultFormatter

from fastmsa.core import AbstractFastMSA, Command, Event, FastMSAError, Message
from fastmsa.uow import AbstractUnitOfWork

AnyMessageType = Union[Type[Event], Type[Command]]
MessageHandlerMap = dict[AnyMessageType, list[Callable]]

MESSAGE_HANDLERS: MessageHandlerMap = defaultdict(list)


E = TypeVar("E", bound=Event)
C = TypeVar("C", bound=Command)
F = TypeVar("F", bound=Callable[..., Any])
T = TypeVar("T")

logger = logging.getLogger("fastmsa.core.event")
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setFormatter(DefaultFormatter())
logger.addHandler(ch)


class MessageBus:
    handlers: MessageHandlerMap = {}
    params_cache: dict[Type[Message], Mapping[str, Parameter]] = {}
    msa: Optional[AbstractFastMSA] = None
    uow: Optional[AbstractUnitOfWork] = None

    def __init__(
        self,
        handlers: MessageHandlerMap,
        msa: Optional[AbstractFastMSA] = None,
    ):
        self.handlers = handlers
        self.msa = msa or self.msa

    def handle(self, message: Message, uow: Optional[AbstractUnitOfWork] = None):  # type: ignore
        queue = [message]
        results = []

        uow = uow or self.uow
        assert uow is not None

        while queue:
            message = queue.pop(0)
            logger.debug("handle message: %r, queue: %r", message, queue)

            if isinstance(message, Event):
                self.handle_event(message, queue, uow)
            elif isinstance(message, Command):
                cmd_result = self.handle_command(message, queue, uow)
                if cmd_result:
                    results.append(cmd_result)
            else:
                raise Exception(f"{message} was not an Event or Command")
        return results

    def handle_event(self, event: Event, queue: list[Message], uow: AbstractUnitOfWork):
        for handler in self.handlers[type(event)]:
            try:
                retrying = Retrying(stop=stop_after_attempt(3), wait=wait_exponential())
                for attempt in retrying:
                    logger.debug("handling event %s with handler %s", event, handler)
                    with attempt:
                        try:
                            self.call_handler(event, handler, uow)
                            queue.extend(uow.collect_new_messages())
                            logger.debug("retyring")
                        except:
                            logger.exception("Failed to handle event %r:", event)
            except RetryError as retry_failure:
                logger.error(
                    "Failed to handle event %s times, giving up!",
                    retry_failure.last_attempt.attempt_number,
                )
                continue

    def handle_command(
        self, command: Command, queue: list[Message], uow: AbstractUnitOfWork
    ):

        logger.debug("handling command %s", command)
        try:
            [handler] = self.handlers[type(command)]
            result = self.call_handler(command, handler, uow)
            queue.extend(uow.collect_new_messages())
            return result
        except Exception:
            logger.exception("Exception handling command %s", command)
            raise

    def call_handler(
        self, message: Message, handler: Callable, uow: AbstractUnitOfWork
    ):
        """핸들러의 파라메터를 보고 적절한 의존성을 주입하여 핸들러를 호출합니다.

        예를 들어 `def a_handler(uow, ..)` 와 같은 핸들러가 있을 경우 `uow`에
        대한 의존성을 주입합니다.
        """
        params = self.params_cache.get(type(message))
        if not params:
            return handler(message)

        args = {
            "uow": uow if "uow" in params else False,
            "msa": self.msa if "msa" in params else False,
        }

        missing = {k: v for k, v in args.items() if v is None}
        dependencies = {k: v for k, v in args.items() if v}  # pass found dependencies

        if not missing:
            return handler(message, **dependencies)
        else:
            logger.error(
                "HANDLER FAILED: message=%r, handler=%r, mssing dependencies: %r",
                message,
                handler,
                missing,
            )


messagebus = MessageBus(MESSAGE_HANDLERS)
"""전역 메세지 버스."""


def clear_handlers():
    """이벤트 핸들러를 초기화 합니다."""
    MESSAGE_HANDLERS.clear()


def on_event(etype: Type[E], bus: MessageBus = messagebus) -> Callable[[F], F]:
    """이벤트 핸들러 데코레이터.

    함수를 이벤트 핸들러 레지스트리에 등록합니다.
    """

    def _wrapper(func: F) -> F:

        bus.params_cache[etype] = signature(func).parameters
        bus.handlers[etype].append(func)
        return func

    return _wrapper


def on_command(etype: Type[C], bus: MessageBus = messagebus) -> Callable[[F], F]:
    """커맨드 핸들러 데코레이터.

    함수를 커맨드 핸들러 레지스트리에 등록합니다.
    """

    def _wrapper(func: F) -> F:
        # 이미 등록된 핸들러가 덮어씌우지지 않도록 방지
        handler = bus.handlers.get(etype)
        if handler:
            raise FastMSAError(f"Handler already exists for {etype}: {handler}")
        bus.params_cache[etype] = signature(func).parameters
        bus.handlers[etype] = [func]
        return func

    return _wrapper
