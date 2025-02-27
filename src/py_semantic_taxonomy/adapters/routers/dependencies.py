def get_kos_graph():
    # Import inside function so we don't import any database-related stuff in tests
    from py_semantic_taxonomy.adapters.persistence import PostgresKOSGraph

    return PostgresKOSGraph()
