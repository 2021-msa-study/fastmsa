"""레포지터리 패턴 구현."""
from __future__ import annotations

from typing import List, Optional, Type, TypeVar

from sqlalchemy.orm import Session

from fastmsa.core import AbstractRepository, Entity
from fastmsa.orm import get_sessionmaker

E = TypeVar("E", bound=Entity)


class SqlAlchemyRepository(AbstractRepository[E]):
    """SqlAlchemy ORM을 저장소로 하는 :class:`AbstractRepository` 구현입니다."""

    def __init__(self, entity_class: Type[E], session: Session = None):
        """임의의 Aggregate T 를 받아 T에대한 Repostiory를 초기화합니다."""
        super().__init__()
        self.entity_class = entity_class
        self.session: Session
        if not session:
            self.session = get_sessionmaker()()
        else:
            self.session = session

    def __repr__(self) -> str:
        return f"SqlAlchemyRepository[{self.entity_class}]"

    def __enter__(self) -> SqlAlchemyRepository[E]:
        """`module`:contextmanager`의 필수 인터페이스 구현."""
        return self

    def close(self) -> None:
        hasattr(self.session, "close") and self.session.close()

    def _add(self, item: E) -> None:
        self.session.add(item)

    def _get(self, id: str = "", **kwargs: str) -> Optional[E]:
        if id:
            return self.session.query(self.entity_class).get(id)

        filter_by = {k: v for k, v in kwargs.items() if v is not None}
        return self.session.query(self.entity_class).filter_by(**filter_by).first()

    def delete(self, item: E) -> None:
        self.session.delete(item)

    def all(self) -> List[E]:
        return self.session.query(self.entity_class).all()

    def clear(self) -> None:
        self.session.query(self.entity_class)
