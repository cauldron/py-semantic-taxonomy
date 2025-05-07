from pydantic import BaseModel, ConfigDict, Field

from py_semantic_taxonomy.adapters.routers.doc_examples import (
    CHANGE_NOTE,
    DEFINITION,
    EDITORIAL_NOTE,
    HISTORY_NOTE,
)
from py_semantic_taxonomy.domain.constants import RDF_MAPPING as RDF
from py_semantic_taxonomy.domain.constants import RelationshipVerbs as RV


class ServerStatus(BaseModel):
    version: str
    search: bool


class ErrorMessage(BaseModel):
    message: str
    detail: dict | None = None


class KOSCommon(BaseModel):
    id_: str = Field(
        alias=RDF["id_"],
        title="Object IRI (`@id`)",
        description="https://www.w3.org/TR/json-ld/#node-identifiers",
        example="http://data.europa.eu/xsp/cn2024/010021000090",
    )
    types: list[str] = Field(
        alias=RDF["types"],
        title="Object `@type`",
        description="https://www.w3.org/TR/json-ld/#specifying-the-type",
        example=["http://www.w3.org/2004/02/skos/core#Concept"],
    )
    pref_labels: list[dict[str, str]] = Field(
        alias=RDF["pref_labels"],
        title="SKOS preferred labels (one per language)",
        description="https://www.w3.org/TR/skos-primer/#secpref",
        example=[
            {"@value": "CHAPTER 1 - LIVE ANIMALS", "@language": "en"},
            {"@value": "CAP\u00cdTULO 1 - ANIMAIS VIVOS", "@language": "pt"},
        ],
    )
    status: list[dict[str, str]] = Field(
        alias=RDF["status"],
        title="BIBO status (accepted/draft/rejected)",
        description="https://github.com/dcmi/bibo/blob/main/rdf/bibo.ttl#L391",
        example=[{"@id": "http://purl.org/ontology/bibo/status/accepted"}],
    )
    definitions: list[dict[str, str]] = Field(
        alias=RDF["definitions"],
        default=[],
        title="SKOS definition (one per language)",
        description="https://www.w3.org/TR/skos-primer/#secdocumentation",
        example=DEFINITION,
    )
    notations: list[dict[str, str]] = Field(
        alias=RDF["notations"],
        default=[],
        description="https://www.w3.org/TR/skos-primer/#secnotations",
        title="SKOS notation (typed literal)",
        example=[
            {"@value": "01", "@type": "http://www.w3.org/1999/02/22-rdf-syntax-ns#PlainLiteral"}
        ],
    )
    change_notes: list[dict] = Field(
        alias=RDF["change_notes"],
        default=[],
        definition="https://www.w3.org/TR/skos-primer/#secdocumentation",
        title="SKOS change note with additional required fields",
        example=CHANGE_NOTE,
    )
    history_notes: list[dict] = Field(
        alias=RDF["history_notes"],
        default=[],
        definition="https://www.w3.org/TR/skos-primer/#secdocumentation",
        title="SKOS history note with additional required fields",
        example=HISTORY_NOTE,
    )
    editorial_notes: list[dict] = Field(
        alias=RDF["editorial_notes"],
        default=[],
        definition="https://www.w3.org/TR/skos-primer/#secdocumentation",
        title="SKOS editorial note with additional required fields",
        example=EDITORIAL_NOTE,
    )

    model_config = ConfigDict(extra="allow")

    def model_dump(self, exclude_unset=True, by_alias=True, *args, **kwargs):
        return super().model_dump(*args, exclude_unset=exclude_unset, by_alias=by_alias, **kwargs)


class Concept(KOSCommon):
    schemes: list[dict] = Field(
        alias=RDF["schemes"],
        title="SKOS concept scheme",
        description="https://www.w3.org/TR/skos-primer/#secscheme",
        example=[{"@id": "http://data.europa.eu/xsp/cn2024/cn2024"}],
    )
    alt_labels: list[dict[str, str]] = Field(
        alias=RDF["alt_labels"],
        default=[],
        title="SKOS alternative labels. Can be more than one per language.",
        description="https://www.w3.org/TR/skos-primer/#secalt",
        examples=[
            {"@value": "Horsies, moo-moos, etc.", "@language": "en"},
        ],
    )
    hidden_labels: list[dict[str, str]] = Field(
        alias=RDF["hidden_labels"],
        default=[],
        title="SKOS hidden labels",
        description="https://www.w3.org/TR/skos-primer/#sechidden",
        example=[{"@language": "ine-pro", "@value": "ékwos"}],
    )
    top_concept_of: list[dict] = Field(
        alias=RDF["top_concept_of"],
        default=[],
        title="SKOS concept scheme if this concept is at top of hierarchy (maximum 1)",
        description="https://www.w3.org/TR/skos-primer/#secscheme",
        example=[{"@id": "http://data.europa.eu/xsp/cn2024/cn2024"}],
    )


class ConceptScheme(KOSCommon):
    created: list[dict] = Field(
        alias="http://purl.org/dc/terms/created",
        title="DCTerms created timestamp",
        description="https://www.dublincore.org/specifications/dublin-core/dcmi-terms/#http://purl.org/dc/terms/created",
        example=[
            {"@type": "http://www.w3.org/2001/XMLSchema#dateTime", "@value": "2023-10-11T13:59:56"}
        ],
    )
    creators: list[dict] = Field(
        alias="http://purl.org/dc/terms/creator",
        title="DCTerms creators list",
        description="https://www.dublincore.org/specifications/dublin-core/dcmi-terms/#http://purl.org/dc/elements/1.1/creator",
        example=[{"@id": "http://publications.europa.eu/resource/authority/corporate-body/ESTAT"}],
    )
    version: list[dict] = Field(
        alias="http://www.w3.org/2002/07/owl#versionInfo",
        title="OWL version info",
        description="https://www.w3.org/TR/owl-ref/#versionInfo-def",
        example=[{"@value": "2024"}],
    )


class Relationship(BaseModel):
    id_: str = Field(
        alias=RDF["id_"],
        title="Object IRI (`@id`)",
        description="https://www.w3.org/TR/json-ld/#node-identifiers",
        example="http://data.europa.eu/xsp/cn2024/010021000090",
    )
    broader: list[dict] = Field(
        alias=RV.broader,
        default=[],
        title="SKOS broader",
        description="https://www.w3.org/TR/skos-primer/#sechierarchy",
        example=[{"@id": "http://data.europa.eu/xsp/cn2024/010021000090"}],
    )
    narrower: list[dict] = Field(
        alias=RV.narrower,
        default=[],
        title="SKOS narrower",
        description="https://www.w3.org/TR/skos-primer/#sechierarchy",
        example=[{"@id": "http://data.europa.eu/xsp/cn2024/010100000080"}],
    )
    exact_match: list[dict] = Field(
        alias=RV.exact_match,
        default=[],
        title="SKOS exact match",
        description="https://www.w3.org/TR/skos-primer/#secassociative",
        example=[{"@id": "http://data.europa.eu/xsp/cn2023/010100000080"}],
    )
    close_match: list[dict] = Field(
        alias=RV.close_match,
        default=[],
        title="SKOS close match",
        description="https://www.w3.org/TR/skos-primer/#secassociative",
        example=[{"@id": "http://data.europa.eu/xsp/cn2023/010100000080"}],
    )
    broad_match: list[dict] = Field(
        alias=RV.broad_match,
        default=[],
        title="SKOS broad match",
        description="https://www.w3.org/TR/skos-primer/#secassociative",
        example=[{"@id": "http://data.europa.eu/xsp/cn2023/010021000090"}],
    )
    narrow_match: list[dict] = Field(
        alias=RV.narrow_match,
        default=[],
        title="SKOS narrow match",
        description="https://www.w3.org/TR/skos-primer/#secassociative",
        example=[{"@id": "http://data.europa.eu/xsp/cn2023/010100000080"}],
    )
    related_match: list[dict] = Field(
        alias=RV.related_match,
        default=[],
        title="SKOS related match",
        description="https://www.w3.org/TR/skos-primer/#secassociative",
        example=[{"@id": "https://www.wikidata.org/wiki/Q726"}],
    )

    model_config = ConfigDict(extra="forbid")

    def model_dump(self, exclude_unset=True, by_alias=True, *args, **kwargs):
        return super().model_dump(*args, exclude_unset=exclude_unset, by_alias=by_alias, **kwargs)


class Correspondence(ConceptScheme):
    compares: list[dict] = Field(
        alias=RDF["compares"],
        title="List of `ConceptScheme` objects being compared",
        description="https://rdf-vocabulary.ddialliance.org/xkos.html#correspondences",
        example=[
            {"@id": "http://data.europa.eu/xsp/cn2023/cn2023"},
            {"@id": "http://data.europa.eu/xsp/cn2024/cn2024"},
        ],
    )
    made_ofs: list[dict] = Field(
        alias=RDF["made_ofs"],
        default=[],
        title="SKOS definition (one per language)",
        description="https://www.w3.org/TR/skos-primer/#secdocumentation",
        example=DEFINITION,
    )


class Association(BaseModel):
    id_: str = Field(
        alias=RDF["id_"],
        title="Object IRI (`@id`)",
        description="https://www.w3.org/TR/json-ld/#node-identifiers",
        example="http://data.europa.eu/xsp/cn2024/010021000090",
    )
    types: list[str] = Field(
        alias=RDF["types"],
        title="Object `@type`",
        description="https://www.w3.org/TR/json-ld/#specifying-the-type",
        example=["http://rdf-vocabulary.ddialliance.org/xkos#ConceptAssociation"],
    )
    source_concepts: list[dict] = Field(
        alias=RDF["source_concepts"],
        title="List of source `Concept` objects",
        description="https://rdf-vocabulary.ddialliance.org/xkos.html#correspondences",
        example=[{"@id": "http://data.europa.eu/xsp/cn2023/010011000090"}],
    )
    target_concepts: list[dict] = Field(
        alias=RDF["target_concepts"],
        title="List of target `Concept` objects",
        description="https://rdf-vocabulary.ddialliance.org/xkos.html#correspondences",
        example=[{"@id": "http://data.europa.eu/xsp/cn2024/010011000090"}],
    )

    model_config = ConfigDict(extra="allow")
