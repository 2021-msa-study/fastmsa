from datetime import datetime

from fastmsa.event import MessageBus
from fastmsa.test.unit import FakeMessageBus
from fastmsa.uow import SqlAlchemyUnitOfWork
from tests.app.domain import commands
from tests.app.views import get_allocations_by

today = datetime.today()


def test_allocations_view(sqlite_uow: SqlAlchemyUnitOfWork, messagebus: MessageBus):
    uow = sqlite_uow
    fakebus = FakeMessageBus(messagebus)
    fakebus.handle(commands.CreateBatch("sku1batch", "sku1", 50, None), uow)
    fakebus.handle(commands.CreateBatch("sku2batch", "sku2", 50, today), uow)
    fakebus.handle(commands.Allocate("order1", "sku1", 20), uow)
    fakebus.handle(commands.Allocate("order1", "sku2", 20), uow)
    # add a spurious batch and order to make sure we're getting the right ones
    fakebus.handle(commands.CreateBatch("sku1batch-later", "sku1", 50, today), uow)
    fakebus.handle(commands.Allocate("otherorder", "sku1", 30), uow)
    fakebus.handle(commands.Allocate("otherorder", "sku2", 10), uow)

    assert get_allocations_by("order1", uow) == [
        {"sku": "sku1", "batchref": "sku1batch"},
        {"sku": "sku2", "batchref": "sku2batch"},
    ]


def test_deallocation(sqlite_uow: SqlAlchemyUnitOfWork, messagebus: MessageBus):
    uow = sqlite_uow
    fakebus = FakeMessageBus(messagebus)
    fakebus.handle(commands.CreateBatch("b1", "sku1", 50, None), uow)
    fakebus.handle(commands.CreateBatch("b2", "sku1", 50, today), uow)
    fakebus.handle(commands.Allocate("o1", "sku1", 40), uow)
    fakebus.handle(commands.ChangeBatchQuantity("b1", 10), uow)

    assert get_allocations_by("o1", uow) == [
        {"sku": "sku1", "batchref": "b2"},
    ]
