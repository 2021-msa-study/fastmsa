"""API 테스트."""
from __future__ import annotations

from typing import Callable, Optional

import pytest
import requests

from fastmsa import FastMSA
from tests import random_batchref, random_orderid, random_sku

AddStockFunc = Callable[[list[tuple[str, str, int, Optional[str]]]], None]


def post_to_add_batch(
    msa: FastMSA, ref: str, sku: str, qty: int, eta: Optional[str]
) -> None:
    """서비스 엔드포인트 `POST /batches` 를 통해 배치를 추가합니다."""
    url = msa.config.get_api_url()
    r = requests.post(
        f"{url}/batches", json={"ref": ref, "sku": sku, "qty": qty, "eta": eta}
    )
    assert r.status_code == 201


def delete_batches(msa: FastMSA, sku: str, refs: list[str]) -> None:
    """서비스 엔드포인트 `DELETE /batches` 를 통해 배치를 삭제합니다."""
    url = msa.config.get_api_url()
    res = requests.delete(
        f"{url}/batches",
        json={
            "sku": sku,
            "refs": refs,
        },
    )
    assert res.status_code == 201


@pytest.fixture
def setup_batches(msa: FastMSA):
    _batch_refs = []
    _sku = ""

    def wrapper(sku: str, cnt_batches):
        nonlocal _batch_refs
        nonlocal _sku
        _batch_refs = [random_batchref(i) for i in range(cnt_batches)]
        _sku = sku
        return _batch_refs

    yield wrapper

    delete_batches(msa, _sku, _batch_refs)


@pytest.mark.usefixtures("server")
def test_happy_path_returns_201_and_allocated_batch(
    # pylint: disable=redefined-outer-name
    msa: FastMSA,
    setup_batches: Callable[[str, int], list[str]],
) -> None:
    sku, othersku = random_sku(), random_sku("other")
    earlybatch, laterbatch = setup_batches(sku, 2)
    [otherbatch] = setup_batches(othersku, 1)
    post_to_add_batch(msa, laterbatch, sku, 100, "2021-01-02")
    post_to_add_batch(msa, earlybatch, sku, 100, "2021-01-01")
    post_to_add_batch(msa, otherbatch, othersku, 100, None)
    data = {"orderid": random_orderid(), "sku": sku, "qty": 3}
    url = msa.config.get_api_url()
    res = requests.post(f"{url}/batches/allocate", json=data)
    assert res.status_code == 201
    assert res.json()["batchref"] == earlybatch
