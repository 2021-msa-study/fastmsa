"""레포지터리 패턴 구현."""
from __future__ import annotations
from typing import Optional, Union, Literal, Generic, TypeVar, Any, cast
from contextlib import ContextDecorator
import abc

from sqlalchemy.orm import Session

from tests.app.domain.models import Batch, OrderLine

T = TypeVar("T")


class AbstractRepository(Generic[T], abc.ABC, ContextDecorator):
    """Repository 패턴의 추상 인터페이스 입니다."""

    def __enter__(self) -> AbstractRepository[T]:
        """`module`:contextmanager`의 필수 인터페이스 구현."""
        return self

    def __exit__(
        self, typ: Any = None, value: Any = None, traceback: Any = None
    ) -> Literal[False]:
        self.close()
        return False

    def close(self) -> None:  # pylint: disable=no-self-use
        """레포지터리와 연결된 저장소 객체를 종료합니다."""
        return

    @abc.abstractmethod
    def add(self, item: T) -> None:
        """레포지터리에 :class:`T` 객체를 추가합니다."""
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, reference: str = "", **kwargs: str) -> Optional[T]:
        """주어진 레퍼런스 문자열에 해당하는 :class:`T` 객체를 조회합니다.

        해당하는 배치를 못 찾을 경우 ``None`` 을 리턴합니다.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def list(self) -> list[T]:
        """모든 배치 객체 리스트를 조회합니다."""
        raise NotImplementedError

    @abc.abstractmethod
    def delete(self, item: T) -> None:
        """레포지터리에서 :class:`T` 객체를 삭제합니다."""
        raise NotImplementedError

    @abc.abstractmethod
    def clear(self) -> None:
        """레포지터리 내의 모든 엔티티 데이터를 지웁니다."""
        raise NotImplementedError


class SqlAlchemyRepository(AbstractRepository[T]):
    """SqlAlchemy ORM을 저장소로 하는 :class:`AbstractRepository` 구현입니다."""

    def __enter__(self) -> SqlAlchemyRepository[T]:
        """`module`:contextmanager`의 필수 인터페이스 구현."""
        return self

    def __init__(self, session: Session):
        self.session = session  # pylint: disable=invalid-name

    def close(self) -> None:
        self.session.close()

    def add(self, item: T) -> None:
        self.session.add(item)

    def get(self, reference: str = "", **kwargs: str) -> Optional[T]:
        filter_by = {
            k: v
            for k, v in dict(reference=reference, **kwargs).items()
            if v is not None
        }
        return cast(Optional[T], self.session.query(T).filter_by(**filter_by).first())

    def delete(self, item: T) -> None:
        self.session.delete(item)

    def list(self) -> list[T]:
        return cast(list[T], self.session.query(T).all())

    def clear(self) -> None:
        self.session.execute("DELETE FROM allocation")
        self.session.execute("DELETE FROM batch")
        self.session.execute("DELETE FROM order_line")
