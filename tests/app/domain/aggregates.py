from __future__ import annotations

from fastmsa.domain import Aggregate
from tests.app.domain.models import Batch, OrderLine, OutOfStock


class Product(Aggregate[Batch]):
    class Meta:
        entity_class = Batch

    def __init__(self, sku: str, items: list[Batch], version_number: int = 0):
        self.id = sku  # Entity 프로토콜을 준수하기 위해 반드시 정의해야 하는 속성.
        self.sku = sku
        self.items = items
        self.version_number = version_number

    def allocate(self, line: OrderLine) -> str:
        try:
            batch = next(b for b in sorted(self.items) if b.can_allocate(line))
            batch.allocate(line)
            self.version_number += 1
            return batch.reference
        except StopIteration:
            raise OutOfStock(f"Out of stock for sku {line.sku}")

    def reallocate(self, line: OrderLine) -> str:
        """기존 Sku의 주문선을 할당 해재 후 새로운 `line`을 할당합니다.

        재할당 서비스 함수의 경우, 작업중 예외가 발생하면 UoW의 동작 방식에 의해 이전 상태로 자동 롤백됩니다.
        모든 유효성 검사와 세부 작업이 다 성공할 경우에만 명시적으로 호출된 commit 함수에 의해 저장소 내용이 변경됩니다.
        """
        try:
            batch = next(b for b in sorted(self.items) if b.can_allocate(line))
            batch.deallocate(line)
            batch.allocate(line)
            return batch.reference
        except StopIteration:
            raise OutOfStock(f"Out of stock for sku {line.sku}")

    def change_quantity(self, batchref: str, new_qty: int) -> None:
        """배치에 할당된 주문선을 수량만큼 해제합니다."""
        # TODO: Fix implementation
        """
        with uow:
            product = uow.items.get(reference=batchref)
            if not product:
                raise ReferenceNotFound()

            batch.change_purchased_quantity(new_qty)
            while batch.available_quantity < 0:
                batch.deallocate_one()
            uow.commit()
        """
