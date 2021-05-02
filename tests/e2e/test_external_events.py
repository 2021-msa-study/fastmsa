import asyncio
import json
from datetime import datetime
from typing import cast

import pytest
from httpx import AsyncClient

from fastmsa.api import AsyncAPIClient
from fastmsa.config import FastMSA
from fastmsa.redis import AsyncRedisClient, RedisMessageBroker
from fastmsa.test.e2e import check_port_opened
from tests import random_batchref, random_orderid, random_sku
from tests.app.domain import commands, events

pytestmark = pytest.mark.skipif(
    not check_port_opened(6379), reason="Redis server is not running"
)


@pytest.fixture(scope="module")
def event_loop():
    yield asyncio.get_event_loop()


@pytest.fixture
@pytest.mark.asyncio
async def api_client(msa: FastMSA) -> AsyncAPIClient:
    testclient = AsyncClient(app=msa.api, base_url="http://test")

    yield AsyncAPIClient(testclient)

    await testclient.aclose()


@pytest.fixture
def redis_client(msa: FastMSA):
    msa.allow_external_event = True

    yield AsyncRedisClient(msa.redis_conn_info)

    msa.allow_external_event = False


@pytest.mark.asyncio
async def test_change_batch_quantity_leading_to_reallocation(
    api_client: AsyncAPIClient,
    redis_client: AsyncRedisClient,
    msa: FastMSA,
):
    msa.allow_external_event = True
    listener = await msa.broker.listener
    tasks: list[asyncio.Task] = await listener.listen()

    async def test():
        # start with two batches and an order allocated to one of them
        orderid, sku = random_orderid(), random_sku()
        earlier_batch, later_batch = random_batchref(1), random_batchref(2)
        await api_client.post_to_add_batch(
            earlier_batch, sku, qty=10, eta=datetime(2021, 4, 26).isoformat()
        )
        await api_client.post_to_add_batch(
            later_batch, sku, qty=10, eta=datetime(2021, 4, 27).isoformat()
        )
        response = await api_client.post_to_allocate(orderid, sku, 10)
        assert response.json()["batchref"] == earlier_batch

        await redis_client.publish_message(
            commands.ChangeBatchQuantity, {"batchref": earlier_batch, "qty": 5}
        )

        await redis_client.subscribe_to(events.Allocated)
        channel = redis_client.channels[-1]

        async for msg in channel.iter(encoding="utf8"):
            data = json.loads(msg)
            assert data["orderid"] == orderid
            assert data["batchref"] == later_batch
            break

    try:
        await asyncio.wait_for(test(), timeout=3)
    except asyncio.TimeoutError:
        raise
    finally:
        for task in tasks:
            task.cancel()

        await redis_client.wait_closed()

        broker = cast(RedisMessageBroker, msa.broker)
        await broker.client.wait_closed()
