from dataclasses import fields

from py_semantic_taxonomy.adapters.routers import request_dto as request
from py_semantic_taxonomy.domain.constants import RDF_MAPPING as RDF
from py_semantic_taxonomy.domain.entities import MadeOf


def test_made_of_domain_request_dto_same_fields():
    domain_fields = {f.name for f in fields(MadeOf)}
    request_fields = set(request.MadeOf.model_fields)
    assert not domain_fields.difference(
        request_fields
    ), "Request validation and domain `madeof` model fields differ"
    assert not request_fields.difference(
        domain_fields
    ), "Request validation and domain `made_of` model fields differ"


def test_made_of_to_db_dict(made_of):
    given = made_of.to_db_dict()
    expected = dict(
        id_="http://data.europa.eu/xsp/cn2023/CN2023_CN2024",
        made_ofs=[
            {"@id": "http://data.europa.eu/xsp/cn2023/top_level_association"},
            {"@id": "http://data.europa.eu/xsp/cn2023/lower_association"},
        ],
    )
    assert given == expected, "Conversion to database dict failed"


def test_made_of_from_json_ld(made_of):
    given = MadeOf.from_json_ld(made_of.to_json_ld())
    expected = MadeOf(
        id_="http://data.europa.eu/xsp/cn2023/CN2023_CN2024",
        made_ofs=[
            {"@id": "http://data.europa.eu/xsp/cn2023/top_level_association"},
            {"@id": "http://data.europa.eu/xsp/cn2023/lower_association"},
        ],
    )
    assert given == expected, "Conversion from JSON-LD failed"


def test_made_of_to_json_ld(made_of):
    given = made_of.to_json_ld()
    expected = {
        "@id": "http://data.europa.eu/xsp/cn2023/CN2023_CN2024",
        RDF["made_ofs"]: [
            {"@id": "http://data.europa.eu/xsp/cn2023/top_level_association"},
            {"@id": "http://data.europa.eu/xsp/cn2023/lower_association"},
        ],
    }
    assert given == expected, "Conversion to JSON-LD failed"
