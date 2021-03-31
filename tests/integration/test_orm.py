from datetime import date

from tests.app.domain import models
from sqlalchemy.orm import Session


def test_orderline_mapper_can_load_lines(session: Session) -> None:
    session.execute(
        "INSERT INTO order_line (orderid, sku, qty) VALUES "
        "('order1', 'RED-CHAIR', 12),"
        "('order1', 'RED-TABLE', 13),"
        "('order2', 'BLUE-LIPSTICK', 14)"
    )
    expected = [
        models.OrderLine("order1", "RED-CHAIR", 12),
        models.OrderLine("order1", "RED-TABLE", 13),
        models.OrderLine("order2", "BLUE-LIPSTICK", 14),
    ]
    assert session.query(models.OrderLine).all() == expected


def test_orderline_mapper_can_save_lines(session: Session) -> None:
    new_line = models.OrderLine("order1", "DECORATIVE-WIDGET", 12)
    session.add(new_line)
    session.commit()

    rows = list(session.execute("SELECT orderid, sku, qty FROM order_line"))
    assert rows == [("order1", "DECORATIVE-WIDGET", 12)]


def test_retrieving_batches(session: Session) -> None:
    session.execute(
        "INSERT INTO batch (reference, sku, _purchased_quantity, eta)"
        " VALUES ('batch1', 'sku1', 100, null)"
    )
    session.execute(
        "INSERT INTO batch (reference, sku, _purchased_quantity, eta)"
        " VALUES ('batch2', 'sku2', 200, '2021-04-11')"
    )
    expected = [
        models.Batch("batch1", "sku1", 100, eta=None),
        models.Batch("batch2", "sku2", 200, eta=date(2011, 4, 11)),
    ]

    assert session.query(models.Batch).all() == expected


def test_saving_batches(session: Session) -> None:
    batch = models.Batch("batch1", "sku1", 100, eta=None)
    session.add(batch)
    session.commit()
    rows = list(
        session.execute("SELECT reference, sku, _purchased_quantity, eta FROM batch")
    )
    assert rows == [("batch1", "sku1", 100, None)]


def test_saving_allocations(session: Session) -> None:
    batch = models.Batch("batch1", "sku1", 100, eta=None)
    line = models.OrderLine("order1", "sku1", 10)
    batch.allocate(line)
    session.add(batch)
    session.commit()
    rows = list(session.execute("SELECT orderline_id, batch_id FROM allocation"))
    assert rows == [(batch.id, getattr(line, "id"))]


def test_retrieving_allocations(session: Session) -> None:
    session.execute(
        "INSERT INTO order_line (orderid, sku, qty) VALUES ('order1', 'sku1', 12)"
    )
    [[olid]] = session.execute(
        "SELECT id FROM order_line WHERE orderid=:orderid AND sku=:sku",
        dict(orderid="order1", sku="sku1"),
    )
    session.execute(
        "INSERT INTO batch (reference, sku, _purchased_quantity, eta)"
        " VALUES ('batch1', 'sku1', 100, null)"
    )
    [[bid]] = session.execute(
        "SELECT id FROM batch WHERE reference=:ref AND sku=:sku",
        dict(ref="batch1", sku="sku1"),
    )
    session.execute(
        "INSERT INTO allocation (orderline_id, batch_id) VALUES (:olid, :bid)",
        dict(olid=olid, bid=bid),
    )

    batch = session.query(models.Batch).one()

    assert batch._allocations == {models.OrderLine("order1", "sku1", 12)}
