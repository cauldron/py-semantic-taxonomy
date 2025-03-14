import pytest
from pydantic import ValidationError

from py_semantic_taxonomy.adapters.routers.request_dto import KOSCommon
from py_semantic_taxonomy.domain.constants import SKOS


def test_kos_common_fixture_valid(cn):
    assert KOSCommon(**cn.concept_top)


def test_kos_common_pref_labels_one_per_language(cn):
    obj = cn.concept_top
    obj[f"{SKOS}prefLabel"] = [
        {"@value": "Something", "@language": "en"},
        {"@value": "Something else", "@language": "en"},
    ]
    with pytest.raises(ValidationError):
        KOSCommon(**obj)


def test_kos_common_pref_label_missing(cn):
    obj = cn.concept_top
    obj[f"{SKOS}prefLabel"] = []
    with pytest.raises(ValidationError):
        KOSCommon(**obj)
