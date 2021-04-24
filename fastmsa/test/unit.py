"""Test 헬퍼를 제공하는 모듈.

- FakeRepository 나 FakeUoW 를 기본 제공합니다.

"""


"""서비스 레이어 단위 테스트.

Low Gear(고속 기어) 테스트입니다.
"""
from typing import Optional, Type, TypeVar

from fastmsa.core import AbstractConfig
from fastmsa.domain import Aggregate, Entity
from fastmsa.orm import AbstractSession
from fastmsa.repo import AbstractRepository
from fastmsa.uow import AbstractUnitOfWork

E = TypeVar("E", bound=Entity)
A = TypeVar("A", bound=Aggregate[Entity])


class FakeConfig(AbstractConfig):
    def get_db_url(self):
        return "sqlite://"

    def init_mappers(self):
        pass

    def validate(self):
        pass


class FakeRepository(AbstractRepository[E]):
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
    committed = False

    def commit(self) -> None:
        self.committed = True


class FakeUnitOfWork(AbstractUnitOfWork[Aggregate[E]]):
    # 생성자 오버로딩이 필요해서 인자값 저장하는 파라미터 추가
    def __init__(
        self,
        agg_class: Type[Aggregate[E]],
        id_field: str,
        items: Optional[list[Aggregate[E]]] = None,
    ) -> None:
        self.repo = FakeRepository(id_field, items)
        self.committed = False

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        pass
