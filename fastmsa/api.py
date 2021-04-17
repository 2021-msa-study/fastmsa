"""FastAPI 로 구현한 RESTful 서비스 앱."""
from __future__ import annotations


from fastapi import FastAPI
from fastmsa.core import FastMSA
from typing import Callable, Any, cast

from pydantic import BaseModel

# globals
app = FastAPI(title=__name__)  # pylint: disable=invalid-name


def init_app(
    msa: FastMSA, init_hook: Callable[[FastMSA, FastAPI], Any] = None
) -> FastAPI:
    """Flask 앱을 초기화 합니다.

    :mod:`app.routes.flask` 모듈에서 엔드포인트 라우팅 설정을 로드하고
    :meth:`.init_db` 를 호출하여 DB를 초기화 합니다.
    """

    if init_hook:
        init_hook(msa, app)

    global get_session  # pylint: disable=global-statement, invalid-name
    get_session = msa.init_db()
    return app


route = app.route
post = app.post
get = app.get
put = app.put
delete = app.delete
