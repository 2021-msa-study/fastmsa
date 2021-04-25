"""FastAPI 엔드포인트 라우팅 모듈입니다."""
from __future__ import annotations

from fastmsa.api import post
from fastmsa.event import handle_event
from fastmsa.uow import SqlAlchemyUnitOfWork
from tests.app.domain import events
from tests.app.domain.aggregates import Product
from tests.app.handlers.batch import InvalidSku
from tests.app.schema.batch import BatchAdd, BatchAllocate


@post("/batches", status_code=201)
def add_batch(batch: BatchAdd):
    """``POST /batches`` 요청을 처리하여 새로운 배치를 저장소에 추가합니다."""
    event = events.BatchCreated(batch.ref, batch.sku, batch.qty, batch.eta)
    handle_event(event, SqlAlchemyUnitOfWork(Product))


@post("/batches/allocate", status_code=201)
def post_allocate_batch(req: BatchAllocate):
    """``POST /allocate`` 엔트포인트 요청을 처리합니다."""
    try:
        event = events.AllocationRequired(req.orderid, req.sku, req.qty)
        results = handle_event(event, SqlAlchemyUnitOfWork(Product))
        return {"batchref": results.pop(0)}
    except InvalidSku as e:
        return {"batchref": None, "error": "InvalidSku"}
