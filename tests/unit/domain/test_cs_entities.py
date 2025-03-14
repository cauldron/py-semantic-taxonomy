from dataclasses import fields

from py_semantic_taxonomy.adapters.routers import request_dto as request
from py_semantic_taxonomy.adapters.routers import response_dto as response
from py_semantic_taxonomy.domain.constants import SKOS_RELATIONSHIP_PREDICATES
from py_semantic_taxonomy.domain.entities import ConceptScheme

CS_DEFINITION = "The main classification for the European ITGS (International trade in goods statistics)  is the Combined Nomenclature (CN). This is the primary nomenclature as it is the one used by the EU Member States to collect detailed data on their trading of goods since 1988. Before the introduction of the CN, ITGS were based on a product classification called NIMEXE.  The CN is based on the Harmonised Commodity Description and Coding System (managed by the World Customs Organisation (WCO). The Harmonised System (HS) is an international classification at two, four and six-digit level which classifies goods according to their nature. It was introduced in 1988 and, since then, was revised six times: in 1996, 2002, 2007, 2012, 2017 and 2022. The CN corresponds to the HS plus a further breakdown at eight-digit level defined to meet EU needs. The CN is revised annually and, as a Council Regulation, is binding on the Member States."


def test_concept_scheme_domain_request_dto_same_fields():
    domain_fields = {f.name for f in fields(ConceptScheme)}
    request_fields = set(request.ConceptScheme.model_fields)
    assert domain_fields.difference(request_fields) == {
        "extra"
    }, "Request validation and domain `ConceptScheme` model fields differ"
    assert not request_fields.difference(
        domain_fields
    ), "Request validation and domain `ConceptScheme` model fields differ"


def test_concept_scheme_domain_response_dto_same_fields():
    domain_fields = {f.name for f in fields(ConceptScheme)}
    response_fields = set(response.ConceptScheme.model_fields)
    assert domain_fields.difference(response_fields) == {
        "extra"
    }, "Response validation and domain `ConceptScheme` model fields differ"
    assert not response_fields.difference(
        domain_fields
    ), "Response validation and domain `ConceptScheme` model fields differ"


def test_concept_scheme_to_db_dict(cn):
    given = ConceptScheme.from_json_ld(cn.scheme).to_db_dict()
    expected = dict(
        id_="http://data.europa.eu/xsp/cn2024/cn2024",
        types=["http://www.w3.org/2004/02/skos/core#ConceptScheme"],
        pref_labels=[
            {"@language": "en", "@value": "Combined Nomenclature, 2024 (CN 2024)"},
            {
                "@language": "pt",
                "@value": "Nomenclatura Combinada, 2024 (NC 2024)",
            },
        ],
        notations=[
            {
                "@type": "http://www.w3.org/1999/02/22-rdf-syntax-ns#PlainLiteral",
                "@value": "CN 2024",
            }
        ],
        created=[
            {
                "@type": "http://www.w3.org/2001/XMLSchema#dateTime",
                "@value": "2023-10-11T13:59:56",
            },
        ],
        creators=[
            {"@id": "http://publications.europa.eu/resource/authority/corporate-body/ESTAT"},
            {"@id": "http://publications.europa.eu/resource/authority/corporate-body/TAXUD"},
        ],
        version=[{"@value": "2024"}],
        status=[
            {
                "@id": "http://purl.org/ontology/bibo/status/accepted",
            },
        ],
        extra={
            "http://data.europa.eu/eli/ontology#based_on": [
                {"@id": "http://data.europa.eu/eli/reg_impl/2023/2364/oj"}
            ],
            "http://data.europa.eu/eli/ontology#version_date": [
                {"@type": "http://www.w3.org/2001/XMLSchema#date", "@value": "2023-11-20"}
            ],
            "http://purl.org/dc/terms/identifier": [
                {"@value": "http://data.europa.eu/xsp/cn2024/cn2024"}
            ],
            "http://purl.org/dc/terms/language": [
                {"@id": "http://publications.europa.eu/resource/authority/language/ENG"},
                {"@id": "http://publications.europa.eu/resource/authority/language/POR"},
            ],
            "http://purl.org/dc/terms/modified": [
                {
                    "@type": "http://www.w3.org/2001/XMLSchema#dateTime",
                    "@value": "2024-07-24T09:37:40",
                }
            ],
            "http://rdf-vocabulary.ddialliance.org/xkos#belongsTo": [
                {"@id": "http://data.europa.eu/2en/class-series/cn"}
            ],
            "http://rdf-vocabulary.ddialliance.org/xkos#follows": [
                {"@id": "http://data.europa.eu/xsp/cn2023/cn2023"}
            ],
            "http://rdf-vocabulary.ddialliance.org/xkos#numberOfLevels": [
                {"@type": "http://www.w3.org/2001/XMLSchema#positiveInteger", "@value": "5"}
            ],
            "http://schema.org/endDate": [
                {"@type": "http://www.w3.org/2001/XMLSchema#date", "@value": "2024-12-31"}
            ],
            "http://schema.org/startDate": [
                {"@type": "http://www.w3.org/2001/XMLSchema#date", "@value": "2024-01-01"}
            ],
            "http://www.w3.org/2004/02/skos/core#scopeNote": [
                {
                    "@type": "http://www.w3.org/2001/XMLSchema#anyURI",
                    "@value": "http://publications.europa.eu/resource/oj/JOC_2019_119_R_0001",
                }
            ],
        },
        history_notes=[],
        change_notes=[],
        definitions=[{"@language": "en", "@value": CS_DEFINITION}],
        editorial_notes=[],
    )
    assert given == expected, "Conversion to database dict failed"


def test_concept_scheme_from_json_ld(cn):
    given = ConceptScheme.from_json_ld(cn.scheme)
    expected = ConceptScheme(
        id_="http://data.europa.eu/xsp/cn2024/cn2024",
        types=["http://www.w3.org/2004/02/skos/core#ConceptScheme"],
        pref_labels=[
            {"@language": "en", "@value": "Combined Nomenclature, 2024 (CN 2024)"},
            {
                "@language": "pt",
                "@value": "Nomenclatura Combinada, 2024 (NC 2024)",
            },
        ],
        notations=[
            {
                "@type": "http://www.w3.org/1999/02/22-rdf-syntax-ns#PlainLiteral",
                "@value": "CN 2024",
            }
        ],
        created=[
            {
                "@type": "http://www.w3.org/2001/XMLSchema#dateTime",
                "@value": "2023-10-11T13:59:56",
            },
        ],
        creators=[
            {"@id": "http://publications.europa.eu/resource/authority/corporate-body/ESTAT"},
            {"@id": "http://publications.europa.eu/resource/authority/corporate-body/TAXUD"},
        ],
        version=[{"@value": "2024"}],
        status=[
            {
                "@id": "http://purl.org/ontology/bibo/status/accepted",
            },
        ],
        extra={
            "http://data.europa.eu/eli/ontology#based_on": [
                {"@id": "http://data.europa.eu/eli/reg_impl/2023/2364/oj"}
            ],
            "http://data.europa.eu/eli/ontology#version_date": [
                {"@type": "http://www.w3.org/2001/XMLSchema#date", "@value": "2023-11-20"}
            ],
            "http://purl.org/dc/terms/identifier": [
                {"@value": "http://data.europa.eu/xsp/cn2024/cn2024"}
            ],
            "http://purl.org/dc/terms/language": [
                {"@id": "http://publications.europa.eu/resource/authority/language/ENG"},
                {"@id": "http://publications.europa.eu/resource/authority/language/POR"},
            ],
            "http://purl.org/dc/terms/modified": [
                {
                    "@type": "http://www.w3.org/2001/XMLSchema#dateTime",
                    "@value": "2024-07-24T09:37:40",
                }
            ],
            "http://rdf-vocabulary.ddialliance.org/xkos#belongsTo": [
                {"@id": "http://data.europa.eu/2en/class-series/cn"}
            ],
            "http://rdf-vocabulary.ddialliance.org/xkos#follows": [
                {"@id": "http://data.europa.eu/xsp/cn2023/cn2023"}
            ],
            "http://rdf-vocabulary.ddialliance.org/xkos#numberOfLevels": [
                {"@type": "http://www.w3.org/2001/XMLSchema#positiveInteger", "@value": "5"}
            ],
            "http://schema.org/endDate": [
                {"@type": "http://www.w3.org/2001/XMLSchema#date", "@value": "2024-12-31"}
            ],
            "http://schema.org/startDate": [
                {"@type": "http://www.w3.org/2001/XMLSchema#date", "@value": "2024-01-01"}
            ],
            "http://www.w3.org/2004/02/skos/core#scopeNote": [
                {
                    "@type": "http://www.w3.org/2001/XMLSchema#anyURI",
                    "@value": "http://publications.europa.eu/resource/oj/JOC_2019_119_R_0001",
                }
            ],
        },
        history_notes=[],
        change_notes=[],
        definitions=[{"@language": "en", "@value": CS_DEFINITION}],
        editorial_notes=[],
    )
    assert given == expected, "Conversion from JSON-LD failed"


def test_concept_scheme_to_json_ld(cn):
    expected = {
        key: value for key, value in cn.scheme.items() if key not in SKOS_RELATIONSHIP_PREDICATES
    }
    given = ConceptScheme.from_json_ld(cn.scheme).to_json_ld()
    assert given == expected, "Conversion to JSON-LD failed"
