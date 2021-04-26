"""도메인 모델."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class Order:
    """고객이 발주하는 주문(Order) 모델입니다.."""

    id: str  # pylint: disable=invalid-name


@dataclass(unsafe_hash=True)
class OrderLine:
    """주문(:class:`Order`)에 대한 여러 주문선을 나타냅니다.

    :meth:`Batch.allocate` 를 이용해 재고 :class:`Batch` 소스와 연결합니다.
    """

    orderid: str
    """:attr:`Order.id` 를 가리키는 레퍼런스 id입니다."""

    sku: str
    """|SKU|."""

    qty: int


class Batch:
    """재고 단위(SKU)별로 예정 시간(`eta`)까지 지정 수량(`qta`)으로 한번에 구매될 상품입니다."""

    def __init__(
        self,
        ref: str,
        sku: str,
        qty: int,
        eta: Optional[date] = None,
        id: Optional[int] = None,
    ):  # pylint: disable=redefined-builtin
        """기본 생성자.

        Args:
            id: 매핑된 DB가 할당한 고유 ID. 세션 commit이 될 경우에만 값이 부여됩니다.
        """
        self.id = id  # pylint: disable=invalid-name
        """매핑된 DB가 할당한 고유 ID. 세션 commit이 될 경우에만 값이 부여됩니다."""

        self.reference = ref

        self.sku = sku
        """|SKU|."""

        self.eta = eta
        """|ETA|."""

        self._purchased_quantity = qty
        self._allocations = set[OrderLine]()

    def change_purchased_quantity(self, new_qty: int) -> None:
        """구매 수량을 변경합니다."""
        self._purchased_quantity = new_qty

    def allocate(self, line: OrderLine) -> None:
        """지정된 :class:`OrderLine` 을 현재 :class:`Batch` 에 추가합니다.

        Args:
            line: 배치에 추가할 OrderLine.
        """
        if self.can_allocate(line):
            self._allocations.add(line)

    def deallocate(self, line: OrderLine) -> None:
        """주문선 `line` 을 할당 취소 합니다."""
        if line in self._allocations:
            self._allocations.remove(line)

    def deallocate_one(self) -> Optional[OrderLine]:
        """주문선 `line` 을 할당 취소 합니다."""
        if not self._allocations:
            return None

        line = next(iter(self._allocations))
        self._allocations.remove(line)
        return line

    @property
    def allocated_quantity(self) -> int:
        """할당된 주문선 수량."""
        return sum(line.qty for line in self._allocations)

    @property
    def available_quantity(self) -> int:
        """사용 가능한 재고 수량."""
        return self._purchased_quantity - self.allocated_quantity

    def can_allocate(self, line: OrderLine) -> bool:
        """할당 가능 여부를 리턴합니다.

        주문선의 SKU가 배치의 SKU와 동일하고 할당 가능한 수량이 주문선의 요구 수량보다
        큰 경우에만 할당 가능합니다.
        """
        return self.sku == line.sku and self.available_quantity >= line.qty

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Batch):
            return False
        return other.reference == self.reference

    def __hash__(self) -> int:
        return hash(self.reference)

    def __lt__(self, other: Batch) -> bool:
        if self.eta is None:
            return True
        if other.eta is None:
            return False
        return self.eta < other.eta


def allocate(line: OrderLine, batches: list[Batch]) -> str:
    """주어진 배치들 중 할당 가능하고  가장 ETA가 빠른 배치를 주문선 `line`에 할당합니다.

    Raises:
        :class:`OutOfStock` 할당 가능한 배치가 없을 때 발생하는 예외.
    """
    try:
        batch = next(b for b in sorted(batches) if b.can_allocate(line))
        batch.allocate(line)
        return batch.reference
    except StopIteration as ex:
        raise OutOfStock(f"Out of stock for sku {line.sku}") from ex
