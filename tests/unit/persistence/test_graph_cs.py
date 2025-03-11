import pytest

from py_semantic_taxonomy.domain.entities import (
    ConceptScheme,
    ConceptSchemeNotFoundError,
    DuplicateIRI,
)


async def test_get_object_type_concept(sqlite, graph):
    cs = await graph.get_object_type(iri="http://data.europa.eu/xsp/cn2024/cn2024")
    assert cs is ConceptScheme, "Wrong result type"


async def test_get_concept_scheme(sqlite, entities, graph):
    cs = await graph.concept_scheme_get(iri="http://data.europa.eu/xsp/cn2024/cn2024")
    assert isinstance(cs, ConceptScheme), "Wrong result type"
    assert cs == entities[2]  # Check all data attributes correct


async def test_get_concept_scheme_not_found(sqlite, graph):
    with pytest.raises(ConceptSchemeNotFoundError):
        await graph.concept_scheme_get(iri="http://data.europa.eu/xsp/cn2024/woof")

