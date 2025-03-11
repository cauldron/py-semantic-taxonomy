from functools import lru_cache


@lru_cache(size=1)
def get_kos_graph():
    # Import inside function so we don't import any database-related stuff in tests
    from py_semantic_taxonomy.adapters.persistence.graph import PostgresKOSGraph

    return PostgresKOSGraph()
