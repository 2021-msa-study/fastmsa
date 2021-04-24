"""ORM 어댑터 모듈"""
from __future__ import annotations

import abc
import io
import logging
import re
from contextlib import AbstractContextManager, contextmanager
from typing import Any, Callable, Generator, Optional, Type, Union, cast

from sqlalchemy import MetaData, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import clear_mappers as _clear_mappers
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session
from sqlalchemy.pool import Pool

from fastmsa.core import FastMSA

SessionMaker = Callable[[], Session]
"""Session 팩토리 타입."""
ScopedSession = AbstractContextManager[Session]
metadata: Optional[MetaData] = None

__session_factory: Optional[SessionMaker] = None


class AbstractSession(abc.ABC):
    """세션의 일반적인 작업(`commit`, `rollback`) 을 추상화한 클래스."""

    @abc.abstractmethod
    def commit(self) -> None:
        """트랜잭션을 커밋합니다."""
        raise NotImplementedError


def get_sessionmaker() -> SessionMaker:
    """기본설정으로 SqlAlchemy Session 팩토리를 만듭니다."""
    from fastmsa.core import get_config

    global __session_factory

    if not __session_factory:
        engine = init_engine(
            start_mappers(),
            get_config().get_db_url(),
            # isolation_level="REPEATABLE READ",
        )
        __session_factory = cast(SessionMaker, sessionmaker(engine))

    return __session_factory


_get_session: Optional[SessionMaker] = None  # pylint: disable=invalid-name


def init_db(
    db_url: Optional[str] = None,
    drop_all: bool = False,
    show_log: bool = False,
    init_hooks: list[Callable[[MetaData], Any]] = None,
    config: FastMSA = None,
) -> SessionMaker:
    """DB 엔진을 초기화 합니다."""
    global _get_session

    if _get_session:
        return _get_session

    metadata = start_mappers(init_hooks=init_hooks)

    engine = init_engine(
        metadata,
        db_url if db_url else (config.get_db_url() if config else "sqlite://"),
        connect_args=config.get_db_connect_args() if config else None,
        poolclass=config.get_db_poolclass() if config else None,
        drop_all=drop_all,
        show_log=show_log,
        # isolation_level="REPEATABLE READ",
    )
    _get_session = cast(SessionMaker, sessionmaker(engine))
    return _get_session


def start_mappers(
    use_exist: bool = True, init_hooks: list[Callable[[MetaData], Any]] = None
) -> MetaData:
    """도메인 객체들을 SqlAlchemy ORM 매퍼에 등록합니다."""
    global metadata  # pylint: disable=global-statement,invalid-name
    if use_exist and metadata:
        return metadata

    metadata = MetaData()

    # 사용자 매핑 함수 추가.
    if init_hooks:
        for hook in init_hooks:
            hook(metadata)

    return metadata


def clear_mappers() -> None:
    """ORM 매핑을 초기화 합니다."""
    _clear_mappers()


def init_engine(
    meta: MetaData,
    url: str,
    connect_args: Optional[dict[str, Any]] = None,
    poolclass: Optional[Type[Pool]] = None,
    show_log: Union[bool, dict[str, Any]] = False,
    isolation_level: Optional[str] = None,
    drop_all: bool = False,
) -> Engine:
    """ORM Engine을 초기화 합니다.

    TODO: 상세 설명 추가.
    """
    logger = logging.getLogger("sqlalchemy.engine.base.Engine")
    out = io.StringIO()
    logger.addHandler(logging.StreamHandler(out))
    engine = create_engine(
        url,
        connect_args=connect_args or {},
        poolclass=poolclass,
        echo=show_log,
        isolation_level=isolation_level,
    )

    if drop_all:
        meta.drop_all(engine)

    meta.create_all(engine)

    if show_log:
        log_txt = out.getvalue()
        if show_log is True:
            print("".join(re.findall("CREATE.*?\n\n", log_txt, re.DOTALL | re.I)))
        elif isinstance(show_log, dict):
            if show_log.get("all"):
                print(log_txt)

    return engine


def get_scoped_session(engine: Engine) -> Callable[[], ScopedSession]:
    """``with...`` 문으로 자동 리소스가 반환되는 세션을 리턴합니다.

    Example: ::

        with get_scoped_session() as db:
            batches = db.query(Batch).all()
            ...

    Args:
        engine: Engine.

    """
    session_factory = sessionmaker(engine)

    @contextmanager
    def scoped_session() -> Generator[Session, None, None]:
        session: Optional[Session] = None
        try:
            yield (session := session_factory())  # pylint: disable=superfluous-parens
        finally:
            if session:
                session.close()  # pylint: disable=no-member

    return scoped_session
