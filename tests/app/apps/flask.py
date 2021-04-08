"""Flask 로 구현한 RESTful 서비스 앱."""
from __future__ import annotations
from tests.app.domain.aggregates import Product
from tests.app.domain.models import Batch
from typing import Callable, Optional, Any, cast

from flask import Flask
from sqlalchemy.orm import sessionmaker

from tests.app.adapters import orm
from tests.app.adapters.orm import SessionMaker
from tests.app.adapters.repository import SqlAlchemyRepository

from tests.app import config

# types
_AnyFunc = Callable[..., Any]
RouteDecorator = Callable[..., Callable[[_AnyFunc], _AnyFunc]]
FlaskResponse = tuple[Any, int]

# globals
app = Flask(__name__)  # pylint: disable=invalid-name
get_session: SessionMaker = cast(SessionMaker, None)  # pylint: disable=invalid-name


def init_db(
    db_url: Optional[str] = None, drop_all: bool = False, show_log: bool = False
) -> SessionMaker:
    """DB 엔진을 초기화 합니다."""
    global get_session  # pylint: disable=global-statement, invalid-name

    if get_session:
        return get_session

    metadata = orm.start_mappers()
    engine = orm.init_engine(
        metadata,
        db_url or config.get_db_url(),
        connect_args=config.get_db_connect_args(),
        poolclass=config.get_db_poolclass(),
        drop_all=drop_all,
        show_log=show_log,
        isolation_level="REPEATABLE READ",
    )
    get_session = cast(SessionMaker, sessionmaker(engine))
    return get_session


def get_repo() -> SqlAlchemyRepository:
    """앱 DB와 연결된 레포지터리 객체를 리턴합니다."""
    return SqlAlchemyRepository(Product, get_session())


def init_app() -> Flask:
    """Flask 앱을 초기화 합니다.

    :mod:`app.routes.flask` 모듈에서 엔드포인트 라우팅 설정을 로드하고
    :meth:`.init_db` 를 호출하여 DB를 초기화 합니다.
    """
    # pylint: disable=import-outside-toplevel,cyclic-import, unused-import
    from ..routes import flask

    global get_session  # pylint: disable=global-statement, invalid-name
    get_session = init_db()
    return app


route: RouteDecorator = cast(RouteDecorator, app.route)
