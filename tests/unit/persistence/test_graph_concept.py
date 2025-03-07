import pytest

from py_semantic_taxonomy.domain.entities import Concept, ConceptNotFoundError


async def test_get_concept(sqlite, cn_db, entities):
    # Defer import until environment is patched
    from py_semantic_taxonomy.adapters.persistence.graph import PostgresKOSGraph

    graph = PostgresKOSGraph()
    concept = await graph.get_concept(iri="http://data.europa.eu/xsp/cn2024/010011000090")
    assert isinstance(concept, Concept), "Wrong result type"
    assert concept == entities[0]  # Check all data attributes correct


async def test_get_concept_not_found(sqlite, cn_db):
    # Defer import until environment is patched
    from py_semantic_taxonomy.adapters.persistence.graph import PostgresKOSGraph

    graph = PostgresKOSGraph()
    with pytest.raises(ConceptNotFoundError):
        await graph.get_concept(iri="http://data.europa.eu/xsp/cn2024/woof")


async def test_get_object_type_concept(sqlite, cn_db):
    # Defer import until environment is patched
    from py_semantic_taxonomy.adapters.persistence.graph import PostgresKOSGraph

    graph = PostgresKOSGraph()
    concept = await graph.get_object_type(iri="http://data.europa.eu/xsp/cn2024/010011000090")
    assert concept is Concept, "Wrong result type"
