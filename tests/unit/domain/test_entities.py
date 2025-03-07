from dataclasses import fields

from py_semantic_taxonomy.adapters.routers import request_dto as request
from py_semantic_taxonomy.adapters.routers import response_dto as response
from py_semantic_taxonomy.domain.entities import CONCEPT_EXCLUDED, Concept


def test_concept_domain_request_dto_same_fields():
    domain_fields = {f.name for f in fields(Concept)}
    request_fields = set(request.Concept.model_fields)
    assert domain_fields.difference(request_fields) == {
        "extra"
    }, "Request validation and domain `Concept` model fields differ"
    assert request_fields.difference(domain_fields) == {
        "broader",
        "narrower",
    }, "Request validation and domain `Concept` model fields differ"


def test_concept_domain_response_dto_same_fields():
    domain_fields = {f.name for f in fields(Concept)}
    response_fields = set(response.Concept.model_fields)
    assert domain_fields.difference(response_fields) == {
        "extra"
    }, "Response validation and domain `Concept` model fields differ"
    assert not response_fields.difference(
        domain_fields
    ), "Response validation and domain `Concept` model fields differ"


def test_concept_to_db_dict(cn):
    given = Concept.from_json_ld(cn.concept_top).to_db_dict()
    expected = dict(
        id_="http://data.europa.eu/xsp/cn2024/010011000090",
        types=["http://www.w3.org/2004/02/skos/core#Concept"],
        pref_labels=[
            {"@language": "en", "@value": "SECTION I - LIVE ANIMALS; ANIMAL PRODUCTS"},
            {
                "@language": "pt",
                "@value": "SECÇÃO I - ANIMAIS VIVOS E PRODUTOS DO REINO ANIMAL",
            },
        ],
        schemes=[{"@id": "http://data.europa.eu/xsp/cn2024/cn2024"}],
        notations=[
            {"@type": "http://www.w3.org/1999/02/22-rdf-syntax-ns#PlainLiteral", "@value": "I"}
        ],
        extra={
            "http://purl.org/dc/elements/1.1/identifier": [{"@value": "010011000090"}],
            "http://rdf-vocabulary.ddialliance.org/xkos#depth": [
                {"@type": "http://www.w3.org/2001/XMLSchema#positiveInteger", "@value": "1"}
            ],
            "http://purl.org/dc/terms/modified": [
                {
                    "@type": "http://www.w3.org/2001/XMLSchema#dateTime",
                    "@value": "2023-10-11T14:43:01",
                }
            ],
            "http://www.w3.org/2004/02/skos/core#scopeNote": [
                {"@language": "en", "@value": "LIVE ANIMALS; ANIMAL PRODUCTS"}
            ],
        },
        hidden_labels=[],
        history_notes=[],
        alt_labels=[],
        change_notes=[],
        definitions=[],
        editorial_notes=[],
    )
    assert given == expected, "Conversion to database dict failed"


def test_concept_from_json_ld(cn):
    given = Concept.from_json_ld(cn.concept_top)
    expected = Concept(
        id_="http://data.europa.eu/xsp/cn2024/010011000090",
        types=["http://www.w3.org/2004/02/skos/core#Concept"],
        pref_labels=[
            {"@language": "en", "@value": "SECTION I - LIVE ANIMALS; ANIMAL PRODUCTS"},
            {
                "@language": "pt",
                "@value": "SECÇÃO I - ANIMAIS VIVOS E PRODUTOS DO REINO ANIMAL",
            },
        ],
        schemes=[{"@id": "http://data.europa.eu/xsp/cn2024/cn2024"}],
        notations=[
            {"@type": "http://www.w3.org/1999/02/22-rdf-syntax-ns#PlainLiteral", "@value": "I"}
        ],
        extra={
            "http://purl.org/dc/elements/1.1/identifier": [{"@value": "010011000090"}],
            "http://rdf-vocabulary.ddialliance.org/xkos#depth": [
                {"@type": "http://www.w3.org/2001/XMLSchema#positiveInteger", "@value": "1"}
            ],
            "http://purl.org/dc/terms/modified": [
                {
                    "@type": "http://www.w3.org/2001/XMLSchema#dateTime",
                    "@value": "2023-10-11T14:43:01",
                }
            ],
            "http://www.w3.org/2004/02/skos/core#scopeNote": [
                {"@language": "en", "@value": "LIVE ANIMALS; ANIMAL PRODUCTS"}
            ],
        },
    )
    assert given == expected, "Conversion from JSON-LD failed"


def test_concept_to_json_ld(cn):
    expected = {key: value for key, value in cn.concept_top.items() if key not in CONCEPT_EXCLUDED}
    given = Concept.from_json_ld(cn.concept_top).to_json_ld()
    assert given == expected, "Conversion to JSON-LD failed"
