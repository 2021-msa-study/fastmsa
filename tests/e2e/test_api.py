"""FastAPI 로 구현된 엔드포인트 테스트입니다."""
from typing import Callable, Optional
from fastmsa.core import FastMSA
import pytest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from tests import random_batchref, random_orderid, random_sku


@pytest.fixture
def client(msa: FastMSA):
    yield TestClient(msa.api)


def post_to_add_batch(
    client: TestClient, ref: str, sku: str, qty: int, eta: Optional[str]
) -> None:
    """서비스 엔드포인트 `POST /batches` 를 통해 배치를 추가합니다."""
    r = client.post("/batches", json={"ref": ref, "sku": sku, "qty": qty, "eta": eta})
    assert r.status_code == 201


def setup_batches(cnt_batches):
    return [random_batchref(i) for i in range(cnt_batches)]


def test_happy_path_returns_201_and_allocated_batch(client):
    sku, othersku = random_sku(), random_sku("other")
    earlybatch, laterbatch = setup_batches(2)
    [otherbatch] = setup_batches(1)
    post_to_add_batch(client, laterbatch, sku, 100, "2021-01-02")
