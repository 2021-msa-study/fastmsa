"""Flask 로 구현한 RESTful 서비스 앱."""
from __future__ import annotations

from typing import Any, Callable, Optional, cast

from flask import Flask

from fastmsa.core import FastMSA
from fastmsa.orm import SessionMaker

# types
_AnyFunc = Callable[..., Any]
RouteDecorator = Callable[..., Callable[[_AnyFunc], _AnyFunc]]
FlaskResponse = tuple[Any, int]

# globals
app = Flask(__name__)  # pylint: disable=invalid-name

get_session: Optional[SessionMaker] = None


def init_app(msa: FastMSA, init_hook: Callable[[FastMSA, Flask], Any] = None) -> Flask:
    """Flask 앱을 초기화 합니다.

    :mod:`app.routes.flask` 모듈에서 엔드포인트 라우팅 설정을 로드하고
    :meth:`.init_db` 를 호출하여 DB를 초기화 합니다.
    """
    global get_session  # pylint: disable=global-statement, invalid-name

    if init_hook:
        init_hook(msa, app)

    if not get_session:
        get_session = msa.init_db()

    return app


route: RouteDecorator = cast(RouteDecorator, app.route)
