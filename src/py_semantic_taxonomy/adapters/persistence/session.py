from sqlalchemy.ext.asyncio import async_sessionmaker
from py_semantic_taxonomy.adapters.persistence.engine import create_engine


engine = create_engine()

# Just currying the creation of `Session` objects
# https://docs.sqlalchemy.org/en/20/orm/session_basics.html#using-a-sessionmaker
# Separate file to make monkeypatching in tests easy
Session = async_sessionmaker(autocommit=False, autoflush=True, bind=engine)
