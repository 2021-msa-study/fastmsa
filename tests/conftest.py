# pylint: disable=redefined-outer-name, protected-access
"""pytest 에서 사용될 전역 Fixture들을 정의합니다."""
from __future__ import annotations

from typing import Callable, Generator, Optional, Tuple

import pytest
from fastapi.applications import FastAPI
from flask.app import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from fastmsa import FastMSA
from fastmsa.api import init_app
from fastmsa.flask import init_app as init_flask_app
from fastmsa.orm import SessionMaker, clear_mappers, start_mappers, init_db
from fastmsa.repo import SqlAlchemyRepository
from fastmsa.test.e2e import FlaskServerThread
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
def msa():
    return Config(__name__)


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
def get_session(msa: FastMSA) -> SessionMaker:
    """:class:`.Session` 팩토리 메소드(:class:`~app.adapters.orm.SessionMaker`)
    를 리턴하는 픽스쳐 입니다.

    호출시마다 :meth:`~app.apps.flask.init_db` 을 호출(`drop_all=True`)하여
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


def init_flask_routes(msa: FastMSA, app: Flask):
    from tests.app.routes import flask  # noqa

    ...


def init_routes(msa: FastMSA, app: FastAPI):
    from tests.app.routes import fastapi  # noqa

    ...


@pytest.fixture
# pylint: disable=unused-argument
def server(
    msa: FastMSA, get_session: SessionMaker
) -> Generator[FlaskServerThread, None, None]:
    # noqa
    """:class:`ServerThread` 로 구현된 재시작 가능한 멀티스레드 Flask 서버를
    리턴하는 픽스쳐입니다.

    픽스쳐 사용후에는 `shutdown`을 통해 서버를 종료합니다.
    """

    test_app = init_flask_app(msa, init_flask_routes)
    server = FlaskServerThread(msa, test_app)
    server.start()

    yield server

    server.shutdown()


@pytest.fixture
def server_fastapi(msa: FastMSA, get_session: SessionMaker):
    """:class:`ServerThread` 로 구현된 재시작 가능한 멀티스레드 Flask 서버를
    리턴하는 픽스쳐입니다.

    픽스쳐 사용후에는 `shutdown`을 통해 서버를 종료합니다.
    """

    test_app = init_app(msa, init_routes)
