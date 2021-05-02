"""FastAPI 로 구현한 RESTful 서비스 앱."""
from typing import Any, Callable

import httpx
from fastapi import FastAPI

from fastmsa.core import AbstractFastMSA

# globals
app: FastAPI = FastAPI(title=__name__)  # pylint:


def init_app(
    msa: AbstractFastMSA, init_hook: Callable[[AbstractFastMSA, FastAPI], Any] = None
) -> FastAPI:
    """FastAPI 앱을 초기화 합니다.

    :mod:`app.routes` 모듈 및에 정의된 엔드포인트 라우팅 설정을 로드하고
    :meth:`fastmsa.orm.init_db` 를 호출하여 DB를 초기화 합니다.
    """
    from fastmsa.orm import init_db  # noqa

    if init_hook:
        init_hook(msa, app)

    init_db()

    return app


class AsyncAPIClient:
    def __init__(self, session: httpx.AsyncClient):
        self.session = session

    async def post_to_add_batch(self, ref: str, sku: str, qty: int, eta: str):
        r = await self.session.post(
            "/batches", json={"ref": ref, "sku": sku, "qty": qty, "eta": eta}
        )
        assert r.status_code == 201

    async def post_to_allocate(self, orderid, sku, qty, expect_success=True):
        r = await self.session.post(
            "/batches/allocate",
            json={
                "orderid": orderid,
                "sku": sku,
                "qty": qty,
            },
        )
        if expect_success:
            assert r.status_code == 201
        return r
