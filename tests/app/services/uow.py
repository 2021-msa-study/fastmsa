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
from typing import Optional, Generic, TypeVar, Any
from contextlib import AbstractContextManager
import abc

from sqlalchemy.orm import Session

from tests.app.adapters.repository import AbstractRepository, SqlAlchemyRepository
from tests.app.adapters.orm import SessionMaker, get_session as default_session_factory

T = TypeVar('T')


class AbstractUnitOfWork(Generic[T], AbstractContextManager[Session]):
    """UnitOfWork 패턴의 추상 인터페이스입니다.

    UnitOfWork(UoW)는 영구 저장소의 유일한 진입점이며, 로드된 객체의
    최신 상태를 계속 트래킹 합니다.
    """
    items: AbstractRepository[T]

    def __enter__(self) -> AbstractUnitOfWork[T]:
        """``with`` 블록에 진입했을때 실행되는 메소드입니다."""
        return self

    def __exit__(self, *args: Any) -> None:
        """``with`` 블록에서 빠져나갈 때 실행되는 메소드입니다."""
        self.rollback()  # commit() 안되었을때 변경을 롤백합니다.
        # (이미 커밋 되었을 경우 rollback은 아무 효과도 없음)

    @abc.abstractmethod
    def commit(self) -> None:
        """세션을 커밋합니다."""
        raise NotImplementedError

    @abc.abstractmethod
    def rollback(self) -> None:
        """세션을 롤백합니다."""
        raise NotImplementedError


class SqlAlchemyUnitOfWork(AbstractUnitOfWork[T]):
    """``SqlAlchemy`` ORM을 이용한 UnitOfWork 패턴 구현입니다."""

    #pylint: disable=super-init-not-called
    def __init__(self, get_session: Optional[SessionMaker] = None) -> None:
        """``SqlAlchemy`` 기반의 UoW를 초기화합니다."""
        if not get_session:
            self.get_session = default_session_factory()
        else:
            self.get_session = get_session
        self.committed = False
        self.session: Optional[Session] = None

    def __enter__(self) -> AbstractUnitOfWork[T]:
        """``with`` 블록에 진입했을 때 필요한 작업을 수행합니다.

        세션을 할당하고, ``batches`` 레포지터리를 초기화합니다.
        """
        self.session = self.get_session()
        self.batches = SqlAlchemyRepository(self.session)
        return super().__enter__()

    def __exit__(self, *args: Any) -> None:
        """``with`` 블록을 빠져나갈 때 필요한 작업을 수행합니다.

        세션을 close합니다.
        """
        super().__exit__(*args)
        if self.session:
            self.session.close()

    def commit(self) -> None:
        """세션을 커밋합니다."""
        self.committed = True
        if self.session:
            self.session.commit()

    def rollback(self) -> None:
        """세션을 롤백합니다."""
        if self.session:
            self.session.rollback()
