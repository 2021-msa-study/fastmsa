"""FastAPI 로 구현한 RESTful 서비스 앱."""
from typing import Any, Callable

from fastapi import FastAPI
from pydantic import BaseModel  # noqa

from fastmsa.core import FastMSA

# globals
app = FastAPI(title=__name__)  # pylint:


def init_app(
    msa: FastMSA, init_hook: Callable[[FastMSA, FastAPI], Any] = None
) -> FastAPI:
    """Flask 앱을 초기화 합니다.

    :mod:`app.routes.flask` 모듈에서 엔드포인트 라우팅 설정을 로드하고
    :meth:`.init_db` 를 호출하여 DB를 초기화 합니다.
    """

    if init_hook:
        init_hook(msa, app)

    msa.init_db()

    return app


route = app.route
post = app.post
get = app.get
put = app.put
delete = app.delete
