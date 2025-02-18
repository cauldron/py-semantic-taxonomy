import json

import pytest
from pydantic import ValidationError

from py_semantic_taxonomy.adapters.routers.request_dto import ConceptScheme


def test_concept_scheme(cn):
    assert ConceptScheme(**cn[2])


def test_concept_schema_model_dump(fixtures_dir, cn):
    expected = json.load(open(fixtures_dir / "concept-scheme.jsonld"))
    assert ConceptScheme(**cn[2]).model_dump() == expected


def test_concept_scheme_type(cn):
    obj = cn[2]
    obj["@type"] = ["http://www.w3.org/2001/XMLSchema#dateTime"]
    with pytest.raises(ValidationError):
        ConceptScheme(**obj)
