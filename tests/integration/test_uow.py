from __future__ import annotations
from tests.integration import insert_product
from typing import Optional, Any, cast
from datetime import date

import pytest

from tests.app.services.uow import (
    AbstractUnitOfWork,
    SqlAlchemyUnitOfWork,
)
from tests.app.domain.models import Batch, OrderLine
from tests.app.adapters.orm import (
    SessionMaker,
    start_mappers,
    init_engine,
    sessionmaker,
    Session,
)
from tests.app import config

from tests.app.domain import aggregates

# XXX: pyright 에서 제대로 typing 을 찾지 못해 Casting 필요
Product = cast(aggregates.Aggregate[Batch], aggregates.Product)


def insert_batch(
    session: Session, ref: str, sku: str, qty: int, eta: Optional[date]
) -> None:
    session.execute(
        "INSERT INTO batch (reference, sku, _purchased_quantity, eta)"
        " VALUES (:ref, :sku, :qty, :eta)",
        dict(ref=ref, sku=sku, qty=qty, eta=eta),
    )


def delete_product_batch_and_allocation(session: Session, ref: str) -> None:
    session.execute(
        """
        DELETE FROM allocation WHERE batch_id in (
        SELECT id FROM batch WHERE reference = :ref
    )""",
        {"ref": ref},
    )
    session.execute(
        """
        DELETE FROM product WHERE sku in (
        SELECT sku FROM batch WHERE reference = :ref
    )""",
        {"ref": ref},
    )
    session.execute("DELETE FROM batch WHERE reference = :ref", {"ref": ref})
    session.commit()


@pytest.fixture
def session_with_batch(get_session):
    batch_ref = ""
    session = get_session()

    def wrapper(ref: str, sku: str, qty: int, eta: Optional[date]):
        nonlocal batch_ref
        batch_ref = ref
        delete_product_batch_and_allocation(session, batch_ref)
        insert_batch(session, ref, sku, qty, eta)
        insert_product(session, sku)
        session.commit()
        return session

    yield wrapper

    delete_product_batch_and_allocation(session, batch_ref)


@pytest.fixture
def cleanup_uow(get_session):
    """에러가 발생해도 주어진 bacth reference 초기화를 보장합니다."""
    batch_ref = ""
    session = get_session()

    def wrapper(ref: str):
        nonlocal batch_ref
        batch_ref = ref
        delete_product_batch_and_allocation(session, batch_ref)
        return SqlAlchemyUnitOfWork(Product, lambda: session)

    yield wrapper

    delete_product_batch_and_allocation(session, batch_ref)


def get_allocated_batch_ref(session: Session, orderid: str, sku: str) -> str:
    [[orderlineid]] = session.execute(
        "SELECT id FROM order_line WHERE orderid=:orderid AND sku=:sku",
        dict(orderid=orderid, sku=sku),
    )
    [[batchref]] = session.execute(
        "SELECT b.reference FROM allocation JOIN batch AS b ON batch_id = b.id"
        " WHERE orderline_id=:orderlineid",
        dict(orderlineid=orderlineid),
    )
    return batchref


def test_uow_can_retrieve_a_batch_and_allocate_to_it(
    get_session: SessionMaker,
    session_with_batch: Any,
):
    session = session_with_batch("batch1", "HIPSTER-WORKBENCH", 100, None)
    uow = SqlAlchemyUnitOfWork(Product, get_session)

    with uow:
        product = uow.repo.get(reference="batch1")
        if product:
            batch = product
            line = OrderLine("o1", "HIPSTER-WORKBENCH", 10)
            batch.allocate(line)
            uow.commit()

    batchref = get_allocated_batch_ref(session, "o1", "HIPSTER-WORKBENCH")
    assert batchref == "batch1"


def test_rolls_back_uncommitted_work_by_default(get_session, cleanup_uow):
    uow = cleanup_uow("batch1")
    with uow:
        insert_batch(uow.session, "batch1", "MEDIUM-PLINTH", 100, None)

    # Commit 을 안한 경우 실제 DB에 데이터가 반영되지 않습니다.
    new_session = get_session()
    rows = list(new_session.execute("SELECT * FROM batch"))
    assert [] == rows, f"{rows}"


def test_rolls_back_committed(get_session, cleanup_uow):
    uow = cleanup_uow("batch1")
    with uow:
        insert_batch(uow.session, "batch1", "MEDIUM-PLINTH", 100, None)
        uow.session.commit()

    # commit 을 하면 DB 상태가 변경되어야 합니다.
    new_session = get_session()
    [ref] = next(new_session.execute("SELECT reference FROM batch"))
    assert "batch1" == ref, f"{ref}"


def test_rolls_back_on_error(get_session, cleanup_uow):
    class MyException(Exception):
        pass

    uow = cleanup_uow("batch1")
    with pytest.raises(MyException):
        with uow:
            insert_batch(uow.session, "batch1", "LARGE-FORK", 100, None)
            raise MyException()
            uow.commit()

    new_session = get_session()
    rows = list(new_session.execute('SELECT * FROM "batch"'))
    assert rows == []
