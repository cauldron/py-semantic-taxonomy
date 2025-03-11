import orjson
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from py_semantic_taxonomy.adapters.persistence.tables import metadata_obj
from py_semantic_taxonomy.cfg import get_settings


def create_engine(
    echo: bool = True,
) -> AsyncEngine:
    s = get_settings()
    if s.db_backend == "postgres":
        connection_str = (
            f"postgresql+asyncpg://{s.db_user}:{s.db_pass}@{s.db_host}:{s.db_port}/{s.db_name}"
        )
    elif s.db_backend == "sqlite":
        # Only for testing
        connection_str = "sqlite+aiosqlite:///:memory:"
    else:
        raise ValueError(f"Missing or incorrect database backend `PyST_db_backend`: {s.db_backend}")
    engine = create_async_engine(
        connection_str,
        json_serializer=lambda obj: orjson.dumps(obj).decode(),
        json_deserializer=lambda obj: orjson.loads(obj),
        echo=echo,
    )
    # Magic?
    # pool_pre_ping=True,
    # pool_size=global_settings.db_pool_size,
    # max_overflow=global_settings.db_max_overflow,
    return engine


async def init_db(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(metadata_obj.create_all)


async def drop_db(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(metadata_obj.drop_all)
