from dataclasses import fields

from py_semantic_taxonomy.adapters.routers import request_dto as request
from py_semantic_taxonomy.adapters.routers import response_dto as response
from py_semantic_taxonomy.domain.entities import Correspondence


def test_correspondence_domain_request_dto_same_fields():
    domain_fields = {f.name for f in fields(Correspondence)}
    request_fields = set(request.Correspondence.model_fields)
    assert domain_fields.difference(request_fields) == {
        "extra",
        "made_of",
    }, "Request validation and domain `Correspondence` model fields differ"
    assert not request_fields.difference(
        domain_fields
    ), "Request validation and domain `Correspondence` model fields differ"


def test_correspondence_domain_response_dto_same_fields():
    domain_fields = {f.name for f in fields(Correspondence)}
    response_fields = set(response.Correspondence.model_fields)
    assert domain_fields.difference(response_fields) == {
        "extra"
    }, "Response validation and domain `Correspondence` model fields differ"
    assert not response_fields.difference(
        domain_fields
    ), "Response validation and domain `Correspondence` model fields differ"


def test_correspondence_to_db_dict(cn):
    given = Correspondence.from_json_ld(cn.correspondence).to_db_dict()
    expected = dict(
        id_="http://pyst-tests.ninja/correspondence/cn2023_cn2024",
        types=["http://rdf-vocabulary.ddialliance.org/xkos#Correspondence"],
        pref_labels=[
            {"@language": "en", "@value": "Combined Nomenclature 2023 to 2024"},
        ],
        notations=[
            {
                "@type": "http://www.w3.org/1999/02/22-rdf-syntax-ns#PlainLiteral",
                "@value": "CN 2023-CN 2024",
            }
        ],
        status=[
            {
                "@id": "http://purl.org/ontology/bibo/status/accepted",
            },
        ],
        made_of=[],
        compares=[
            {"@id": "http://data.europa.eu/xsp/cn2024/cn2024"},
            {"@id": "http://data.europa.eu/xsp/cn2023/cn2023"},
        ],
        created=[
            {
                "@type": "http://www.w3.org/2001/XMLSchema#dateTime",
                "@value": "2025-01-01T12:34:56",
            },
        ],
        creators=[
            {
                "@id": "http://publications.europa.eu/resource/authority/corporate-body/ESTAT",
            },
        ],
        version=[{"@value": "1.0"}],
        extra={},
        history_notes=[],
        change_notes=[],
        definitions=[],
        editorial_notes=[],
    )
    assert given == expected, "Conversion to database dict failed"


def test_correspondence_from_json_ld(cn):
    given = Correspondence.from_json_ld(cn.correspondence)
    expected = Correspondence(
        id_="http://pyst-tests.ninja/correspondence/cn2023_cn2024",
        types=["http://rdf-vocabulary.ddialliance.org/xkos#Correspondence"],
        pref_labels=[
            {"@language": "en", "@value": "Combined Nomenclature 2023 to 2024"},
        ],
        notations=[
            {
                "@type": "http://www.w3.org/1999/02/22-rdf-syntax-ns#PlainLiteral",
                "@value": "CN 2023-CN 2024",
            }
        ],
        status=[
            {
                "@id": "http://purl.org/ontology/bibo/status/accepted",
            },
        ],
        compares=[
            {"@id": "http://data.europa.eu/xsp/cn2024/cn2024"},
            {"@id": "http://data.europa.eu/xsp/cn2023/cn2023"},
        ],
        created=[
            {
                "@type": "http://www.w3.org/2001/XMLSchema#dateTime",
                "@value": "2025-01-01T12:34:56",
            },
        ],
        creators=[
            {
                "@id": "http://publications.europa.eu/resource/authority/corporate-body/ESTAT",
            },
        ],
        version=[{"@value": "1.0"}],
    )
    assert given == expected, "Conversion from JSON-LD failed"


def test_Correspondence_to_json_ld(cn):
    given = Correspondence.from_json_ld(cn.correspondence).to_json_ld()
    assert given == cn.correspondence, "Conversion to JSON-LD failed"
