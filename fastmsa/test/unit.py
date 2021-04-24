"""Test 헬퍼를 제공하는 모듈.

- FakeRepository 나 FakeUoW 를 기본 제공합니다.

"""


"""서비스 레이어 단위 테스트.

Low Gear(고속 기어) 테스트입니다.
"""
from typing import Optional, Type, TypeVar

from fastmsa.core import FastMSA
from fastmsa.domain import Aggregate, Entity
from fastmsa.orm import AbstractSession
from fastmsa.repo import AbstractRepository
from fastmsa.uow import AbstractUnitOfWork

E = TypeVar("E", bound=Entity)
A = TypeVar("A", bound=Aggregate)


class FakeConfig(FastMSA):
    """단위 테스트를 위한 Fake 설정."""

    def __init__(self):
        super().__init__(__name__)

    def get_db_url(self):
        return "sqlite://"

    def init_mappers(self):
        pass

    def validate(self):
        pass


class FakeRepository(AbstractRepository[E]):
    """단위 테스트를 위한 Fake 레포지터리."""

    def __init__(self, id_field: str, items: Optional[list[E]] = None):
        self.id_field = id_field
        self._items = set(items) if items else set()

    def add(self, item: E) -> None:
        self._items.add(item)

    def get(self, id: str = "", **kwargs: str) -> Optional[E]:
        item = next((p for p in self._items if getattr(p, self.id_field) == id), None)
        return item

    def delete(self, batch: E) -> None:
        self._items.remove(batch)

    def all(self) -> list[E]:
        return list(self._items)

    def close(self) -> None:
        pass

    def clear(self) -> None:
        self._bacthes = set[E]()


class FakeSession(AbstractSession):
    """단위 테스트를 위한 Fake Session."""

    committed = False

    def commit(self) -> None:
        self.committed = True


class FakeUnitOfWork(AbstractUnitOfWork[A]):
    """단위 테스트를 위한 Fake UoW.

    Params:
        - agg_class: 사용되지는 않지만 타입 추론을 위해 필요 (지우지 말것)
    """

    def __init__(
        self,
        agg_class: Type[A],
        id_field: str,
        items: Optional[list[A]] = None,
    ) -> None:
        self.repo = FakeRepository(id_field, items)
        self.committed = False

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        pass
