from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    db_backend: str = "postgres"
    db_user: str = "missing"
    db_pass: str = "missing"
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "PyST"

    auth_token: str = "missing"

    typesense_url: str = "missing"
    typesense_api_key: str = "missing"
    typesense_embedding_model: str = "ts/all-MiniLM-L12-v2"
    typesense_exclude_if_missing_for_language: bool = True

    languages: list[str] = ["en", "de", "es", "fr", "pt", "it", "da"]

    # allow_origins: Set[str] = {
    #     "https://brightway.cauldron.ch",
    #     "https://brightway-lca.cloud",
    #     "https://brightway-lca.com",
    # }
    model_config = SettingsConfigDict(
        env_prefix="PyST_", env_file="pyst-config.env", env_file_encoding="utf-8"
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
