from __future__ import annotations

import abc
from typing import Any, Callable, Optional, Type

import uvicorn
from sqlalchemy.pool import Pool, StaticPool
from sqlalchemy.sql.schema import MetaData


class FastMSA:
    """FastMSA App 설정."""

    title: str

    def __init__(self, name: str, title: Optional[str] = None):
        self.name = name

        if title:
            self.title = title

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
        """Get API server's db uri.

        The url format should conform the SQLAlchemy's url scheme.

        Example::

            db_host = os.environ.get("DB_HOST", "localhost")
            db_user = os.environ.get("DB_USER", "postgres")
            db_pass = os.environ.get("DB_PASS", "test")
            db_name = os.environ.get("DB_NAME", db_user)

            return f"postgresql://{db_user}:{db_pass}@{db_host}/{db_name}"
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
