"""레포지터리 패턴 구현."""
from __future__ import annotations

import abc
from contextlib import ContextDecorator
from typing import Any, Generic, List, Literal, Optional, Type, TypeVar

from sqlalchemy.orm import Session

from fastmsa.domain import Entity
from fastmsa.orm import get_sessionmaker

E = TypeVar("E", bound=Entity)


class AbstractRepository(Generic[E], abc.ABC, ContextDecorator):
    """Repository 패턴의 추상 인터페이스 입니다."""

    entity_class: Type[E]

    def __init__(self):
        self.seen = set[E]()

    def __enter__(self) -> AbstractRepository[E]:
        """`module`:contextmanager`의 필수 인터페이스 구현."""
        return self

    def __exit__(
        self, typ: Any = None, value: Any = None, traceback: Any = None
    ) -> Literal[False]:
        self.close()
        return False

    def close(self) -> None:
        """레포지터리와 연결된 저장소 객체를 종료합니다."""
        return

    def add(self, item: E) -> None:
        """레포지터리에 :class:`T` 객체를 추가합니다."""
        self._add(item)
        self.seen.add(item)

    @abc.abstractmethod
    def _add(self, item: E) -> None:
        """레포지터리에 :class:`T` 객체를 추가합니다."""
        raise NotImplementedError

    def get(self, id: Any = "", **kwargs: str) -> Optional[E]:
        """주어진 레퍼런스 문자열에 해당하는 :class:`T` 객체를 조회합니다.

        객체를 찾았을 경우 `seen` 컬렉셔에 추가합니다.
        못 찾을 경우 ``None`` 을 리턴합니다.
        """

        if not kwargs:
            item = self._get(id)
        else:
            # get(by_field=value) 처럼 이름있는 파라메터에 `by_` 가 붙어있는 경우
            # _get_by_field 메소드를 호출하도록 라우팅 합니다.
            k, v = next((k, v) for k, v in kwargs.items())
            if k.startswith("by_"):
                item: Optional[E] = getattr(self, "_get_" + k)(v)
            else:
                item = self._get(id="", **kwargs)

        if item:
            self.seen.add(item)
        return item

    @abc.abstractmethod
    def _get(self, id: str = "", **kwargs: str) -> Optional[E]:
        """주어진 레퍼런스 문자열에 해당하는 :class:`T` 객체를 조회합니다.

        해당하는 배치를 못 찾을 경우 ``None`` 을 리턴합니다.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def all(self) -> List[E]:
        """모든 배치 객체 리스트를 조회합니다."""
        raise NotImplementedError

    @abc.abstractmethod
    def delete(self, item: E) -> None:
        """레포지터리에서 :class:`T` 객체를 삭제합니다."""
        raise NotImplementedError

    @abc.abstractmethod
    def clear(self) -> None:
        """레포지터리 내의 모든 엔티티 데이터를 지웁니다."""
        raise NotImplementedError


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
