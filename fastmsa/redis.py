from __future__ import annotations

import asyncio
import json
from dataclasses import asdict, dataclass, is_dataclass
from typing import Callable, Optional, cast

import aioredis
from redis import Redis

from fastmsa.core import (
    AbstractFastMSA,
    AbstractMessageBroker,
    AbstractPubsub,
    AbstractPubsubClient,
)
from fastmsa.core.models import AbstractChannelListener
from fastmsa.event import messagebroker
from fastmsa.logging import get_logger

logger = get_logger("fastmsa.redis")


@dataclass
class RedisConnectInfo:
    host: str
    port: int

    @property
    def conn_args(self):
        return {"host": self.host, "port": self.port}


class RedisClient(AbstractPubsubClient):
    def __init__(self, info: RedisConnectInfo):
        self.redis = Redis(**asdict(info))
        self.info = info

    def subscribe_to(self, *channels) -> AbstractPubsub:
        str_channels: list[str] = [(ch.__name__ if type(ch) == type else ch) for ch in channels]  # type: ignore
        pubsub = self.redis.pubsub(ignore_subscribe_messages=True)
        pubsub.subscribe(*str_channels)
        return cast(AbstractPubsub, pubsub)

    def publish_message(self, channel, message):
        if type(channel) == type:
            channel = channel.__name__

        data = message
        if is_dataclass(message):
            data = asdict(message)

        logger.info("publish message to %s: %r", channel, data)
        self.redis.publish(channel, json.dumps(data))


ChannelMessageHandler = dict[str, Callable]


class AsyncRedisListener(AbstractChannelListener):
    def __init__(
        self,
        redis: AsyncRedisClient,
        channels,
        handlers: Optional[ChannelMessageHandler],
    ):
        self.channels = channels
        self.handlers = handlers
        self.redis = redis
        self.tasks = list[asyncio.Task]()

    async def listen(self) -> list[asyncio.Task]:
        async def reader(channel, handler):
            logger.debug("Listen from channel: %r", channel)
            async for msg in channel.iter(encoding="utf8"):
                data = json.loads(msg)
                logger.debug("Got message in channel: %r: %r", ch.name, data)
                if asyncio.iscoroutinefunction(handler):
                    await handler(self.redis, data)
                else:
                    handler(self.redis, data)

        self.tasks = []
        for ch in self.channels:
            channel_name = ch.name.decode()
            handler = self.handlers[channel_name]
            self.tasks.append(asyncio.create_task(reader(ch, handler)))

        return self.tasks


class AsyncRedisClient(AbstractPubsubClient):
    def __init__(
        self,
        info: RedisConnectInfo,
        handlers: ChannelMessageHandler = None,
    ):
        self.url = f"redis://{info.host}:{info.port}"
        self.info = info
        self.redis = None
        self.handler = handlers

    async def subscribe_to(self, *channels):
        str_channels: list[str] = [(ch.__name__ if type(ch) == type else ch) for ch in channels]  # type: ignore
        if not self.redis:
            self.redis = await aioredis.create_redis_pool(self.url)
        self.channels = await self.redis.subscribe(*str_channels)
        assert isinstance(self.channels[0], aioredis.Channel)
        return AsyncRedisListener(self, self.channels, self.handler)

    async def publish_message_async(self, channel, message):
        if type(channel) == type:
            channel = channel.__name__
        data = message
        if is_dataclass(message):
            data = asdict(message)
        if not self.redis:
            self.redis = await aioredis.create_redis_pool(self.url)
        await self.redis.publish(channel, json.dumps(data))

    def publish_message(self, channel, message):
        if type(channel) == type:
            channel = channel.__name__
        loop = asyncio.get_event_loop()
        loop.run_in_executor(None, self.publish_message_async, channel, message)

    async def wait_closed(self):
        if self.redis:
            self.redis.close()
            await self.redis.wait_closed()


class RedisMessageBroker(AbstractMessageBroker):
    """Redis로 구현된 외부 메세지 브로커입니다."""

    def __init__(
        self,
        conn_info: RedisConnectInfo,
        msa: AbstractFastMSA,
    ):

        self._broker = messagebroker
        self.conn_info = conn_info
        self.msa = msa or self.msa

        # Type[Message] -> Callble 타입의 매핑을 문자열 타입으로 바꿉니다.
        self.channel_handlers = {
            k.__name__: v[0] for k, v in self._broker.handlers.items()
        }
        self.aclient = AsyncRedisClient(self.conn_info, self.channel_handlers)
        self.client = RedisClient(self.conn_info)

    @property
    async def listener(self) -> AbstractChannelListener:
        channels = self.channel_handlers.keys()
        return await self.aclient.subscribe_to(*channels)

    async def main(self, wait_until_close=True):
        tasks = await (await self.listener).listen()
        # tasks.append(self.aclient.redis.wait_closed())
        try:
            if wait_until_close:
                await asyncio.gather(*tasks)
        finally:
            if self.aclient:
                await self.aclient.wait_closed()
