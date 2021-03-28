"""App Configurations."""
from __future__ import annotations
from typing import Any, Optional
import os

from sqlalchemy.pool import StaticPool, Pool


def get_api_host() -> str:
    """Get API server's host address."""
    return "127.0.0.1"


def get_api_port() -> int:
    """Get API server's host port."""
    return 5000


def get_api_url() -> str:
    """Get API server's full url."""
    return f'http://{get_api_host()}:{get_api_port()}'


def get_db_url() -> str:
    """Get API server's db uri.

    The url format should conform the SQLAlchemy's url scheme.
    """
    db_host = os.environ.get('DB_HOST', 'localhost')
    db_user = os.environ.get('DB_USER', 'smprc')
    db_pass = os.environ.get('DB_PASS', 'test')
    db_name = os.environ.get('DB_NAME', db_user)
    return f"postgresql://{db_user}:{db_pass}@{db_host}/{db_name}"


def get_db_connect_args() -> dict[str, Any]:
    """Get db connection arguments for SQLAlchemy's engine creation.

    Example:
        For SQLite dbs, it could be: ::

            {'check_same_thread': False}
    """
    return {}


def get_db_poolclass() -> Optional[Pool]:
    """Get db poolclass arguemnt for SQLAlchemy's engine creation.

    Returns:
        A pool class

    """
    return StaticPool
