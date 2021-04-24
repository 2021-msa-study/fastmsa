from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Any, Optional, Type, cast

import uvicorn
from sqlalchemy.pool import Pool, StaticPool


class FastMSA:
    """FastMSA App 설정."""

    title: str

    def __init__(self, name: str, title: Optional[str] = None):
        self.name = name

        if title:
            self.title = title

    @property
    def api(self):
        from fastmsa.api import app  # noqa

        return app

    def get_api_host(self) -> str:
        """Get API server's host address."""
        return "127.0.0.1"

    def get_api_port(self) -> int:
        """Get API server's host port."""
        return 5000

    def get_api_url(self) -> str:
        """Get API server's full url."""
        return f"http://{self.get_api_host()}:{self.get_api_port()}"

    def get_db_url(self) -> str:
        """SqlAlchemy 에서 사용 가능한 형식의 DB URL을 리턴합니다.

        다음처럼 OS 환경변수를 이용할 수도 있씁니다.

        if self.mode == "prod":
            db_host = os.environ.get("DB_HOST", "localhost")
            db_user = os.environ.get("DB_USER", "postgres")
            db_pass = os.environ.get("DB_PASS", "password")
            db_name = os.environ.get("DB_NAME", db_user)
            return f"postgresql://{db_user}:{db_pass}@{db_host}/{db_name}"
        else:
            return f"sqlite://"
        """

        raise NotImplementedError

    def get_db_connect_args(self) -> dict[str, Any]:
        """Get db connection arguments for SQLAlchemy's engine creation.

        Example:
            For SQLite dbs, it could be: ::

                {'check_same_thread': False}
        """
        return {}

    def get_db_poolclass(self) -> Optional[Type[Pool]]:
        """Get db poolclass arguemnt for SQLAlchemy's engine creation.

        Returns:
            A pool class

        """
        return StaticPool

    def init_fastapi(self):
        """FastMSA 설정을 FastAPI 앱에 적용합니다."""
        from fastmsa.api import app

        app.title = self.title

    def run(self, reload=False):
        uvicorn.run(f"fastmsa.api:app", reload=reload)


class FastMSAError(Exception):
    """``FastMSA`` 와 관련된 모든 에러의 기본 클래스."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

    ...


def load_config(
    path: Optional[Path] = None,
    name: Optional[str] = None,
    module_name: Optional[str] = None,
) -> FastMSA:
    """`name` 정보를 이용해  `config.py` 를 로드한다."""
    if not path:
        path = Path(".").absolute()

    if not name:
        name = path.name

    if (path / name / "config.py").exists():
        module_name = module_name or name

        if path not in sys.path:
            sys.path.insert(0, str(path))

        conf_module = importlib.import_module(f"{module_name}.config")
        config = cast(Type[FastMSA], getattr(conf_module, "Config"))
        return config(name)

    return FastMSA(name)
