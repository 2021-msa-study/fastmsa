# pylint: disable=redefined-outer-name, protected-access
"""pytest 에서 사용될 전역 Fixture들을 정의합니다."""
from __future__ import annotations

from typing import Callable, Optional, Tuple

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from fastmsa import FastMSA
from fastmsa.orm import SessionMaker, clear_mappers, init_db, start_mappers
from fastmsa.repo import SqlAlchemyRepository
from fastmsa.uow import AbstractUnitOfWork, SqlAlchemyUnitOfWork
from tests.app.adapters.orm import init_mappers
from tests.app.domain.aggregates import Product

# types

SqlAlchemyRepoMaker = Callable[[], SqlAlchemyRepository]
AddStockLines = list[Tuple[str, str, int, Optional[str]]]
""":meth:`add_stock` 함수의 인자 타입."""
AddStockFunc = Callable[[AddStockLines], None]
""":meth:`add_stock` 함수 타입."""

from tests.app.config import Config


@pytest.fixture
def session() -> Session:
    """테스트에 사용될 새로운 :class:`.Session` 픽스처를 리턴합니다.

    :rtype: :class:`~sqlalchemy.orm.Session`
    """
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    clear_mappers()
    metadata = start_mappers(use_exist=False, init_hooks=[init_mappers])
    metadata.create_all(engine)
    return sessionmaker(engine)()


@pytest.fixture
def msa(session):
    from tests.app.routes import fastapi  # noqa

    init_event_handlers()
    return Config(__name__)


@pytest.fixture
def get_session(msa: FastMSA) -> SessionMaker:
    """:class:`.Session` 팩토리 메소드(:class:`~app.adapters.orm.SessionMaker`)
    를 리턴하는 픽스쳐 입니다.

    호출시마다 :meth:`fastmsa.orm.init_db` 을 호출(`drop_all=True`)하여
    모든 DB 엔티티를 매번 재생성합니다.

    :rtype: :class:`~app.adapters.orm.SessionMaker`
    """
    return init_db(drop_all=True, init_hooks=[init_mappers])


@pytest.fixture
def get_repo(get_session: SessionMaker) -> SqlAlchemyRepoMaker:
    """:class:`SqlAlchemyRepository` 팩토리 함수를 리턴하는 픽스쳐입니다."""
    return lambda: SqlAlchemyRepository(Product, get_session())


@pytest.fixture
def get_uow(get_session: SessionMaker) -> Callable[[], AbstractUnitOfWork[Product]]:
    return lambda: SqlAlchemyUnitOfWork(Product, get_session)


def init_event_handlers():
    import tests.app.handlers.batch  # noqa
