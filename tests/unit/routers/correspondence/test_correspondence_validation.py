import pytest
from pydantic import ValidationError

from py_semantic_taxonomy.adapters.routers.request_dto import Correspondence
from py_semantic_taxonomy.domain.constants import XKOS


def test_correspondence(cn):
    assert Correspondence(**cn.correspondence)


def test_correspondence_model_dump(fixtures_dir, cn):
    assert Correspondence(**cn.correspondence).model_dump() == cn.correspondence


def test_correspondence_type(cn):
    obj = cn.correspondence
    obj["@type"] = ["http://www.w3.org/2001/XMLSchema#dateTime"]
    with pytest.raises(ValidationError):
        Correspondence(**obj)


def test_correspondence_made_of(cn):
    obj = cn.correspondence
    obj[f"{XKOS}madeOf"] = []
    with pytest.raises(ValueError):
        Correspondence(**obj)
