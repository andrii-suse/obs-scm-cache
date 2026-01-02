from pydantic_settings import BaseSettings
from os import environ


class Settings(BaseSettings):
    database_url: str = environ.get("OBS_SCM_CACHE_DB_URL", "")
    echo_sql: bool = True
    test: bool = False
    project_name: str = "OBS SCM Cache"
    oauth_token_secret: str = "TBD"
    log_level: str = "DEBUG"


settings = Settings()  # type: ignore
