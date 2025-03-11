import pytest

from py_semantic_taxonomy.domain.entities import Concept, ConceptNotFoundError, DuplicateIRI


async def test_get_object_type_concept(sqlite, cn_db):
    # Defer import until environment is patched
    from py_semantic_taxonomy.adapters.persistence.graph import PostgresKOSGraph

    graph = PostgresKOSGraph()
    concept = await graph.get_object_type(iri="http://data.europa.eu/xsp/cn2024/010011000090")
    assert concept is Concept, "Wrong result type"


async def test_get_concept(sqlite, cn_db, entities):
    # Defer import until environment is patched
    from py_semantic_taxonomy.adapters.persistence.graph import PostgresKOSGraph

    graph = PostgresKOSGraph()
    concept = await graph.concept_get(iri="http://data.europa.eu/xsp/cn2024/010011000090")
    assert isinstance(concept, Concept), "Wrong result type"
    assert concept == entities[0]  # Check all data attributes correct


async def test_get_concept_not_found(sqlite, cn_db):
    # Defer import until environment is patched
    from py_semantic_taxonomy.adapters.persistence.graph import PostgresKOSGraph

    graph = PostgresKOSGraph()
    with pytest.raises(ConceptNotFoundError):
        await graph.concept_get(iri="http://data.europa.eu/xsp/cn2024/woof")


async def test_create_concept(sqlite, cn_db, cn, entities):
    # Defer import until environment is patched
    from py_semantic_taxonomy.adapters.persistence.graph import PostgresKOSGraph

    graph = PostgresKOSGraph()
    expected = Concept.from_json_ld(cn.concept_low)

    response = await graph.concept_create(concept=expected)
    assert isinstance(response, Concept), "Wrong result type"
    assert response == expected, "Data attributes from database differ"

    given = await graph.concept_get(iri=cn.concept_low["@id"])
    assert given == expected, "Data attributes from database differ"


async def test_create_concept_duplicate(sqlite, cn_db, cn, entities):
    # Defer import until environment is patched
    from py_semantic_taxonomy.adapters.persistence.graph import PostgresKOSGraph

    graph = PostgresKOSGraph()
    with pytest.raises(DuplicateIRI):
        await graph.concept_create(concept=Concept.from_json_ld(cn.concept_top))
