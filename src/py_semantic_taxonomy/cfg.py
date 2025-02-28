from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    db_backend: str = "postgres"

    # allow_origins: Set[str] = {
    #     "https://brightway.cauldron.ch",
    #     "https://brightway-lca.cloud",
    #     "https://brightway-lca.com",
    # }
    model_config = SettingsConfigDict(env_prefix="PyST_", env_file=".env")


def get_settings() -> Settings:
    return Settings()
