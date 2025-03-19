import orjson
import structlog
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from py_semantic_taxonomy.adapters.persistence.tables import metadata_obj
from py_semantic_taxonomy.cfg import get_settings

logger = structlog.get_logger("py-semantic-taxonomy")


def create_engine(
    echo: bool = False,
) -> AsyncEngine:
    s = get_settings()
    if s.db_backend == "postgres":
        connection_str = (
            f"postgresql+asyncpg://{s.db_user}:{s.db_pass}@{s.db_host}:{s.db_port}/{s.db_name}"
        )
        logger.info("Using Postgres backend at %s:%s", s.db_host, s.db_port)
    elif s.db_backend == "sqlite":
        # Only for testing
        connection_str = "sqlite+aiosqlite:///:memory:"
        logger.info("Using in-memory SQLite backend")
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
    logger.info("Initializing relational database")
    async with engine.begin() as conn:
        await conn.run_sync(metadata_obj.create_all)


async def drop_db(engine: AsyncEngine) -> None:
    logger.info("Dropping relational database")
    async with engine.begin() as conn:
        await conn.run_sync(metadata_obj.drop_all)
