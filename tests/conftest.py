# pylint: disable=redefined-outer-name, protected-access
"""pytest 에서 사용될 전역 Fixture들을 정의합니다."""
from __future__ import annotations

from typing import Callable, Generator, Optional, Tuple

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from fastmsa.event import MessageHandlerMap
from fastmsa.orm import SessionMaker, clear_mappers, init_db, start_mappers
from fastmsa.repo import SqlAlchemyRepository
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


@pytest.fixture(scope="module")
def handlers() -> Generator[MessageHandlerMap, None, None]:
    yield init_handlers()


@pytest.fixture
def msa(handlers, session):
    from fastmsa.event import messagebus
    from tests.app.routes import fastapi  # noqa

    assert handlers, "Empty handlers!"
    msa = Config.load_from_config()
    messagebus.msa = msa  # XXX: Dependency Injection
    return msa


@pytest.fixture
def get_session() -> SessionMaker:
    """:class:`.Session` 팩토리 메소드(:class:`~app.adapters.orm.SessionMaker`)
    를 리턴하는 픽스쳐 입니다.

    호출시마다 :meth:`fastmsa.orm.init_db` 을 호출(`drop_all=True`)하여
    모든 DB 엔티티를 매번 재생성합니다.

    :rtype: :class:`~app.adapters.orm.SessionMaker`
    """
    return init_db(drop_all=False, init_hooks=[init_mappers])


def init_handlers() -> MessageHandlerMap:
    from fastmsa.event import MESSAGE_HANDLERS, messagebus
    from tests.app.adapters.repos import SqlAlchemyProductRepository
    from tests.app.handlers import batch, external  # noqa

    messagebus.uow = SqlAlchemyUnitOfWork(
        [Product],
        repo_maker={
            Product: lambda session: SqlAlchemyProductRepository(Product, session)
        },
    )

    # 테스트에 의해 글로벌 핸들러 레지스트리가 망가지지 않도록 복사본 리턴.
    return dict(MESSAGE_HANDLERS)
