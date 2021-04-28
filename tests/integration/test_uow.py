from __future__ import annotations

from datetime import date
from typing import Any, Optional

import pytest

from fastmsa.orm import Session, SessionMaker
from fastmsa.uow import SqlAlchemyUnitOfWork
from tests import random_batchref, random_sku
from tests.app.domain.aggregates import Product
from tests.app.domain.models import OrderLine
from tests.integration import insert_product


def insert_batch(
    session: Session, ref: str, sku: str, qty: int, eta: Optional[date]
) -> None:
    session.execute(
        "INSERT INTO batch (reference, sku, _purchased_quantity, eta)"
        " VALUES (:ref, :sku, :qty, :eta)",
        dict(ref=ref, sku=sku, qty=qty, eta=eta),
    )


def delete_product_batch_and_allocation(session: Session, sku: str, ref: str) -> None:
    session.execute(
        """
        DELETE FROM allocation WHERE batch_id in (
        SELECT id FROM batch WHERE reference = :ref
    )""",
        {"ref": ref},
    )
    session.execute("DELETE FROM batch WHERE reference = :ref", {"ref": ref})
    session.execute("DELETE FROM product WHERE sku = :sku", {"sku": sku})
    session.commit()


@pytest.fixture
def session_with_product(get_session):
    _batch_ref = ""
    _sku = ""
    session = get_session()

    def wrapper(ref: str, sku: str, qty: int, eta: Optional[date]):
        nonlocal _batch_ref
        nonlocal _sku
        _batch_ref = ref
        _sku = sku
        delete_product_batch_and_allocation(session, _sku, _batch_ref)
        insert_product(session, sku)
        insert_batch(session, ref, sku, qty, eta)
        session.commit()
        return session

    yield wrapper

    delete_product_batch_and_allocation(session, _sku, _batch_ref)


@pytest.fixture
def cleanup_uow(get_session):
    """에러가 발생해도 주어진 bacth reference 초기화를 보장합니다."""
    _batch_ref = ""
    _sku = ""
    session = get_session()

    def wrapper(sku: str, ref: str):
        nonlocal _batch_ref
        nonlocal _sku
        _batch_ref = ref
        _sku = sku
        delete_product_batch_and_allocation(session, sku, _batch_ref)
        return SqlAlchemyUnitOfWork([Product], lambda: session)

    yield wrapper

    delete_product_batch_and_allocation(session, _sku, _batch_ref)


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
    session_with_product: Any,
):
    ref, sku = random_batchref(), random_sku()
    session = session_with_product(ref, sku, 100, None)
    uow = SqlAlchemyUnitOfWork([Product], get_session)

    with uow:
        product = uow[Product].get(sku)
        if product:
            line = OrderLine("o1", sku, 10)
            product.allocate(line)
            uow.commit()

    ref_got = get_allocated_batch_ref(session, "o1", sku)
    assert ref == ref_got


def test_rolls_back_uncommitted_work_by_default(get_session, cleanup_uow):
    ref, sku = random_batchref(), random_sku()
    uow = cleanup_uow(sku, ref)
    with uow:
        insert_product(uow.session, sku)
        insert_batch(uow.session, ref, sku, 100, None)

    # Commit 을 안한 경우 실제 DB에 데이터가 반영되지 않습니다.
    new_session = get_session()
    rows = list(new_session.execute("SELECT * FROM batch WHERE sku=:sku", {"sku": sku}))
    assert [] == rows, f"{rows}"


def test_rolls_back_committed(get_session, cleanup_uow):
    ref, sku = random_batchref(), random_sku()
    uow = cleanup_uow(sku, ref)
    with uow:
        insert_product(uow.session, sku)
        insert_batch(uow.session, ref, sku, 100, None)
        uow.session.commit()

    # commit 을 하면 DB 상태가 변경되어야 합니다.
    new_session = get_session()
    [ref_got] = next(
        new_session.execute("SELECT reference FROM batch WHERE sku=:sku", {"sku": sku})
    )
    assert ref == ref_got, f"{ref} != {ref_got}"


def test_rolls_back_on_error(get_session, cleanup_uow):
    class MyException(Exception):
        pass

    ref, sku = random_batchref(), random_sku()
    uow = cleanup_uow(sku, ref)
    with pytest.raises(MyException):
        with uow:
            insert_product(uow.session, sku)
            insert_batch(uow.session, ref, sku, 100, None)
            raise MyException()
            uow.commit()

    new_session = get_session()
    rows = list(new_session.execute("SELECT * FROM batch WHERE sku=:sku", {"sku": sku}))
    assert rows == []
