"""샘플 이벤트 핸들러."""
from fastmsa.event import on_event

from ..domain.events import SampleEvent


@on_event(SampleEvent)
def print_sample(event: SampleEvent):
    """샘플 이벤트 메세지를 출력하는 핸들러."""
    print(event.msg)
