"""샘플 서비스."""
from datetime import datetime
from typing import Optional

from fastmsa.uow import AbstractUnitOfWork

from ..domain.aggregates import Product
from ..domain.models import Item


def add_item(
    id: int,
    uuid: str,
    product_id: str,
    created: Optional[datetime],
    uow: AbstractUnitOfWork[Product],
) -> None:
    """Item을 추가합니다."""
    with uow:
        product = uow.repo.get(id)

        if not product:
            product = Product(id, items=[])
            uow.repo.add(product)
        product.items.append(Item(id, uuid, product_id, created or datetime.now()))
        uow.commit()
