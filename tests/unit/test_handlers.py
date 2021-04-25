from fastmsa.event import handle_event
from fastmsa.test.unit import FakeUnitOfWork
from tests.app.domain.aggregates import Product
from tests.app.domain.events import AllocationRequired, BatchCreated


class TestAddBatch:
    def test_for_new_product(self):
        uow = FakeUnitOfWork(Product, "sku")
        handle_event(BatchCreated("b1", "CRUNCHY-ARMCHAIR", 100, None), uow)
        assert uow.repo.get("CRUNCHY-ARMCHAIR") is not None
        assert uow.committed


class TestAllocate:
    def test_returns_allocation(self):
        uow = FakeUnitOfWork(Product, "sku")
        handle_event(BatchCreated("batch1", "COMPLICATED-LAMP", 100, None), uow)
        result = handle_event(AllocationRequired("o1", "COMPLICATED-LAMP", 10), uow)
        assert ["batch1"] == result
