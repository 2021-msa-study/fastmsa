# pylint: disable=redefined-outer-name, protected-access
"""pytest 에서 사용될 전역 Fixture들을 정의합니다."""
from __future__ import annotations

from typing import Callable, Generator, Optional, Tuple

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from fastmsa.event import MessageBus
from fastmsa.orm import (
    SessionMaker,
    clear_mappers,
    init_db,
    set_default_sessionmaker,
    start_mappers,
)
from fastmsa.repo import SqlAlchemyRepository
from fastmsa.test.e2e import FakeRedisClient, check_port_opened
from fastmsa.uow import SqlAlchemyUnitOfWork
from tests.app.adapters.orm import init_mappers
from tests.app.domain.aggregates import Product

# types

SqlAlchemyRepoMaker = Callable[[], SqlAlchemyRepository]
AddStockLines = list[Tuple[str, str, int, Optional[str]]]
""":meth:`add_stock` 함수의 인자 타입."""
AddStockFunc = Callable[[AddStockLines], None]
""":meth:`add_stock` 함수 타입."""

from tests.app.config import Config


def memory_sessionmaker():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    clear_mappers()
    metadata = start_mappers(use_exist=False, init_hooks=[init_mappers])
    metadata.create_all(engine)
    return sessionmaker(engine)


@pytest.fixture
def session() -> Session:
    """테스트에 사용될 새로운 :class:`.Session` 픽스처를 리턴합니다.

    :rtype: :class:`~sqlalchemy.orm.Session`
    """
    return memory_sessionmaker()()


@pytest.fixture(scope="module")
def messagebus() -> Generator[MessageBus, None, None]:
    import warnings

    from fastmsa.event import messagebus
    from tests.app.adapters.repos import SqlAlchemyProductRepository
    from tests.app.handlers import batch, external  # noqa

    if not check_port_opened(5432):
        warnings.warn(
            "PostgreSQL server is not running. Falling back to in-memory SQLite DB"
        )
        set_default_sessionmaker(memory_sessionmaker())

    messagebus.uow = SqlAlchemyUnitOfWork(
        [Product],
        repo_maker={
            Product: lambda session: SqlAlchemyProductRepository(Product, session)
        },
    )
    yield messagebus


@pytest.fixture
def msa(messagebus: MessageBus):
    import warnings

    from sqlalchemy.pool import StaticPool

    from tests.app.routes import fastapi  # noqa

    assert messagebus.handlers, "Empty handlers!"
    msa = Config.load_from_config()
    old_msa = messagebus.msa
    messagebus.msa = msa  # XXX: Dependency Injection

    if not check_port_opened(6379):
        warnings.warn("Redis server is not running. Falling back to FakeRedisClient")

    msa.broker.client = FakeRedisClient()

    yield msa

    messagebus.msa = old_msa


@pytest.fixture
def get_session() -> SessionMaker:
    """:class:`.Session` 팩토리 메소드(:class:`~app.adapters.orm.SessionMaker`)
    를 리턴하는 픽스쳐 입니다.

    호출시마다 :meth:`fastmsa.orm.init_db` 을 호출(`drop_all=True`)하여
    모든 DB 엔티티를 매번 재생성합니다.

    :rtype: :class:`~app.adapters.orm.SessionMaker`
    """
    return init_db(drop_all=False, init_hooks=[init_mappers])
