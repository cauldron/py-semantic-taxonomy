import orjson
from pydantic_settings import BaseSettings
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from py_semantic_taxonomy.adapters.persistence.tables import metadata_obj
from py_semantic_taxonomy.cfg import get_settings

base_settings = get_settings()


def create_engine(
    s: BaseSettings = base_settings,
    echo: bool = True,
) -> AsyncEngine:
    if s.db_backend == "postgres":
        connection_str = f"postgresql+asyncpg://{s.db_user}:{s.db_pass}@{s.db_host}:{s.db_port}/{s.db_name}"
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
        # Magic?
        # pool_pre_ping=True,
        # pool_size=global_settings.db_pool_size,
        # max_overflow=global_settings.db_max_overflow,
    )
    return engine


engine = create_engine()


async def init_db(engine: AsyncEngine = engine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(metadata_obj.create_all)


async def drop_db(engine: AsyncEngine = engine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(metadata_obj.drop_all)


# def get_bound_async_sessionmaker(engine: AsyncEngine = engine, **kwargs) -> async_sessionmaker:
#     return async_sessionmaker(bind=engine, **kwargs)


# bound_async_sessionmaker = get_bound_async_sessionmaker()
