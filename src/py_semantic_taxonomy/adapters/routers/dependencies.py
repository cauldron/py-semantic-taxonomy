from py_semantic_taxonomy.adapters.persistence import PostgresKOSGraph


def get_kos_graph():
    return PostgresKOSGraph()
