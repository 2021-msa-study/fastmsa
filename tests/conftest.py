# pylint: disable=redefined-outer-name, protected-access
"""pytest 에서 사용될 전역 Fixture들을 정의합니다."""
from __future__ import annotations
from typing import Optional, Callable, Generator, Tuple, cast
from datetime import datetime

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
import pytest

from .app.adapters.orm import start_mappers, SessionMaker
from .app.adapters.repository import SqlAlchemyRepository
from .app.domain.models import Batch
from .app.services.uow import AbstractUnitOfWork, SqlAlchemyUnitOfWork

from .app.apps.flask import init_app, init_db
from .e2e import FlaskServerThread

from tests.app.domain import aggregates

# XXX: pyright 에서 제대로 typing 을 찾지 못해 Casting 필요
Product = cast(aggregates.Aggregate[Batch], aggregates.Product)

# types

SqlAlchemyRepoMaker = Callable[[], SqlAlchemyRepository]
AddStockLines = list[Tuple[str, str, int, Optional[str]]]
""":meth:`add_stock` 함수의 인자 타입."""
AddStockFunc = Callable[[AddStockLines], None]
""":meth:`add_stock` 함수 타입."""


@pytest.fixture
def session() -> Session:
    """테스트에 사용될 새로운 :class:`.Session` 픽스처를 리턴합니다.

    :rtype: :class:`~sqlalchemy.orm.Session`
    """
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    metadata = start_mappers(use_exist=True)
    metadata.create_all(engine)
    return sessionmaker(engine)()


@pytest.fixture
def get_session() -> SessionMaker:
    """:class:`.Session` 팩토리 메소드(:class:`~app.adapters.orm.SessionMaker`)
    를 리턴하는 픽스쳐 입니다.

    호출시마다 :meth:`~app.apps.flask.init_db` 을 호출(`drop_all=True`)하여
    모든 DB 엔티티를 매번 재생성합니다.

    :rtype: :class:`~app.adapters.orm.SessionMaker`
    """
    return init_db(drop_all=True)


@pytest.fixture
def get_repo(get_session: SessionMaker) -> SqlAlchemyRepoMaker:
    """:class:`SqlAlchemyRepository` 팩토리 함수를 리턴하는 픽스쳐입니다."""
    return lambda: SqlAlchemyRepository(Batch, get_session())


@pytest.fixture
def get_uow(get_session: SessionMaker) -> Callable[[], AbstractUnitOfWork[Batch]]:
    return lambda: SqlAlchemyUnitOfWork(Product, get_session)


@pytest.fixture
# pylint: disable=unused-argument
def server(get_session: SessionMaker) -> Generator[FlaskServerThread, None, None]:
    # noqa
    """:class:`ServerThread` 로 구현된 재시작 가능한 멀티스레드 Flask 서버를
    리턴하는 픽스쳐입니다.

    픽스쳐 사용후에는 `shutdown`을 통해 서버를 종료합니다.
    """
    test_app = init_app()
    server = FlaskServerThread(test_app)
    server.start()

    yield server

    server.shutdown()
