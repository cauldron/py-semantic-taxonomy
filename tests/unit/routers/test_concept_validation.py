import json

import pytest
from pydantic import ValidationError

from py_semantic_taxonomy.adapters.routers.request_dto import Concept


def test_top_level_concept(cn):
    assert Concept(**cn[0])


def test_top_level_concept_model_dump(fixtures_dir, cn):
    expected = json.load(open(fixtures_dir / "top-concept.jsonld"))
    assert Concept(**cn[0]).model_dump() == expected


def test_concept_type(cn):
    obj = cn[0]
    obj["@type"] = ["http://www.w3.org/2001/XMLSchema#dateTime"]
    with pytest.raises(ValidationError):
        Concept(**obj)


def test_concept_pref_labels(cn):
    obj = cn[0]
    obj["http://www.w3.org/2004/02/skos/core#prefLabel"] = [
        {"@value": "Something", "@language": "en"},
        {"@value": "Something else", "@language": "en"},
    ]
    with pytest.raises(ValidationError):
        Concept(**obj)


def test_concept_definition(cn):
    obj = cn[0]
    obj["http://www.w3.org/2004/02/skos/core#definition"] = [
        {"@value": "Something", "@language": "en"},
        {"@value": "Something else", "@language": "en"},
    ]
    with pytest.raises(ValidationError):
        Concept(**obj)


def test_child_concept(cn):
    assert Concept(**cn[1])


def test_child_concept_model_dump(fixtures_dir, cn):
    expected = json.load(open(fixtures_dir / "child-concept.jsonld"))
    assert Concept(**cn[1]).model_dump() == expected


def test_broader_self_reference(cn):
    obj = cn[0]
    assert Concept(**obj)
    obj["http://www.w3.org/2004/02/skos/core#broader"] = [{"@id": obj["@id"]}]
    with pytest.raises(ValidationError):
        Concept(**obj)


def test_narrower_self_reference(cn):
    obj = cn[0]
    assert Concept(**obj)
    obj["http://www.w3.org/2004/02/skos/core#narrower"] = [{"@id": obj["@id"]}]
    with pytest.raises(ValidationError):
        Concept(**obj)
