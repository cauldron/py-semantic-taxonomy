import json

import pytest
from pydantic import ValidationError

from py_semantic_taxonomy.adapters.routers.request_dto import ConceptScheme
from py_semantic_taxonomy.domain.constants import SKOS


def test_concept_scheme(cn):
    assert ConceptScheme(**cn.scheme)


def test_concept_schema_model_dump(fixtures_dir, cn):
    expected = json.load(open(fixtures_dir / "concept-scheme.jsonld"))
    assert ConceptScheme(**cn.scheme).model_dump() == expected


def test_concept_scheme_type(cn):
    obj = cn.scheme
    obj["@type"] = ["http://www.w3.org/2001/XMLSchema#dateTime"]
    with pytest.raises(ValidationError):
        ConceptScheme(**obj)


def test_concept_scheme_no_top_concept(cn):
    cn.scheme[f"{SKOS}hasTopConcept"] = [{"@id": "http://data.europa.eu/xsp/cn2024/010011000090"}]
    with pytest.raises(ValidationError):
        ConceptScheme(**cn.scheme)
