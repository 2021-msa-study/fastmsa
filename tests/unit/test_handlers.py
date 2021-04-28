from datetime import date
from typing import cast

import pytest

from fastmsa.event import EventHandlerMap, messagebus
from fastmsa.test.unit import FakeMessageBus, FakeRepository, FakeUnitOfWork
from tests.app.domain.aggregates import Product
from tests.app.domain.events import (AllocationRequired, BatchCreated,
                                     BatchQuantityChanged, OutOfStock)
from tests.app.handlers import batch

FakeProductUnitOfWork = FakeUnitOfWork[Product]


class FakeProductRepository(FakeRepository[Product]):
    def _get_by_batchref(self, batchref):
        return next(
            (p for p in self._items for b in p.items if b.reference == batchref), None
        )


@pytest.fixture
def repo():
    return FakeProductRepository("sku")


@pytest.fixture
def uow(handlers: EventHandlerMap, repo: FakeProductRepository):
    return FakeUnitOfWork(Product, repo=repo)


class TestAddBatch:
    def test_for_new_product(self, uow: FakeProductUnitOfWork):
        messagebus.handle(BatchCreated("b1", "CRUNCHY-ARMCHAIR", 100, None), uow)
        assert uow.repo.get("CRUNCHY-ARMCHAIR") is not None
        assert uow.committed

    def test_for_existing_product(self, uow: FakeProductUnitOfWork):
        messagebus.handle(BatchCreated("b1", "GARISH-RUG", 100, None), uow)
        messagebus.handle(BatchCreated("b2", "GARISH-RUG", 99, None), uow)
        assert "b2" in [b.reference for b in uow.repo.get("GARISH-RUG").items]


class TestAllocate:
    def test_returns_allocation(self, uow: FakeProductUnitOfWork):
        messagebus.handle(BatchCreated("batch1", "COMPLICATED-LAMP", 100, None), uow)
        result = messagebus.handle(
            AllocationRequired("o1", "COMPLICATED-LAMP", 10), uow
        )
        assert ["batch1"] == result

    def test_errors_for_invalid_sku(self, uow: FakeProductUnitOfWork):
        messagebus.handle(BatchCreated("b1", "AREALSKU", 100, None), uow)

        with pytest.raises(batch.InvalidSku, match="Invalid sku NONEXISTENTSKU"):
            messagebus.handle(AllocationRequired("o1", "NONEXISTENTSKU", 10), uow)

    def test_commits(self, uow: FakeProductUnitOfWork):
        messagebus.handle(BatchCreated("b1", "OMINOUS-MIRROR", 100, None), uow)
        messagebus.handle(AllocationRequired("o1", "OMINOUS-MIRROR", 10), uow)
        assert uow.committed

    def test_sends_email_on_out_of_stock_error(
        self, uow: FakeProductUnitOfWork, handlers: EventHandlerMap
    ):
        messagebus = FakeMessageBus(handlers, fake_events={OutOfStock})
        messagebus.handle(BatchCreated("b1", "POPULAR-CURTAINS", 9, None), uow)
        messagebus.handle(AllocationRequired("o1", "POPULAR-CURTAINS", 10), uow)
        [event] = messagebus.events_published
        assert OutOfStock == type(event)
        assert "POPULAR-CURTAINS" == cast(OutOfStock, event).sku


class TestChangeBatchQuantity:
    def test_changes_available_quantity(self, uow: FakeProductUnitOfWork):
        messagebus.handle(BatchCreated("batch1", "ADORABLE-SETTEE", 100, None), uow)
        [batch] = uow.repo.get("ADORABLE-SETTEE").items
        assert batch.available_quantity == 100

        messagebus.handle(BatchQuantityChanged("batch1", 50), uow)

        assert batch.available_quantity == 50

    def test_reallocates_if_necessary(self, uow: FakeProductUnitOfWork):
        event_history = [
            BatchCreated("batch1", "INDIFFERENT-TABLE", 50, None),
            BatchCreated("batch2", "INDIFFERENT-TABLE", 50, date.today()),
            AllocationRequired("order1", "INDIFFERENT-TABLE", 20),
            AllocationRequired("order2", "INDIFFERENT-TABLE", 20),
        ]

        for e in event_history:
            messagebus.handle(e, uow)

        [batch1, batch2] = uow.repo.get("INDIFFERENT-TABLE").items
        assert batch1.available_quantity == 10
        assert batch2.available_quantity == 50

        messagebus.handle(BatchQuantityChanged("batch1", 25), uow)

        # order1 or order2 will be deallocated, so we'll have 25 - 20
        assert batch1.available_quantity == 5
        # and 20 will be reallocated to the next batch
        assert batch2.available_quantity == 30
