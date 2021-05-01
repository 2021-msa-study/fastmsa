"""FastMSA App Configuration."""


import os

from fastmsa.config import FastMSA
from fastmsa.uow import RepoMakerDict


class Config(FastMSA):
    """여기에 변경할 설정을 추가합니다.

    설정 가능한 모든 항목들은 `FastMSA` 클래스 정의를 참고하세요.
    """

    title = "Test APP"
    allow_external_event = True  # 외부 메세지 브로커와의 통신을 활성화합니다.

    @property
    def uow(self):
        from fastmsa.uow import SqlAlchemyUnitOfWork
        from tests.app.adapters.repos import SqlAlchemyProductRepository
        from tests.app.domain.aggregates import Product

        repo_maker: RepoMakerDict = {
            Product: lambda session: SqlAlchemyProductRepository(Product, session)
        }

        return SqlAlchemyUnitOfWork([Product], repo_maker=repo_maker)

    def get_db_url(self) -> str:
        """DB 접속 정보."""
        db_host = os.environ.get("DB_HOST", "localhost")
        db_user = os.environ.get("DB_USER", "postgres")
        db_pass = os.environ.get("DB_PASS", "test")
        db_name = os.environ.get("DB_NAME", db_user)
        return f"postgresql://{db_user}:{db_pass}@{db_host}/{db_name}"
