"""FastAPI 엔드포인트 라우팅 모듈입니다."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastmsa.api import BaseModel, delete, post
from fastmsa.uow import SqlAlchemyUnitOfWork
from tests.app import services
from tests.app.domain.aggregates import Product
from tests.app.domain.models import Batch, OrderLine


class BatchAdd(BaseModel):
    eta: Optional[datetime]
    ref: str
    sku: str
    qty: int


class BatchDelete(BaseModel):
    eta: Optional[datetime]
    refs: list[str]
    sku: str
    qty: int


class BatchAllocate(BaseModel):
    eta: Optional[datetime]
    orderid: str
    ref: str
    sku: str
    qty: int


@post("/batches", status_code=201)
def add_batch(batch: BatchAdd):
    """``POST /batches`` 요청을 처리하여 새로운 배치를 저장소에 추가합니다."""
    with SqlAlchemyUnitOfWork(Product) as uow:
        eta = batch.eta
        services.batch.add(batch.ref, batch.sku, batch.qty, eta, uow)
        return "OK", 201


@delete("/batches", status_code=201)
def delete_batches(request: BatchDelete):
    """``DELETE /allocate`` 엔트포인트 요청을 처리합니다.

    주어진 레퍼런스 문자열 리스트를 이용해 배치들을 삭제합니다.
    """
    batches = list[Batch]()

    with SqlAlchemyUnitOfWork(Product) as uow:
        product = uow.repo.get(request.sku)
        if product:
            batches = [it for it in product.items if it.reference in request.refs]
            for batch in batches:
                product.items.remove(batch)
            print("batches delete:", batches)
            uow.commit()

        return {"deleted": len(batches)}


@post("/batches/allocate", status_code=201)
def post_allocate_batch(req: BatchAllocate):
    """``POST /allocate`` 엔트포인트 요청을 처리합니다."""
    batchref = None

    with SqlAlchemyUnitOfWork(Product) as uow:
        product = uow.repo.get(req.sku)
        if product:
            line = OrderLine(req.orderid, req.sku, req.qty)
            batchref = product.allocate(line)
            uow.commit()

        return {"batchref": batchref}
