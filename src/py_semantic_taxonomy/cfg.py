from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    db_backend: str = "postgres"
    db_user: str = "missing"
    db_pass: str = "missing"
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "PyST"

    # allow_origins: Set[str] = {
    #     "https://brightway.cauldron.ch",
    #     "https://brightway-lca.cloud",
    #     "https://brightway-lca.com",
    # }
    model_config = SettingsConfigDict(env_prefix="PyST_", env_file=".env")


def get_settings() -> Settings:
    return Settings()
