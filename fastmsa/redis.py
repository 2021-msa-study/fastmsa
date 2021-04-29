from __future__ import annotations

import asyncio
import json
from dataclasses import asdict, dataclass, is_dataclass

import aioredis
from redis import Redis

from fastmsa.core import AbstractMessageBroker
from fastmsa.core.logging import get_logger

logger = get_logger("fastmsa.redis")


@dataclass
class RedisConnectInfo:
    host: str
    port: int

    @property
    def conn_args(self):
        return {"host": self.host, "port": self.port}


class RedisClient(AbstractMessageBroker):
    def __init__(self, info: RedisConnectInfo):
        self.redis = Redis(**asdict(info))
        self.info = info

    def subscribe_to(self, *channels: str):
        pubsub = self.redis.pubsub(ignore_subscribe_messages=True)
        pubsub.subscribe(*channels)
        return pubsub

    def publish_message(self, channel, message):
        data = message
        if is_dataclass(message):
            data = asdict(message)

        logger.info("publish message to %s: %r", channel, data)
        self.redis.publish(channel, json.dumps(data))


class AsyncRedisListener:
    def __init__(self, redis: AsyncRedisClient, channels, handler=None):
        self.channels = channels
        self.handler = handler
        self.redis = redis

    async def listen(self):
        async def reader(channel):
            async for ch, msg in channel.iter():
                logger.debug("Got message in channel: %r: %r", ch, msg)
                if self.handler:
                    await self.handler(self.redis.redis, channel, msg)

        for ch in self.channels:
            asyncio.get_running_loop().create_task(reader(ch))


class AsyncRedisClient(AbstractMessageBroker):
    def __init__(self, info: RedisConnectInfo, handler=None):
        self.url = f"redis://{info.host}:{info.port}"
        self.info = info
        self.redis = None
        self.handler = handler

    async def subscribe_to(self, *channels):
        if not self.redis:
            self.redis = await aioredis.create_redis_pool(self.url)
        self.channels = await self.redis.psubscribe(*channels)
        assert isinstance(self.channels[0], aioredis.Channel)
        return AsyncRedisListener(self, self.channels, self.handler)

    def publish_message(self, channel, message):
        data = message
        if is_dataclass(message):
            data = asdict(message)

        self.redis.publish(channel, json.dumps(data))

    async def wait_closed(self):
        if self.redis:
            await self.redis.wait_closed()
