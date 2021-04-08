"""Test 헬퍼를 제공하는 모듈.

- FakeRepository 나 FakeUoW 를 기본 제공합니다.

"""


"""서비스 레이어 단위 테스트.

Low Gear(고속 기어) 테스트입니다.
"""
from fastmsa.domain import Aggregate
from typing import Sequence, Optional, Type, TypeVar

from fastmsa.uow import AbstractUnitOfWork
from fastmsa.repository import AbstractRepository
from fastmsa.orm import AbstractSession

T = TypeVar("T", bound=Aggregate)


class FakeRepository(AbstractRepository[T]):
    def __init__(
        self, agg_class: Type[T], id_field: str, items: Optional[list[T]] = None
    ):
        self.agg_class = agg_class
        self.id_field = id_field
        self._items = set(items) if items else set()

    def add(self, item: T) -> None:
        self._items.add(item)

    def get(self, id: str = "", **kwargs: str) -> Optional[T]:
        return next((p for p in self._items if getattr(p, self.id_field) == id), None)

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


class FakeUnitOfWork(AbstractUnitOfWork[T]):
    # 생성자 오버로딩이 필요해서 인자값 저장하는 파라미터 추가
    def __init__(
        self, agg_class: Type[T], id_field: str, items: Optional[list[T]] = None
    ) -> None:
        self.repo = FakeRepository(agg_class, id_field, items)
        self.committed = False

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        pass
