from functools import lru_cache

from py_semantic_taxonomy.domain.ports import GraphService as GraphServiceProtocol
from py_semantic_taxonomy.domain.ports import KOSGraphDatabase, SearchEngine
from py_semantic_taxonomy.domain.ports import SearchService as SearchServiceProtocol


@lru_cache(maxsize=1)
def get_kos_graph() -> KOSGraphDatabase:
    # Import inside function so we don't import any database-related stuff in tests
    from py_semantic_taxonomy.adapters.persistence.graph import PostgresKOSGraphDatabase

    return PostgresKOSGraphDatabase()


@lru_cache(maxsize=1)
def get_search_engine() -> SearchEngine:
    from py_semantic_taxonomy.adapters.persistence.search_engine import TypesenseSearchEngine
    from py_semantic_taxonomy.cfg import get_settings

    settings = get_settings()
    return TypesenseSearchEngine(
        url=settings.typesense_url,
        api_key=settings.typesense_api_key,
        embedding_model=settings.typesense_embedding_model,
    )


@lru_cache(maxsize=1)
def get_graph_service() -> GraphServiceProtocol:
    from py_semantic_taxonomy.application.graph_service import GraphService

    return GraphService()


@lru_cache(maxsize=1)
def get_search_service() -> SearchServiceProtocol:
    from py_semantic_taxonomy.application.search_service import SearchService

    return SearchService()
