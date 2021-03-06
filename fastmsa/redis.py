from __future__ import annotations

import asyncio
import json
from dataclasses import asdict, dataclass, is_dataclass
from typing import Callable, Optional, Any

import aioredis  # type: ignore

from fastmsa.core import (
    AbstractChannelListener,
    AbstractFastMSA,
    AbstractMessageBroker,
    AbstractPubsubClient,
)
from fastmsa.event import messagebroker
from fastmsa.logging import get_logger
from fastmsa.utils import Fore, bold

logger = get_logger("fastmsa.redis")


@dataclass
class RedisConnectInfo:
    host: str
    port: int

    @property
    def conn_args(self):
        return {"host": self.host, "port": self.port}

    @property
    def url(self) -> str:
        return f"redis://{self.host}:{self.port}"


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

    async def listen(self) -> list[asyncio.Task[Any]]:
        async def reader(channel, handler):
            channel_name = channel.name.decode()
            logger.info("Listen from channel: %s", bold(channel_name, Fore.MAGENTA))
            async for msg in channel.iter(encoding="utf8"):
                try:
                    data = json.loads(msg)
                    logger.debug("Got message in channel: %s: %r", channel_name, data)
                    if asyncio.iscoroutinefunction(handler):
                        await handler(self.redis, data)
                    else:
                        handler(self.redis, data)
                except Exception as e:
                    logger.exception(
                        "%s on %s",
                        type(e).__qualname__,
                        bold(channel_name, Fore.MAGENTA),
                    )

        self.tasks = []
        for ch in self.channels:
            channel_name = ch.name.decode()
            assert self.handlers
            handler = self.handlers[channel_name]
            self.tasks.append(reader(ch, handler))

        return self.tasks


class AsyncRedisClient(AbstractPubsubClient):
    def __init__(
        self,
        info: RedisConnectInfo,
        handlers: ChannelMessageHandler = None,
    ):
        self.url = info.url
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

    async def publish_message(self, channel, message):
        if type(channel) == type:
            channel = channel.__name__
        data = message
        if is_dataclass(message):
            data = asdict(message)
        if not self.redis:
            self.redis = await aioredis.create_redis_pool(self.url)
        await self.redis.publish(channel, json.dumps(data))

    def publish_message_sync(self, channel, message):
        if type(channel) == type:
            channel = channel.__name__

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            loop.create_task(self.publish_message(channel, message))
        else:
            asyncio.run(self.publish_message(channel, message))

    async def wait_closed(self):
        if self.redis:
            self.redis.close()
            await self.redis.wait_closed()


class RedisMessageBroker(AbstractMessageBroker):
    """Redis??? ????????? ?????? ????????? ??????????????????."""

    def __init__(
        self,
        conn_info: RedisConnectInfo,
        msa: AbstractFastMSA,
    ):

        self._broker = messagebroker
        self.conn_info = conn_info
        self._msa = msa

        # Type[Message] -> Callble ????????? ????????? ????????? ???????????? ????????????.
        self.channel_handlers = {
            k.__name__: v[0] for k, v in self._broker.handlers.items()
        }
        self.client = AsyncRedisClient(self.conn_info, self.channel_handlers)

    @property
    def msa(self):
        return self._msa

    @msa.setter
    def msa(self, new_msa):
        self._msa = new_msa

    @property
    async def listener(self) -> AbstractChannelListener:
        channels = self.channel_handlers.keys()
        return await self.client.subscribe_to(*channels)

    async def main(self, wait_until_close=True):
        tasks = []
        logger.info(f"{bold('RedisMessageBroker')} started...")
        try:
            tasks = await (await self.listener).listen()
            if wait_until_close:
                await asyncio.gather(*tasks)
        except:
            # for task in tasks:
            #    task.cancel()
            ...
        finally:
            if self.client:
                await self.client.wait_closed()
