import os

from fastmsa.core import AbstractConfig


class Config(AbstractConfig):
    def get_db_url(self) -> str:
        """Get API server's db uri.

        The url format should conform the SQLAlchemy's url scheme.
        """
        env = os.environ.get("ENV", "dev")
        if env == "prod":
            db_host = os.environ.get("DB_HOST", "localhost")
            db_user = os.environ.get("DB_USER", "postgres")
            db_pass = os.environ.get("DB_PASS", "test")
            db_name = os.environ.get("DB_NAME", db_user)

            return f"postgresql://{db_user}:{db_pass}@{db_host}/{db_name}"

        return "sqlite://"
