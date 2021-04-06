"""Flask 엔드포인트 라우팅 모듈입니다."""
from __future__ import annotations
from datetime import datetime
from typing import cast

from flask import request, jsonify

from tests.app.apps.flask import route, FlaskResponse
from tests.app.services.uow import SqlAlchemyUnitOfWork
from tests.app.domain.models import Batch, OrderLine, allocate
from tests.app import services


from tests.app.domain import aggregates

# XXX: pyright 에서 제대로 typing 을 찾지 못해 Casting 필요
Product = cast(aggregates.Aggregate[Batch], aggregates.Product)


@route("/batches", methods=["POST"])
def add_batch() -> FlaskResponse:
    """``POST /batches`` 요청을 처리하여 새로운 배치를 저장소에 추가합니다."""
    with SqlAlchemyUnitOfWork(Product) as uow:
        eta = request.json["eta"]
        if eta:
            eta = datetime.fromisoformat(eta).date()
        services.batch.add(
            request.json["ref"], request.json["sku"], request.json["qty"], eta, uow
        )
        return "OK", 201


@route("/batches", methods=["DELETE"])
def delete_batches() -> FlaskResponse:
    """``DELETE /allocate`` 엔트포인트 요청을 처리합니다.

    주어진 레퍼런스 문자열 리스트를 이용해 배치들을 삭제합니다.
    """
    refs: list[str] = request.json["refs"]

    with SqlAlchemyUnitOfWork(Product) as uow:
        batches = [it for it in uow.repo.list() if it.reference in refs]
        for batch in batches:
            uow.repo.delete(batch)
        print("batches delete:", batches)
        uow.commit()

        return jsonify({"deleted": len(batches)}), 201


@route("/batches/allocate", methods=["POST"])
def post_allocate_batch() -> FlaskResponse:
    """``POST /allocate`` 엔트포인트 요청을 처리합니다."""
    with SqlAlchemyUnitOfWork(Product) as uow:
        batches = uow.repo.list()
        line = OrderLine(
            request.json["orderid"],
            request.json["sku"],
            request.json["qty"],
        )
        batchref = allocate(line, batches)
        uow.commit()

    return jsonify({"batchref": batchref}), 201
