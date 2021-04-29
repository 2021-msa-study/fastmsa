"""기본 환경 설정."""

from __future__ import annotations

import importlib
import sys
from configparser import ConfigParser
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Type, cast

from sqlalchemy.pool import Pool, StaticPool

from fastmsa.core.models import AbstractFastMSA, AbstractMessageBroker
from fastmsa.redis import RedisClient, RedisConnectInfo


@dataclass
class FastMSASetupConfig:
    name: str
    title: Optional[str] = None
    module_name: Optional[str] = None
    module_path: Optional[str] = None


def load_setupcfg(path: Path) -> Optional[FastMSASetupConfig]:
    if (path / "setup.cfg").exists():
        # 현재 경로에 "setup.cfg" 파일이 있다면 [fastmsa] 섹션에서
        # name, module 등의 정보를 읽습니다.
        config = ConfigParser()
        config.read("setup.cfg")
        if "fastmsa" in config:
            return FastMSASetupConfig(**config["fastmsa"])
    return None


@dataclass
class FastMSA(AbstractFastMSA):
    """FastMSA App 설정."""

    name: str
    title: str
    module_path: Path
    module_name: str
    allow_external_event = False

    """외부 메세지 브로커를 사용할지 여부."""
    is_implicit_name: bool = True
    """setup.cfg 없이 암시적으로 부여된 이름인지 여부."""
    _redis: Optional[RedisClient] = None

    @staticmethod
    def load_from_config(path=Path(".")) -> FastMSA:
        """`name` 정보를 이용해  `config.py` 를 로드한다."""
        cfg = load_setupcfg(path)
        name = path.name
        title = name
        module_name = name
        module_path = Path(".") / name
        is_implicit_name = True

        if cfg:
            is_implicit_name = False
            name = cfg.name
            module_name = cfg.module_name or module_name
            title = cfg.title or title

            if cfg.module_path:
                module_path = Path(cfg.module_path)
            elif module_name:
                module_path = Path(module_name.replace(".", "/"))

        abs_path = str(path.absolute())
        kwargs = dict(
            name=name,
            title=title,
            module_name=module_name,
            module_path=module_path,
            is_implicit_name=is_implicit_name,
        )

        assert name.isidentifier()

        if (module_path / "config.py").exists():
            if abs_path not in sys.path:
                sys.path.insert(0, abs_path)

            conf_module = importlib.import_module(f"{module_name}.config")
            config = cast(Type[FastMSA], getattr(conf_module, "Config"))
            # config.py 파일이 발견되면 이 설정을 로드합니다.
            return cast(FastMSA, config(**kwargs))

        return FastMSA(**kwargs)

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

    @property
    def message_broker(self) -> Optional[AbstractMessageBroker]:
        if not self.allow_external_event:
            return None
        else:
            if not self._redis:
                self._redis = RedisClient(self.redis_conn_info)
            return self._redis

    @property
    def redis_conn_info(self) -> RedisConnectInfo:
        return RedisConnectInfo(
            host="localhost",
            port=6379,
        )

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


class Config(FastMSA):
    """기본 ."""

    title = "FastMSA"

    def get_db_url(self) -> str:
        """DB 접속 정보."""
        return "sqlite://"
