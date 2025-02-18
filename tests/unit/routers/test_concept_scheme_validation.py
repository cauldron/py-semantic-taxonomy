import json
from py_semantic_taxonomy.adapters.routers.request_dto import ConceptScheme, Concept


def test_concept_scheme(cn):
    assert ConceptScheme(**cn[2])


def test_concept_schema_model_dump(fixtures_dir, cn):
    expected = json.load(open(fixtures_dir / "concept-scheme.jsonld"))
    assert ConceptScheme(**cn[2]).model_dump() == expected
