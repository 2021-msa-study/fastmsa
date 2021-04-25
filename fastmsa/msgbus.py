"""이벤트 드리븐 아키텍처를 위한 메세지 버스 관리 기능을 지원합니다.

주의:

    구현된 메시지 버스는 한 번에 하나의 핸들러만 실행되므로 동시성을 제공하지 않습니다.
    우리의 목표는 병렬 스레드를 지원하는 것이 아니라 개념적으로 작업을 분리하고 각
    UoW를 가능한 한 작게 유지하는 것입니다. 각 사용 사례의 실행 방법에 대한 "레시피"가
    한 곳에 기록되어 있기 때문에 코드베이스를 이해하는 데 도움이 됩니다.
"""
from typing import Type, Callable
from collections import defaultdict

from fastmsa.domain import Event

HANDLERS = defaultdict[Type[Event], list[Callable]](list)


def handle(event: Event):
    """이벤트 핸들러에 레지스트리에서 `event` 와 관련된 모든 핸들러를 실행합니다."""
    for handler in HANDLERS[type(event)]:
        handler(event)


def clear_handlers():
    """이벤트 핸들러를 초기화 합니다."""
    HANDLERS.clear()


def event_handler(event: Type[Event]):
    """이벤트 핸들러 데코레이터.

    함수를 HANDLERS 레지스트리에 등록합니다.
    """
    global HANDLERS

    def _wrapper(func: Callable):
        HANDLERS[event].append(func)
        return func

    return _wrapper
