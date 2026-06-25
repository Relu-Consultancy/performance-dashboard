import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    secret_key: str = os.environ.get("PMDASH_SECRET_KEY", "dev-secret-change-me")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days
    database_url: str = os.environ.get("PMDASH_DATABASE_URL", "sqlite:///./pmdash.db")


settings = Settings()
