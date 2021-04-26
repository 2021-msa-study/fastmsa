"""기본 환경 설정."""

from fastmsa.core import FastMSA


class Config(FastMSA):
    """기본 ."""

    title = "FastMSA"

    def get_db_url(self) -> str:
        """DB 접속 정보."""
        return "sqlite://"
