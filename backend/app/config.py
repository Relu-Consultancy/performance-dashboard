import os
from pydantic_settings import BaseSettings


def _normalize_db_url(url: str) -> str:
    # Render (and some other hosts) hand out "postgres://", but SQLAlchemy 2.0 requires "postgresql://"
    if url.startswith("postgres://"):
        return "postgresql://" + url[len("postgres://"):]
    return url


class Settings(BaseSettings):
    secret_key: str = os.environ.get("PMDASH_SECRET_KEY", "dev-secret-change-me")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days
    database_url: str = _normalize_db_url(os.environ.get("PMDASH_DATABASE_URL", "sqlite:///./pmdash.db"))


settings = Settings()
