import json

import pytest
from pydantic import ValidationError

from py_semantic_taxonomy.adapters.routers.request_dto import Concept, ConceptCreate, ConceptUpdate


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
    obj["http://www.w3.org/2004/02/skos/core#prefLabel"] = [
        {"@value": "Something", "@language": "en"},
        {"@value": "Something else", "@language": "en"},
    ]
    with pytest.raises(ValidationError):
        Concept(**obj)


def test_concept_definition(cn):
    obj = cn.concept_top
    obj["http://www.w3.org/2004/02/skos/core#definition"] = [
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
    obj["http://www.w3.org/2004/02/skos/core#broader"] = [{"@id": obj["@id"]}]
    with pytest.raises(ValidationError):
        ConceptCreate(**obj)


def test_broader_not_allowed_in_update(cn):
    obj = cn.concept_top
    del obj["http://www.w3.org/2004/02/skos/core#narrower"]
    del obj["http://www.w3.org/2004/02/skos/core#topConceptOf"]
    assert ConceptUpdate(**obj)
    with pytest.raises(ValidationError):
        ConceptUpdate(**(obj | {"http://www.w3.org/2004/02/skos/core#broader": []}))
    with pytest.raises(ValidationError):
        ConceptUpdate(**(obj | {"http://www.w3.org/2004/02/skos/core#broaderTransitive": []}))


def test_narrower_self_reference(cn):
    obj = cn.concept_top
    assert ConceptCreate(**obj)
    obj["http://www.w3.org/2004/02/skos/core#narrower"] = [{"@id": obj["@id"]}]
    with pytest.raises(ValidationError):
        ConceptCreate(**obj)


def test_narrower_not_allowed_in_update(cn):
    obj = cn.concept_top
    del obj["http://www.w3.org/2004/02/skos/core#narrower"]
    del obj["http://www.w3.org/2004/02/skos/core#topConceptOf"]
    assert ConceptUpdate(**obj)
    with pytest.raises(ValidationError):
        ConceptUpdate(**(obj | {"http://www.w3.org/2004/02/skos/core#narrower": []}))
    with pytest.raises(ValidationError):
        ConceptUpdate(**(obj | {"http://www.w3.org/2004/02/skos/core#narrowerTransitive": []}))


def test_concept_must_be_in_at_least_one_scheme(cn):
    obj = cn.concept_top
    assert Concept(**obj)
    obj["http://www.w3.org/2004/02/skos/core#inScheme"] = []
    with pytest.raises(ValidationError):
        Concept(**obj)


def test_concept_can_be_in_more_than_one_scheme(cn):
    obj = cn.concept_top
    assert Concept(**obj)
    obj["http://www.w3.org/2004/02/skos/core#inScheme"].append({"@id": "http://example.foo/scheme"})
    assert Concept(**obj)


def test_pref_label_notation_overlap_error(cn):
    obj = cn.concept_top
    assert Concept(**obj)
    obj["http://www.w3.org/2004/02/skos/core#notation"] = [
        {
            "@type": "http://www.w3.org/1999/02/22-rdf-syntax-ns#PlainLiteral",
            "@value": obj["http://www.w3.org/2004/02/skos/core#prefLabel"][0]["@value"],
        }
    ]
    with pytest.raises(ValidationError):
        Concept(**obj)


def test_alt_label_notation_overlap(cn):
    obj = cn.concept_top
    obj["http://www.w3.org/2004/02/skos/core#altLabel"] = [
        {"@value": "Cow goes moo", "@language": "en"}
    ]
    obj["http://www.w3.org/2004/02/skos/core#notation"] = [
        {
            "@type": "http://www.w3.org/1999/02/22-rdf-syntax-ns#PlainLiteral",
            "@value": "Cow goes moo",
        }
    ]
    assert Concept(**obj)
