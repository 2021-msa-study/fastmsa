# pylint: disable=protected-access
from sqlalchemy.orm import Session

from tests.app.domain.models import Batch, OrderLine
from tests.app.adapters.repository import SqlAlchemyRepository

from tests.integration import insert_allocation, insert_batch, insert_order_line


def test_repository_can_save_a_batch(session: Session) -> None:
    batch = Batch("batch1", "RUSTY-SOAPDISH", 100, eta=None)

    repo = SqlAlchemyRepository(session)
    repo.add(batch)
    session.commit()

    rows = list(
        session.execute(
            'SELECT reference, sku, _purchased_quantity, eta FROM batch'))
    assert rows == [("batch1", "RUSTY-SOAPDISH", 100, None)]


def test_repository_can_retrieve_a_batch_with_allocations(
        session: Session) -> None:
    orderline_id = insert_order_line(session)
    batch1_id = insert_batch(session, "batch1", "GENERIC-SOFA")
    insert_batch(session, "batch2")
    insert_allocation(session, orderline_id, batch1_id)

    repo = SqlAlchemyRepository(session)
    retrieved = repo.get("batch1")

    expected = Batch("batch1", "GENERIC-SOFA", 100, eta=None)
    assert retrieved == expected  # Batch.__eq__ only compares reference
    assert retrieved.sku == expected.sku
    assert retrieved._purchased_quantity == expected._purchased_quantity
    assert retrieved._allocations == {
        OrderLine("order1", "GENERIC-SOFA", 12),
    }
