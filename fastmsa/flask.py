"""Flask 로 구현한 RESTful 서비스 앱."""
from __future__ import annotations
from fastmsa.core import FastMsa
from typing import Callable, Any, cast

from fastmsa.orm import init_db

from flask import Flask

# types
_AnyFunc = Callable[..., Any]
RouteDecorator = Callable[..., Callable[[_AnyFunc], _AnyFunc]]
FlaskResponse = tuple[Any, int]

# globals
app = Flask(__name__)  # pylint: disable=invalid-name


def init_app(msa: FastMsa, init_hook: Callable[[FastMsa, Flask], Any] = None) -> Flask:
    """Flask 앱을 초기화 합니다.

    :mod:`app.routes.flask` 모듈에서 엔드포인트 라우팅 설정을 로드하고
    :meth:`.init_db` 를 호출하여 DB를 초기화 합니다.
    """

    if init_hook:
        init_hook(msa, app)

    global get_session  # pylint: disable=global-statement, invalid-name
    get_session = msa.init_db()
    return app


route: RouteDecorator = cast(RouteDecorator, app.route)
