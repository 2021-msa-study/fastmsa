"""이벤트 드리븐 아키텍처를 위한 메세지 버스 관리 기능을 지원합니다.

주의:

    구현된 메시지 버스는 한 번에 하나의 핸들러만 실행되므로 동시성을 제공하지 않습니다.
    우리의 목표는 병렬 스레드를 지원하는 것이 아니라 개념적으로 작업을 분리하고 각
    UoW를 가능한 한 작게 유지하는 것입니다. 각 사용 사례의 실행 방법에 대한 "레시피"가
    한 곳에 기록되어 있기 때문에 코드베이스를 이해하는 데 도움이 됩니다.
"""
from collections import defaultdict
from typing import Any, Callable, Type, TypeVar

from fastmsa.core import Event
from fastmsa.uow import AbstractUnitOfWork

EventHandlerMap = dict[Type[Event], list[Callable]]
HANDLERS: EventHandlerMap = defaultdict[Type[Event], list[Callable]](list)

E = TypeVar("E", bound=Event)
F = TypeVar("F", bound=Callable[..., Any])
T = TypeVar("T")


class MessageBus:
    handlers: EventHandlerMap

    def __init__(self, handlers: EventHandlerMap):
        self.handlers = handlers

    def handle(self, event: Event, uow: AbstractUnitOfWork[T]):  # type: ignore
        queue = [event]
        results = []

        while queue:
            event = queue.pop(0)
            for handler in self.handlers[type(event)]:
                results.append(handler(event, uow=uow))
                queue.extend(uow.collect_new_events())

        return results


messagebus = MessageBus(HANDLERS)
"""전역 메세지 버스."""


def clear_handlers():
    """이벤트 핸들러를 초기화 합니다."""
    HANDLERS.clear()


def on_event(etype: Type[E], bus: MessageBus = messagebus) -> Callable[[F], F]:
    """이벤트 핸들러 데코레이터.

    함수를 HANDLERS 레지스트리에 등록합니다.
    """

    def _wrapper(func: F) -> F:
        bus.handlers[etype].append(func)
        return func

    return _wrapper
