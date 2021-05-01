"""Batch 서비스."""
from datetime import datetime
from typing import Optional, Sequence

from fastmsa.uow import AbstractUnitOfWork
from tests.app.domain.aggregates import Product
from tests.app.domain.models import Batch, OrderLine


class InvalidSku(Exception):
    """배치의 SKU와 다른 SKU를 할당하려 할 때 발생하는 예외입니다."""

    ...


class ReferenceNotFound(Exception):
    """배치 레퍼런스가 존재하지 않을 때 발생하는 예외입니ㅏ.."""

    ...


def is_valid_sku(sku: str, batches: Sequence[Batch]) -> bool:
    """`batches` 에서 `sku` 와 일치하는 품목이 하나라도 있으며 참을 리턴합니다."""
    return sku in {it.sku for it in batches}


def add_batch(
    ref: str, sku: str, qty: int, eta: Optional[datetime], uow: AbstractUnitOfWork
) -> None:
    """UOW를 이용해 배치를 추가합니다."""
    with uow:
        product = uow[Product].get(sku)

        if not product:
            product = Product(sku, items=[])
            uow[Product].add(product)
        product.items.append(Batch(ref, sku, qty, eta))
        uow.commit()


def allocate(
    orderid: str, sku: str, qty: int, uow: AbstractUnitOfWork
) -> Optional[str]:
    """ETA가 가장 빠른 배치를 찾아 :class:`.OrderLine` 을 할당합니다.

    Raises:
        InvalidSku: ``SKU`` 가 잘못 지정되어 할당하는한 배치가 없을 경우 발생하는 예외
    """
    line = OrderLine(orderid, sku, qty)
    with uow:
        product = uow[Product].get(line.sku)
        if product is None:
            raise InvalidSku(f"Invalid sku {line.sku}")
        batchref = product.allocate(line)
        uow.commit()
    return batchref
