import orjson
from enum import Enum
from pydantic_settings import BaseSettings
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from py_semantic_taxonomy.cfg import get_settings
from py_semantic_taxonomy.adapters.persistence.tables import Base

base_settings = get_settings()


class DatabaseChoice(Enum):
    postgres = "postgres"
    sqlite = "sqlite"


async def create_engine(
    s: BaseSettings = base_settings,
    database: DatabaseChoice = DatabaseChoice.postgres,
    echo: bool = False,
    init_db: bool = True
) -> AsyncEngine:
    if database == DatabaseChoice.postgres:
        connection_str = f"postgresql+asyncpg://{s.db_user}:{s.db_pass.get_secret_value()}@{s.db_host}:{s.db_port}/{s.db_name}"
    else:
        # Only for testing
        connection_str = f"sqlite+aiosqlite:///:memory:"
    engine = create_async_engine(
        connection_str,
        json_serializer=lambda obj: orjson.dumps(obj),
        json_deserializer=lambda obj: orjson.loads(obj),
        echo=echo,
        # Magic?
        # pool_pre_ping=True,
        # pool_size=global_settings.db_pool_size,
        # max_overflow=global_settings.db_max_overflow,
    )
    if init_db:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    return engine
