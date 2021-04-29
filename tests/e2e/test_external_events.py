import json
from datetime import datetime

import pytest
from tenacity import Retrying, stop_after_delay

from fastmsa.api import APIClient
from fastmsa.config import FastMSA
from fastmsa.redis import RedisClient
from fastmsa.test import TestClient
from tests import random_batchref, random_orderid, random_sku


@pytest.fixture
def api_client(msa: FastMSA) -> APIClient:
    testclient = TestClient(msa.api)
    return APIClient(testclient)


@pytest.fixture
def redis_client(msa: FastMSA):
    msa.allow_external_event = True

    yield RedisClient(msa.redis_conn_info)

    msa.allow_external_event = False


def test_change_batch_quantity_leading_to_reallocation(
    api_client: APIClient,
    redis_client: RedisClient,
    msa: FastMSA,
):
    msa.allow_external_event = True
    # start with two batches and an order allocated to one of them
    orderid, sku = random_orderid(), random_sku()
    earlier_batch, later_batch = random_batchref(1), random_batchref(2)
    api_client.post_to_add_batch(
        earlier_batch, sku, qty=10, eta=datetime(2021, 4, 26).isoformat()
    )
    api_client.post_to_add_batch(
        later_batch, sku, qty=10, eta=datetime(2021, 4, 27).isoformat()
    )
    response = api_client.post_to_allocate(orderid, sku, 10)
    assert response.json()["batchref"] == earlier_batch

    # change quantity on allocated batch so it's less than our order
    redis_client.publish_message(
        "change_batch_quantity", {"batchref": earlier_batch, "qty": 5}
    )
    redis = redis_client.redis
    pubsub = redis.pubsub(ignore_subscribe_messages=True)
    pubsub.subscribe("line_allocated")

    # wait until we see a message saying the order has been reallocated
    messages = []
    for attempt in Retrying(stop=stop_after_delay(3), reraise=True):
        with attempt:
            message = pubsub.get_message(timeout=3)
            if message:
                messages.append(message)
                print(messages)
            assert messages
            data = json.loads(messages[-1]["data"])
            assert data["orderid"] == orderid
            assert data["batchref"] == later_batch
