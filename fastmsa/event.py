"""이벤트 드리븐 아키텍처를 위한 메세지 버스 관리 기능을 지원합니다.

주의:

    구현된 메시지 버스는 한 번에 하나의 핸들러만 실행되므로 동시성을 제공하지 않습니다.
    우리의 목표는 병렬 스레드를 지원하는 것이 아니라 개념적으로 작업을 분리하고 각
    UoW를 가능한 한 작게 유지하는 것입니다. 각 사용 사례의 실행 방법에 대한 "레시피"가
    한 곳에 기록되어 있기 때문에 코드베이스를 이해하는 데 도움이 됩니다.
"""
import logging
from collections import defaultdict
from typing import Any, Callable, Type, TypeVar

from tenacity import RetryError, Retrying, stop_after_attempt, wait_exponential

from fastmsa.core import Command, Event, Message
from fastmsa.uow import AbstractUnitOfWork

EventHandlerMap = dict[Type[Event], list[Callable]]
CommandHandlerMap = dict[Type[Command], Callable]
MessageHandlers = tuple[EventHandlerMap, CommandHandlerMap]

EVENT_HANDLERS: EventHandlerMap = defaultdict(list)
COMMAND_HANDLERS: CommandHandlerMap = defaultdict()


E = TypeVar("E", bound=Event)
C = TypeVar("C", bound=Command)
F = TypeVar("F", bound=Callable[..., Any])
T = TypeVar("T")

logger = logging.getLogger("fastmsa.core.event")


class MessageBus:
    event_handlers: EventHandlerMap = {}
    command_handlers: CommandHandlerMap = {}

    def __init__(
        self,
        handlers: MessageHandlers,
    ):
        self.event_handlers, self.command_handlers = handlers

    def handle(self, message: Message, uow: AbstractUnitOfWork):  # type: ignore
        queue = [message]
        results = []

        while queue:
            message = queue.pop(0)
            if isinstance(message, Event):
                self.handle_event(message, queue, uow)
            elif isinstance(message, Command):
                cmd_result = self.handle_command(message, queue, uow)
                results.append(cmd_result)
            else:
                raise Exception(f"{message} was not an Event or Command")
        return results

    def handle_event(self, event: Event, queue: list[Message], uow: AbstractUnitOfWork):
        for handler in self.event_handlers[type(event)]:
            try:
                retrying = Retrying(stop=stop_after_attempt(3), wait=wait_exponential())
                for attempt in retrying:
                    with attempt:
                        logger.debug(
                            "handling event %s with handler %s", event, handler
                        )
                        handler(event, uow=uow)
                        queue.extend(uow.collect_new_messages())
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
            handler = self.command_handlers[type(command)]
            result = handler(command, uow=uow)
            queue.extend(uow.collect_new_messages())
            return result
        except Exception:
            logger.exception("Exception handling command %s", command)
            raise


messagebus = MessageBus((EVENT_HANDLERS, COMMAND_HANDLERS))
"""전역 메세지 버스."""


def clear_handlers():
    """이벤트 핸들러를 초기화 합니다."""
    EVENT_HANDLERS.clear()
    COMMAND_HANDLERS.clear()


def on_event(etype: Type[E], bus: MessageBus = messagebus) -> Callable[[F], F]:
    """이벤트 핸들러 데코레이터.

    함수를 이벤트 핸들러 레지스트리에 등록합니다.
    """

    def _wrapper(func: F) -> F:
        bus.event_handlers[etype].append(func)
        return func

    return _wrapper


def on_command(etype: Type[C], bus: MessageBus = messagebus) -> Callable[[F], F]:
    """커맨드 핸들러 데코레이터.

    함수를 커맨드 핸들러 레지스트리에 등록합니다.
    """

    def _wrapper(func: F) -> F:
        assert not bus.command_handlers.get(etype)  # 이미 등록된 핸들러가 덮어씌우지지 않도록 방지
        bus.command_handlers[etype] = func
        return func

    return _wrapper
