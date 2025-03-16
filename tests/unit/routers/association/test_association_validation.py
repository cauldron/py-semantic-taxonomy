import pytest
from pydantic import ValidationError

from py_semantic_taxonomy.adapters.routers.request_dto import Association


def test_association(cn):
    assert Association(**cn.association_top)


def test_association_model_dump(fixtures_dir, cn):
    assert Association(**cn.association_top).model_dump() == cn.association_top


def test_association_type(cn):
    obj = cn.association_top
    obj["@type"] = ["http://www.w3.org/2001/XMLSchema#dateTime"]
    with pytest.raises(ValidationError):
        Association(**obj)
