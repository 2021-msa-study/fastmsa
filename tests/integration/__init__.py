from typing import cast

from sqlalchemy.orm import Session

from tests import random_batchref, random_sku


def insert_order_line(session: Session) -> int:
    session.execute(
        "INSERT INTO order_line (orderid, sku, qty)"
        " VALUES ('order1', 'GENERIC-SOFA', 12)"
    )
    [[orderline_id]] = session.execute(
        "SELECT id FROM order_line WHERE orderid=:orderid AND sku=:sku",
        dict(orderid="order1", sku="GENERIC-SOFA"),
    )

    return cast(int, orderline_id)


def insert_batch(session: Session, ref: str = "", sku: str = "") -> int:
    if not ref:
        ref = random_batchref()

    if not sku:
        sku = random_sku()

    session.execute(
        "INSERT INTO batch (reference, sku, _purchased_quantity, eta)"
        " VALUES (:ref, :sku, 100, null)",
        dict(ref=ref, sku=sku),
    )
    [[batch_id]] = session.execute(
        "SELECT id FROM batch WHERE reference=:ref AND sku=:sku", dict(ref=ref, sku=sku)
    )

    return cast(int, batch_id)


def insert_allocation(session: Session, orderline_id: int, batch_id: int) -> None:
    session.execute(
        "INSERT INTO allocation (orderline_id, batch_id)"
        " VALUES (:orderline_id, :batch_id)",
        dict(orderline_id=orderline_id, batch_id=batch_id),
    )
