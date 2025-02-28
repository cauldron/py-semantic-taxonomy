# Separate file to make monkeypatching in tests easy
from typing import Optional
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, create_async_engine
from py_semantic_taxonomy.adapters.persistence.engine import create_engine
from py_semantic_taxonomy.adapters.persistence.tables import Base


async def init_db() -> None:
    engine = create_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def async_session(
    engine_factory: Optional[create_async_engine] = None,
    autocommit: bool = True,
    autoflush: bool = False,
    **kwargs
) -> AsyncSession:
    if engine_factory is None:
        engine = create_engine()
    else:
        engine = engine_factory()
    session = async_sessionmaker(autocommit=False, autoflush=True, bind=engine, **kwargs)
    return session
