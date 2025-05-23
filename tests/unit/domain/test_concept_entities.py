from dataclasses import fields

from py_semantic_taxonomy.adapters.routers import request_dto as request
from py_semantic_taxonomy.adapters.routers import response_dto as response
from py_semantic_taxonomy.domain.constants import RDF_MAPPING as RDF
from py_semantic_taxonomy.domain.constants import SKOS_RELATIONSHIP_PREDICATES, RelationshipVerbs
from py_semantic_taxonomy.domain.entities import Concept


def test_concept_domain_request_dto_same_fields():
    domain_fields = {f.name for f in fields(Concept)}
    request_fields = set(request.Concept.model_fields)
    assert domain_fields.difference(request_fields) == {
        "extra"
    }, "Request validation and domain `Concept` model fields differ"
    assert not request_fields.difference(
        domain_fields
    ), "Request validation and domain `Concept` model fields differ"


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
        top_concept_of=[
            {
                "@id": "http://data.europa.eu/xsp/cn2024/cn2024",
            },
        ],
        notations=[
            {"@type": "http://www.w3.org/1999/02/22-rdf-syntax-ns#PlainLiteral", "@value": "I"}
        ],
        status=[
            {
                "@id": "http://purl.org/ontology/bibo/status/accepted",
            },
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


def test_concept_filter_language(cn):
    original = Concept.from_json_ld(cn.concept_top)
    original.definitions = [
        {"@language": "en", "@value": "foo"},
        {"@language": "pt", "@value": "bar"},
    ]
    original.hidden_labels = [
        {"@language": "en", "@value": "a"},
        {"@language": "pt", "@value": "b"},
    ]
    original.alt_labels = [
        {"@language": "en", "@value": "1"},
        {"@language": "pt", "@value": "2"},
    ]
    result = original.filter_language("en")
    SAME_FIELDS = (
        "change_notes",
        "editorial_notes",
        "extra",
        "history_notes",
        "id_",
        "notations",
        "schemes",
        "status",
        "top_concept_of",
        "types",
    )
    for field in SAME_FIELDS:
        assert getattr(original, field) == getattr(result, field), "Value should be the same"
    assert result.pref_labels == [
        {"@language": "en", "@value": "SECTION I - LIVE ANIMALS; ANIMAL PRODUCTS"},
    ], "Wrong value on language selection"
    assert result.definitions == [
        {"@language": "en", "@value": "foo"},
    ], "Wrong value on language selection"
    assert result.hidden_labels == [
        {"@language": "en", "@value": "a"},
    ], "Wrong value on language selection"
    assert result.alt_labels == [
        {"@language": "en", "@value": "1"},
    ], "Wrong value on language selection"


def test_concept_to_search_dict(cn):
    cn.concept_top[RDF["alt_labels"]] = [
        {"@language": "pt", "@value": "foo"},
        {"@language": "pt", "@value": "bar"},
    ]
    cn.concept_top[RDF["pref_labels"]] = [
        {
            "@language": "pt",
            "@value": "SECÇÃO I - ANIMAIS VIVOS",
        },
        {"@language": "en", "@value": "SECTION I - LIVE ANIMALS; ANIMAL PRODUCTS"},
        {"@language": "PT-FOO", "@value": "E PRODUTOS DO REINO ANIMAL"},
    ]
    cn.concept_top[RDF["hidden_labels"]] = [{"@language": "jp", "@value": "ふー"}]
    given = Concept.from_json_ld(cn.concept_top).to_search_dict("pt")
    expected = {
        "id": "iMEtIMBiU8E",
        "url": "http%3A%2F%2Fdata.europa.eu%2Fxsp%2Fcn2024%2F010011000090",
        "alt_labels": ["foo", "bar"],
        "hidden_labels": [],
        "pref_label": "SECÇÃO I - ANIMAIS VIVOS E PRODUTOS DO REINO ANIMAL",
        "definition": "",
        "notation": "I",
        "all_languages_pref_labels": [
            "SECÇÃO I - ANIMAIS VIVOS",
            "SECTION I - LIVE ANIMALS; ANIMAL PRODUCTS",
            "E PRODUTOS DO REINO ANIMAL",
        ],
    }
    assert given == expected, "Conversion to search dict failed"


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
        top_concept_of=[
            {
                "@id": "http://data.europa.eu/xsp/cn2024/cn2024",
            },
        ],
        status=[
            {
                "@id": "http://purl.org/ontology/bibo/status/accepted",
            },
        ],
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


def test_concept_from_json_ld_exlude_relationship_predicates(cn):
    obj = cn.concept_top
    obj[RelationshipVerbs.narrower.value] = [{"@id": "http://example.com/foo"}]
    obj[RelationshipVerbs.exact_match.value] = [{"@id": "http://example.com/foo"}]

    given = Concept.from_json_ld(obj)
    for key in given.extra:
        assert key not in RelationshipVerbs, "Relationship in `extra` section"


def test_concept_to_json_ld(cn):
    expected = {
        key: value
        for key, value in cn.concept_top.items()
        if key not in SKOS_RELATIONSHIP_PREDICATES
    }
    given = Concept.from_json_ld(cn.concept_top).to_json_ld()
    assert given == expected, "Conversion to JSON-LD failed"
