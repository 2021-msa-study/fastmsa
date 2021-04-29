from datetime import datetime

import pytest

from fastmsa.event import MessageHandlerMap, messagebus
from fastmsa.test.unit import FakeMessageBus, FakeRepository, FakeUnitOfWork
from tests.app.domain import commands, events
from tests.app.domain.aggregates import Product
from tests.app.handlers import batch


class FakeProductRepository(FakeRepository[Product]):
    def _get_by_batchref(self, batchref):
        return next(
            (p for p in self._items for b in p.items if b.reference == batchref), None
        )


@pytest.fixture
def repo():
    return FakeProductRepository("sku")


@pytest.fixture
def uow(handlers: MessageHandlerMap, repo: FakeProductRepository):
    return FakeUnitOfWork(repos={Product: repo})


class TestAddBatch:
    def test_for_new_product(self, uow: FakeUnitOfWork):
        messagebus.handle(
            commands.CreateBatch("b1", "CRUNCHY-ARMCHAIR", 100, None), uow
        )
        assert uow[Product].get("CRUNCHY-ARMCHAIR") is not None
        assert uow.committed

    def test_for_existing_product(self, uow: FakeUnitOfWork):
        messagebus.handle(commands.CreateBatch("b1", "GARISH-RUG", 100, None), uow)
        messagebus.handle(commands.CreateBatch("b2", "GARISH-RUG", 99, None), uow)
        assert "b2" in [b.reference for b in uow[Product].get("GARISH-RUG").items]


class TestAllocate:
    def test_returns_allocation(self, uow: FakeUnitOfWork):
        messagebus.handle(
            commands.CreateBatch("batch1", "COMPLICATED-LAMP", 100, None), uow
        )
        result = messagebus.handle(commands.Allocate("o1", "COMPLICATED-LAMP", 10), uow)
        assert ["batch1"] == result

    def test_errors_for_invalid_sku(self, uow: FakeUnitOfWork):
        messagebus.handle(commands.CreateBatch("b1", "AREALSKU", 100, None), uow)

        with pytest.raises(batch.InvalidSku, match="Invalid sku NONEXISTENTSKU"):
            messagebus.handle(commands.Allocate("o1", "NONEXISTENTSKU", 10), uow)

    def test_commits(self, uow: FakeUnitOfWork):
        messagebus.handle(commands.CreateBatch("b1", "OMINOUS-MIRROR", 100, None), uow)
        messagebus.handle(commands.Allocate("o1", "OMINOUS-MIRROR", 10), uow)
        assert uow.committed

    def test_sends_email_on_out_of_stock_error(
        self, uow: FakeUnitOfWork, handlers: MessageHandlerMap
    ):
        messagebus = FakeMessageBus(handlers, fake_messages={events.OutOfStock})
        messagebus.handle(commands.CreateBatch("b1", "POPULAR-CURTAINS", 9, None), uow)
        messagebus.handle(commands.Allocate("o1", "POPULAR-CURTAINS", 10), uow)
        # [event] = messagebus.message_published
        # assert events.OutOfStock == type(event)
        # assert "POPULAR-CURTAINS" == cast(events.OutOfStock, event).sku


class TestChangeBatchQuantity:
    def test_changes_available_quantity(self, uow: FakeUnitOfWork):
        messagebus.handle(
            commands.CreateBatch("batch1", "ADORABLE-SETTEE", 100, None), uow
        )
        [batch] = uow[Product].get("ADORABLE-SETTEE").items
        assert batch.available_quantity == 100

        messagebus.handle(commands.ChangeBatchQuantity("batch1", 50), uow)

        assert batch.available_quantity == 50

    def test_reallocates_if_necessary(self, uow: FakeUnitOfWork):
        message_history = [
            commands.CreateBatch("batch1", "INDIFFERENT-TABLE", 50, None),
            commands.CreateBatch("batch2", "INDIFFERENT-TABLE", 50, datetime.today()),
            commands.Allocate("order1", "INDIFFERENT-TABLE", 20),
            commands.Allocate("order2", "INDIFFERENT-TABLE", 20),
        ]

        for e in message_history:
            messagebus.handle(e, uow)

        [batch1, batch2] = uow[Product].get("INDIFFERENT-TABLE").items
        assert batch1.available_quantity == 10
        assert batch2.available_quantity == 50

        messagebus.handle(commands.ChangeBatchQuantity("batch1", 25), uow)

        # order1 or order2 will be deallocated and, so we'll have 25 - 20
        assert batch1.available_quantity == 5
        # and 20 will be reallocated to the next batch
        assert batch2.available_quantity == 30
