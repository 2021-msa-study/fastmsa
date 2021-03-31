"""서비스 레이어 단위 테스트.

Low Gear(고속 기어) 테스트입니다.
"""
from typing import Sequence, Optional, Generic, TypeVar, cast

import pytest

from tests.app.adapters.repository import AbstractRepository
from tests.app.adapters.orm import AbstractSession

from tests.app.domain.models import Batch, OrderLine
from tests.app.domain.aggregates import Product
from tests.app.services.uow import AbstractUnitOfWork
from tests.app import services

T = TypeVar("T")


class FakeRepository(AbstractRepository[T]):
    def __init__(self, items: Sequence[T]):
        self._items = set(items)

    def add(self, item: T) -> None:
        self._items.add(item)

    def delete(self, batch: T) -> None:
        self._items.remove(batch)

    def list(self) -> list[T]:
        return list(self._items)

    def close(self) -> None:
        pass

    def clear(self) -> None:
        self._bacthes = set[T]()


class FakeSession(AbstractSession):
    committed = False

    def commit(self) -> None:
        self.committed = True


class FakeProductRepository(FakeRepository[Product]):
    def __init__(self, products: list[Product]):
        super().__init__(products)

    def add(self, item: Product) -> None:
        self._items.add(item)

    def get(self, reference: str = "", **_: str) -> Optional[Product]:
        return next((p for p in self._items if p.sku == reference), None)


class FakeUnitOfWork(AbstractUnitOfWork[Product]):
    def __init__(self) -> None:
        self.repos = FakeProductRepository([])
        self.committed = False

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        pass


def test_add_batch() -> None:
    uow = FakeUnitOfWork()
    services.batch.add("b1", "CRUNCHY-ARMCHAIR", 100, None, uow)
    assert uow.repos.get("CRUNCHY-ARMCHAIR") is not None
    assert uow.committed


def test_allocate_returns_allocation() -> None:
    uow = FakeUnitOfWork()
    services.batch.add("batch1", "COMPLICATED-LAMP", 100, None, uow)
    result = services.batch.allocate("o1", "COMPLICATED-LAMP", 10, uow)
    assert "batch1", result


def test_returns_allocation() -> None:
    batch = Batch("b1", "COMPLICATED-LAMP", 100, eta=None)
    uow = FakeUnitOfWork([batch])
    result = services.batch.allocate("o1", "COMPLICATED-LAMP", 10, uow)
    assert result == "b1"


def test_error_for_invalid_sku() -> None:
    batch = Batch("b1", "AREALSKU", 100, eta=None)
    uow = FakeUnitOfWork([batch])
    with pytest.raises(services.batch.InvalidSku, match="Invalid sku NONEXISTENTSKU"):
        services.batch.allocate("o1", "NONEXISTENTSKU", 10, uow)


def test_commits() -> None:
    batch = Batch("b1", "OMINOUS-MIRROR", 100, eta=None)
    uow = FakeUnitOfWork([batch])
    services.batch.allocate("o1", "OMINOUS-MIRROR", 10, uow)
    assert uow.committed is True


def test_allocate_returns_allocation() -> None:
    uow = FakeUnitOfWork()
    services.batch.add("batch1", "COMPLICATED-LAMP", 100, None, uow)
    result = services.batch.allocate("o1", "COMPLICATED-LAMP", 10, uow)
    assert "batch1" == result


def test_allocate_errors_for_invalid_sku() -> None:
    uow = FakeUnitOfWork()
    services.batch.add("b1", "AREALSKU", 100, None, uow)
    with pytest.raises(services.batch.InvalidSku, match="Invalid sku NONEXISTENTSKU"):
        services.batch.allocate("o1", "NONEXISTENTSKU", 10, uow)
