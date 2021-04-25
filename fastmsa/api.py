"""FastAPI 로 구현한 RESTful 서비스 앱."""
from typing import Any, Callable

from fastapi import FastAPI

from fastmsa.core import FastMSA

# globals
app: FastAPI = FastAPI(title=__name__)  # pylint:


def init_app(
    msa: FastMSA, init_hook: Callable[[FastMSA, FastAPI], Any] = None
) -> FastAPI:
    """FastAPI 앱을 초기화 합니다.

    :mod:`app.routes` 모듈 및에 정의된 엔드포인트 라우팅 설정을 로드하고
    :meth:`fastmsa.orm.init_db` 를 호출하여 DB를 초기화 합니다.
    """
    from fastmsa.orm import init_db  # noqa

    if init_hook:
        init_hook(msa, app)

    init_db()

    return app
