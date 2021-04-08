"""서비스 레이어 단위 테스트.

Low Gear(고속 기어) 테스트입니다.
"""
import pytest

from fastmsa.uow import AbstractUnitOfWork
from fastmsa.test.unit import FakeUnitOfWork

from tests.app import services


from tests.app.domain.aggregates import Product
from tests.app.domain.models import Batch


def test_add_batch() -> None:
    uow = FakeUnitOfWork(Product, "sku")
    services.batch.add("b1", "CRUNCHY-ARMCHAIR", 100, None, uow)
    assert uow.repo.get("CRUNCHY-ARMCHAIR") is not None
    assert uow.committed


def test_returns_allocation() -> None:
    batch = Batch("b1", "COMPLICATED-LAMP", 100, eta=None)
    product = Product(batch.sku, [batch])
    uow = FakeUnitOfWork(Product, "sku", [product])
    result = services.batch.allocate("o1", "COMPLICATED-LAMP", 10, uow)
    assert result == "b1"


def test_error_for_invalid_sku() -> None:
    batch = Batch("b1", "AREALSKU", 100, eta=None)
    product = Product(batch.sku, [batch])
    uow = FakeUnitOfWork(Product, "sku", [product])
    with pytest.raises(services.batch.InvalidSku, match="Invalid sku NONEXISTENTSKU"):
        services.batch.allocate("o1", "NONEXISTENTSKU", 10, uow)


def test_commits() -> None:
    batch = Batch("b1", "OMINOUS-MIRROR", 100, eta=None)
    product = Product(batch.sku, [batch])
    uow = FakeUnitOfWork(Product, "sku", [product])
    services.batch.allocate("o1", "OMINOUS-MIRROR", 10, uow)
    assert uow.committed is True


def test_allocate_returns_allocation() -> None:
    uow = FakeUnitOfWork(Product, "sku")
    services.batch.add("batch1", "COMPLICATED-LAMP", 100, None, uow)
    result = services.batch.allocate("o1", "COMPLICATED-LAMP", 10, uow)
    assert "batch1" == result


def test_allocate_errors_for_invalid_sku() -> None:
    uow = FakeUnitOfWork(Product, "sku")
    services.batch.add("b1", "AREALSKU", 100, None, uow)
    with pytest.raises(services.batch.InvalidSku, match="Invalid sku NONEXISTENTSKU"):
        services.batch.allocate("o1", "NONEXISTENTSKU", 10, uow)
