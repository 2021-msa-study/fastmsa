"""UnitOfWork 패턴 모듈.

UoW 는 영구 저장소의 유일한 진입점이며, 로드된 객체의 최신 상태를 계속 트래킹 합니다.
이를 통해 얻을 수 있는 3가지 이득은 다음과 같습니다.

- A *stable snapshot of the database* to work with, so the objects
  we use aren’t changing halfway through an operation
- A way to persist all of our *changes at once*, so if something goes wrong,
  we don’t end up in an inconsistent state
- A *simple API* to our persistence concerns and a handy place to get a repository
"""
from __future__ import annotations

import abc
from contextlib import AbstractContextManager
from typing import Any, Generic, Optional, Type, TypeVar

from sqlalchemy.orm import Session

from fastmsa.domain import Aggregate, Entity
from fastmsa.orm import SessionMaker, get_sessionmaker
from fastmsa.repo import AbstractRepository, SqlAlchemyRepository

E = TypeVar("E", bound=Entity)
A = TypeVar("A", bound=Aggregate)


class AbstractUnitOfWork(Generic[A], AbstractContextManager[Session]):
    """UnitOfWork 패턴의 추상 인터페이스입니다.

    UnitOfWork(UoW)는 영구 저장소의 유일한 진입점이며, 로드된 객체의
    최신 상태를 계속 트래킹 합니다.
    """

    repo: AbstractRepository[A]

    def __enter__(self) -> AbstractUnitOfWork[A]:
        """``with`` 블록에 진입했을때 실행되는 메소드입니다."""
        return self

    def __exit__(self, *args: Any) -> None:
        """``with`` 블록에서 빠져나갈 때 실행되는 메소드입니다."""
        self.rollback()  # commit() 안되었을때 변경을 롤백합니다.
        # (이미 커밋 되었을 경우 rollback은 아무 효과도 없음)

    def commit(self) -> None:
        """세션을 커밋합니다."""
        self._commit()

    def collect_new_messages(self):
        """처리된 Aggregate 객체에 추가된 이벤트를 수집합니다."""
        for agg in self.repo.seen:
            while agg.messages:
                yield agg.messages.pop(0)

    @abc.abstractmethod
    def _commit(self) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def rollback(self) -> None:
        """세션을 롤백합니다."""
        raise NotImplementedError


class SqlAlchemyUnitOfWork(AbstractUnitOfWork[A]):  # type: ignore
    """``SqlAlchemy`` ORM을 이용한 UnitOfWork 패턴 구현입니다."""

    # pylint: disable=super-init-not-called
    def __init__(
        self,
        agg_class: Type[A],
        get_session: Optional[SessionMaker] = None,
        items: Optional[list[A]] = None,
    ) -> None:
        """``SqlAlchemy`` 기반의 UoW를 초기화합니다."""
        super().__init__()

        if items is None:
            items = []

        if not get_session:
            self.get_session = get_sessionmaker()
        else:
            self.get_session = get_session

        self.committed = False
        self.session: Optional[Session] = None
        self.agg_class = agg_class

    def __repr__(self):
        return f"SqlAlchemyUnitOfWork[{self.agg_class}]"

    def __enter__(self) -> AbstractUnitOfWork[A]:
        """``with`` 블록에 진입했을 때 필요한 작업을 수행합니다.

        세션을 할당하고, ``batches`` 레포지터리를 초기화합니다.
        """
        self.session = self.get_session()
        self.repo = SqlAlchemyRepository[A](
            self.agg_class,
            self.session,
        )
        return super().__enter__()

    def __exit__(self, *args: Any) -> None:
        """``with`` 블록을 빠져나갈 때 필요한 작업을 수행합니다.

        세션을 close합니다.
        """
        super().__exit__(*args)
        if self.session:
            self.session.close()

    def _commit(self) -> None:
        """세션을 커밋합니다."""
        self.committed = True
        if self.session:
            self.session.commit()

    def rollback(self) -> None:
        """세션을 롤백합니다."""
        if self.session:
            self.session.rollback()
