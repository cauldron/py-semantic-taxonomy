import json

from py_semantic_taxonomy.adapters.routers.request_dto import Concept


def test_top_level_concept(cn):
    assert Concept(**cn[0])


def test_top_level_concept_model_dump(fixtures_dir, cn):
    expected = json.load(open(fixtures_dir / "top-concept.jsonld"))
    assert Concept(**cn[0]).model_dump() == expected


def test_child_concept(cn):
    assert Concept(**cn[1])


def test_child_concept_model_dump(fixtures_dir, cn):
    expected = json.load(open(fixtures_dir / "child-concept.jsonld"))
    assert Concept(**cn[1]).model_dump() == expected
