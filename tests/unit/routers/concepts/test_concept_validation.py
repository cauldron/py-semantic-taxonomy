import json

import pytest
from pydantic import ValidationError

from py_semantic_taxonomy.adapters.routers.request_dto import Concept, ConceptCreate, ConceptUpdate
from py_semantic_taxonomy.domain.constants import SKOS


def test_top_level_concept(cn):
    assert Concept(**cn.concept_top)


def test_top_level_concept_model_dump(fixtures_dir, cn):
    expected = json.load(open(fixtures_dir / "top-concept.jsonld"))
    assert Concept(**cn.concept_top).model_dump() == expected


def test_concept_type(cn):
    obj = cn.concept_top
    obj["@type"] = ["http://www.w3.org/2001/XMLSchema#dateTime"]
    with pytest.raises(ValidationError):
        Concept(**obj)


def test_concept_pref_labels(cn):
    obj = cn.concept_top
    obj[f"{SKOS}prefLabel"] = [
        {"@value": "Something", "@language": "en"},
        {"@value": "Something else", "@language": "en"},
    ]
    with pytest.raises(ValidationError):
        Concept(**obj)


def test_concept_definition(cn):
    obj = cn.concept_top
    obj[f"{SKOS}definition"] = [
        {"@value": "Something", "@language": "en"},
        {"@value": "Something else", "@language": "en"},
    ]
    with pytest.raises(ValidationError):
        Concept(**obj)


def test_child_concept(cn):
    assert Concept(**cn.concept_mid)


def test_child_concept_model_dump(fixtures_dir, cn):
    expected = json.load(open(fixtures_dir / "child-concept.jsonld"))
    assert Concept(**cn.concept_mid).model_dump() == expected


def test_broader_self_reference(cn):
    obj = cn.concept_top
    assert ConceptCreate(**obj)
    obj[f"{SKOS}broader"] = [{"@id": obj["@id"]}]
    with pytest.raises(ValidationError):
        ConceptCreate(**obj)


def test_broader_not_allowed_in_update(cn):
    obj = cn.concept_top
    if f"{SKOS}narrower" in obj:
        del obj[f"{SKOS}narrower"]
    del obj[f"{SKOS}topConceptOf"]
    assert ConceptUpdate(**obj)
    with pytest.raises(ValidationError):
        ConceptUpdate(**(obj | {f"{SKOS}broader": []}))
    with pytest.raises(ValidationError):
        ConceptUpdate(**(obj | {f"{SKOS}broaderTransitive": []}))


def test_narrower_self_reference(cn):
    obj = cn.concept_top
    assert ConceptCreate(**obj)
    obj[f"{SKOS}narrower"] = [{"@id": obj["@id"]}]
    with pytest.raises(ValidationError):
        ConceptCreate(**obj)


def test_narrower_not_allowed_in_update(cn):
    obj = cn.concept_top
    if f"{SKOS}narrower" in obj:
        del obj[f"{SKOS}narrower"]
    del obj[f"{SKOS}topConceptOf"]
    assert ConceptUpdate(**obj)
    with pytest.raises(ValidationError):
        ConceptUpdate(**(obj | {f"{SKOS}narrower": []}))
    with pytest.raises(ValidationError):
        ConceptUpdate(**(obj | {f"{SKOS}narrowerTransitive": []}))


def test_concept_must_be_in_at_least_one_scheme(cn):
    obj = cn.concept_top
    assert Concept(**obj)
    obj[f"{SKOS}inScheme"] = []
    with pytest.raises(ValidationError):
        Concept(**obj)


def test_concept_can_be_in_more_than_one_scheme(cn):
    obj = cn.concept_top
    assert Concept(**obj)
    obj[f"{SKOS}inScheme"].append({"@id": "http://example.foo/scheme"})
    assert Concept(**obj)


def test_pref_label_notation_overlap_error(cn):
    obj = cn.concept_top
    assert Concept(**obj)
    obj[f"{SKOS}notation"] = [
        {
            "@type": "http://www.w3.org/1999/02/22-rdf-syntax-ns#PlainLiteral",
            "@value": obj[f"{SKOS}prefLabel"][0]["@value"],
        }
    ]
    with pytest.raises(ValidationError):
        Concept(**obj)


def test_alt_label_notation_overlap(cn):
    obj = cn.concept_top
    obj[f"{SKOS}altLabel"] = [{"@value": "Cow goes moo", "@language": "en"}]
    obj[f"{SKOS}notation"] = [
        {
            "@type": "http://www.w3.org/1999/02/22-rdf-syntax-ns#PlainLiteral",
            "@value": "Cow goes moo",
        }
    ]
    assert Concept(**obj)
