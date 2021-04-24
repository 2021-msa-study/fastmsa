from __future__ import annotations

import abc
from typing import Any, Callable, Optional, Type

import uvicorn
from sqlalchemy.pool import Pool, StaticPool
from sqlalchemy.sql.schema import MetaData


class AbstractConfig(abc.ABC):
    """App Configurations."""

    def get_api_host(self) -> str:
        """Get API server's host address."""
        return "127.0.0.1"

    def get_api_port(self) -> int:
        """Get API server's host port."""
        return 5000

    def get_api_url(self) -> str:
        """Get API server's full url."""
        return f"http://{self.get_api_host()}:{self.get_api_port()}"

    @abc.abstractmethod
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


DEFAULT_APP: Optional[FastMSA] = None


class FastMSA:
    def __init__(self, name: str, config: AbstractConfig):
        global DEFAULT_APP

        self.name = name
        self._config = config

        if not DEFAULT_APP:
            DEFAULT_APP = self

    @property
    def app(self):
        from .api import app

        return app

    def run(self, reload=False):
        uvicorn.run(f"fastmsa.api:app", reload=reload)

    @property
    def config(self) -> AbstractConfig:
        return self._config

    def init_db(
        self, drop_all=False, init_hooks: list[Callable[[MetaData], Any]] = None
    ):
        from fastmsa import orm

        return orm.init_db(drop_all=drop_all, init_hooks=init_hooks, config=self.config)


def get_config() -> AbstractConfig:
    if DEFAULT_APP:
        return DEFAULT_APP.config

    raise ValueError("초기화된 FastMSA 앱이 없습니다.")


class FastMSAError(Exception):
    """``FastMSA`` 와 관련된 모든 에러의 기본 클래스."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

    ...
