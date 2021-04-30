"""UnitOfWork 패턴 모듈.

SqlAlchemy를 이용한 기본 구현체를 제공합니다.
"""
from __future__ import annotations

from typing import Any, Callable, Optional, Sequence, Type

from fastmsa.core import (
    AbstractRepository,
    AbstractUnitOfWork,
    Aggregate,
    AggregateReposMap,
)
from fastmsa.logging import get_logger
from fastmsa.orm import Session, SessionMaker, get_sessionmaker
from fastmsa.repo import SqlAlchemyRepository

RepoMakerFunc = Callable[[Session], AbstractRepository]
RepoMakerDict = dict[Type[Aggregate], RepoMakerFunc]


logger = get_logger("fastmsa.uow")


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):  # type: ignore
    """``SqlAlchemy`` ORM을 이용한 UnitOfWork 패턴 구현입니다."""

    # pylint: disable=super-init-not-called
    def __init__(
        self,
        agg_classes: Sequence[Type[Aggregate]],
        get_session: Optional[SessionMaker] = None,
        repo_maker: Optional[RepoMakerDict] = None,
    ) -> None:
        """``SqlAlchemy`` 기반의 UoW를 초기화합니다."""
        super().__init__()
        self.agg_classes = agg_classes
        self.repos: AggregateReposMap = {}
        self.repo_maker = repo_maker or {}

        if not get_session:
            self.get_session = get_sessionmaker()
        else:
            self.get_session = get_session

        self.committed = False
        self.session: Optional[Session] = None

    def __repr__(self):
        return f"SqlAlchemyUnitOfWork[{self.repo_maker}]"

    def __enter__(self) -> AbstractUnitOfWork:
        """``with`` 블록에 진입했을 때 필요한 작업을 수행합니다.

        세션을 할당하고, ``batches`` 레포지터리를 초기화합니다.
        """
        super().__enter__()
        self.session = self.get_session()
        for agg_class in self.agg_classes:
            repo_maker = self.repo_maker.get(agg_class)
            self.repos[agg_class] = (
                repo_maker(self.session)
                if repo_maker
                else SqlAlchemyRepository(
                    agg_class,
                    self.session,
                )
            )
        return self

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
