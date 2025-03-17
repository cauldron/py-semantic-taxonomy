from functools import lru_cache

from py_semantic_taxonomy.domain.ports import KOSGraphDatabase, SearchService


@lru_cache(maxsize=1)
def get_kos_graph() -> KOSGraphDatabase:
    # Import inside function so we don't import any database-related stuff in tests
    from py_semantic_taxonomy.adapters.persistence.graph import PostgresKOSGraphDatabase

    return PostgresKOSGraphDatabase()


@lru_cache(maxsize=1)
def get_search() -> SearchService:
    from py_semantic_taxonomy.application.search_service import TypesenseSearch

    return TypesenseSearch()
