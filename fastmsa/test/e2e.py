"""E2E 테스트 모듈입니다."""
from collections import defaultdict

from fastmsa.core import AbstractPubsubClient


def check_port_opened(port: int):
    """e2e 테스트를 위해 포트 오픈 여부를 체크합니다."""
    import socket

    a_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        location = ("127.0.0.1", port)
        result_of_check = a_socket.connect_ex(location)

        if result_of_check == 0:
            return True
        else:
            return False

    finally:
        a_socket.close()


class FakeRedisClient(AbstractPubsubClient):
    def __init__(self):
        ...
        self.subscriptions = set()
        self.published_messages = defaultdict(list)

    async def subscribe_to(self, *channels):
        self.subscriptions = set(channels)

    async def publish_message(self, channel, message):
        self.published_messages[channel].append(message)

    def publish_message_sync(self, channel, message):
        self.published_messages[channel].append(message)

    async def wait_closed(self):
        ...
