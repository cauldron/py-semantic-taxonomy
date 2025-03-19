from typing import Self

from pydantic import BaseModel, ConfigDict, Field, conlist, field_validator, model_validator

from py_semantic_taxonomy.adapters.routers.doc_examples import (
    CHANGE_NOTE,
    DEFINITION,
    EDITORIAL_NOTE,
    HISTORY_NOTE,
)
from py_semantic_taxonomy.adapters.routers.validation import (
    IRI,
    DateTime,
    MultilingualString,
    Node,
    NonLiteralNote,
    Notation,
    Status,
    VersionString,
    one_per_language,
)
from py_semantic_taxonomy.domain.constants import RDF_MAPPING as RDF
from py_semantic_taxonomy.domain.constants import (
    SKOS,
    SKOS_RELATIONSHIP_PREDICATES,
    XKOS,
)
from py_semantic_taxonomy.domain.constants import RelationshipVerbs as RV


class KOSCommon(BaseModel):
    id_: IRI = Field(
        alias=RDF["id_"],
        title="Object IRI (`@id`)",
        description="https://www.w3.org/TR/json-ld/#node-identifiers",
        example="http://data.europa.eu/xsp/cn2024/010021000090",
    )
    types: conlist(item_type=IRI) = Field(
        alias=RDF["types"],
        title="Object `@type`",
        description="https://www.w3.org/TR/json-ld/#specifying-the-type",
        example=["http://www.w3.org/2004/02/skos/core#Concept"],
    )
    pref_labels: conlist(MultilingualString, min_length=1) = Field(
        alias=RDF["pref_labels"],
        title="SKOS preferred labels (one per language)",
        description="https://www.w3.org/TR/skos-primer/#secpref",
        example=[
            {"@value": "CHAPTER 1 - LIVE ANIMALS", "@language": "en"},
            {"@value": "CAP\u00cdTULO 1 - ANIMAIS VIVOS", "@language": "pt"},
        ],
    )
    status: conlist(Status, min_length=1) = Field(
        alias=RDF["status"],
        title="BIBO status (accepted/draft/rejected)",
        description="https://github.com/dcmi/bibo/blob/main/rdf/bibo.ttl#L391",
        example=[{"@id": "http://purl.org/ontology/bibo/status/accepted"}],
    )
    notations: list[Notation] = Field(
        alias=RDF["notations"],
        default=[],
        description="https://www.w3.org/TR/skos-primer/#secnotations",
        title="SKOS notation (typed literal)",
        example=[
            {"@value": "01", "@type": "http://www.w3.org/1999/02/22-rdf-syntax-ns#PlainLiteral"}
        ],
    )
    change_notes: list[NonLiteralNote] = Field(
        alias=RDF["change_notes"],
        default=[],
        definition="https://www.w3.org/TR/skos-primer/#secdocumentation",
        title="SKOS change note with additional required fields",
        example=CHANGE_NOTE,
    )
    history_notes: list[NonLiteralNote] = Field(
        alias=RDF["history_notes"],
        default=[],
        definition="https://www.w3.org/TR/skos-primer/#secdocumentation",
        title="SKOS history note with additional required fields",
        example=HISTORY_NOTE,
    )
    editorial_notes: list[NonLiteralNote] = Field(
        alias=RDF["editorial_notes"],
        default=[],
        definition="https://www.w3.org/TR/skos-primer/#secdocumentation",
        title="SKOS editorial note with additional required fields",
        example=EDITORIAL_NOTE,
    )

    model_config = ConfigDict(extra="allow")

    def model_dump(self, exclude_unset=True, by_alias=True, *args, **kwargs):
        return super().model_dump(*args, exclude_unset=exclude_unset, by_alias=by_alias, **kwargs)

    @field_validator("pref_labels", mode="after")
    @classmethod
    def pref_labels_one_per_language(
        cls, value: list[MultilingualString]
    ) -> list[MultilingualString]:
        return one_per_language(value, "prefLabel")


class Concept(KOSCommon):
    """Validation class for SKOS Concepts.

    Checks that required fields are included and have correct type."""

    schemes: conlist(Node, min_length=1) = Field(
        alias=RDF["schemes"],
        title="SKOS concept scheme (normally only one)",
        description="https://www.w3.org/TR/skos-primer/#secscheme",
        example=[{"@id": "http://data.europa.eu/xsp/cn2024/cn2024"}],
    )
    # Can have multiple alternative labels per language, and multiple languages
    alt_labels: list[MultilingualString] = Field(
        alias=RDF["alt_labels"],
        default=[],
        title="SKOS alternative labels. Can be more than one per language.",
        description="https://www.w3.org/TR/skos-primer/#secalt",
        example=[
            {"@value": "Horsies, moo-moos, etc.", "@language": "en"},
        ],
    )
    # Can have multiple hidden labels per language, and multiple languages
    hidden_labels: list[MultilingualString] = Field(
        alias=RDF["hidden_labels"],
        default=[],
        title="SKOS hidden labels",
        description="https://www.w3.org/TR/skos-primer/#sechidden",
        example=[{"@language": "ine-pro", "@value": "ékwos"}],
    )
    # One definition per language, at least one definition
    definitions: list[MultilingualString] = Field(
        alias=RDF["definitions"],
        default=[],
        title="SKOS definition (one per language)",
        description="https://www.w3.org/TR/skos-primer/#secdocumentation",
        example=DEFINITION,
    )
    top_concept_of: conlist(Node, max_length=1) = Field(
        alias=RDF["top_concept_of"],
        default=[],
        title="SKOS concept scheme if this concept is at top of hierarchy (maximum 1)",
        description="https://www.w3.org/TR/skos-primer/#secscheme",
        example=[{"@id": "http://data.europa.eu/xsp/cn2024/cn2024"}],
    )

    @field_validator("types", mode="after")
    @classmethod
    def type_includes_concept(cls, value: list[str]) -> list[str]:
        CONCEPT = f"{SKOS}Concept"
        if CONCEPT not in value:
            raise ValueError(f"`@type` values must include `{CONCEPT}`")
        return value

    @field_validator("definitions", mode="after")
    @classmethod
    def definition_one_per_language(
        cls, value: list[MultilingualString]
    ) -> list[MultilingualString]:
        return one_per_language(value, "definition")

    @model_validator(mode="after")
    def notations_disjoint_pref_label(self) -> Self:
        if overlap := {obj.value for obj in self.pref_labels}.intersection(
            {obj.value for obj in self.notations}
        ):
            raise ValueError(f"Found overlapping values in `prefLabel` and `notation`: {overlap}")
        return self


class ConceptCreate(Concept):
    broader: list[Node] = Field(
        alias=str(RV.broader),
        default=[],
        title="SKOS broader",
        description="https://www.w3.org/TR/skos-primer/#sechierarchy",
        example=[{"@id": "http://data.europa.eu/xsp/cn2024/010021000090"}],
    )
    narrower: list[Node] = Field(
        alias=str(RV.narrower),
        default=[],
        title="SKOS narrower (use of `broader` is preferred; see docs)",
        description="https://www.w3.org/TR/skos-primer/#sechierarchy",
        example=[{"@id": "http://data.europa.eu/xsp/cn2024/010100000080"}],
    )

    @model_validator(mode="after")
    def hierarchy_doesnt_reference_self(self) -> Self:
        for node in self.broader:
            if node.id_ == self.id_:
                raise ValueError("Concept can't have `broader` relationship to itself")
        for node in self.narrower:
            if node.id_ == self.id_:
                raise ValueError("Concept can't have `narrower` relationship to itself")
        return self

    @model_validator(mode="before")
    @classmethod
    def check_no_transitive_relationships(cls, data: dict) -> dict:
        for key in data:
            if key in {f"{SKOS}broaderTransitive", f"{SKOS}narrowerTransitive"}:
                short = key[len(SKOS) :]
                raise ValueError(
                    f"Found `{short}` in new concept; transitive relationships are implied and should be omitted."
                )
        return data


class ConceptUpdate(Concept):
    @model_validator(mode="before")
    @classmethod
    def check_no_graph_relationships(cls, data: dict) -> dict:
        for key in data:
            if key in SKOS_RELATIONSHIP_PREDICATES:
                short = key[len(SKOS) :]
                raise ValueError(
                    f"Found `{short}` in concept update; Use specific API calls to update graph structure."
                )
        return data


class ConceptSchemeCommon(KOSCommon):
    created: conlist(DateTime, min_length=1, max_length=1) = Field(
        alias="http://purl.org/dc/terms/created",
        title="DCTerms created timestamp",
        description="https://www.dublincore.org/specifications/dublin-core/dcmi-terms/#http://purl.org/dc/terms/created",
        example=[
            {"@type": "http://www.w3.org/2001/XMLSchema#dateTime", "@value": "2023-10-11T13:59:56"}
        ],
    )
    creators: list[Node] = Field(
        alias="http://purl.org/dc/terms/creator",
        title="DCTerms creators list",
        description="https://www.dublincore.org/specifications/dublin-core/dcmi-terms/#http://purl.org/dc/elements/1.1/creator",
        example=[{"@id": "http://publications.europa.eu/resource/authority/corporate-body/ESTAT"}],
    )
    version: conlist(VersionString, min_length=1, max_length=1) = Field(
        alias="http://www.w3.org/2002/07/owl#versionInfo",
        title="OWL version info",
        description="https://www.w3.org/TR/owl-ref/#versionInfo-def",
        example=[{"@value": "2024"}],
    )


class ConceptScheme(ConceptSchemeCommon):
    """Validation class for SKOS Concept Schemes.

    Checks that required fields are included and have correct type."""

    definitions: conlist(MultilingualString, min_length=1) = Field(
        alias=RDF["definitions"],
        title="SKOS definition (one per language)",
        description="https://www.w3.org/TR/skos-primer/#secdocumentation",
        example=DEFINITION,
    )

    @field_validator("types", mode="after")
    @classmethod
    def type_includes_concept_scheme(cls, value: list[str]) -> list[str]:
        SCHEME = f"{SKOS}ConceptScheme"
        if SCHEME not in value:
            raise ValueError(f"`@type` must include `{SCHEME}`")
        return value

    @model_validator(mode="before")
    @classmethod
    def check_no_top_concept(cls, data: dict) -> dict:
        """skos:hasTopConcept has range skos:Concept, which we don't want. Create links later."""
        if f"{SKOS}hasTopConcept" in data:
            raise ValueError(
                f"Found `hasTopConcept` in concept scheme; Specify `topConceptOf` of constituent concepts instead."
            )
        return data

    @field_validator("definitions", mode="after")
    @classmethod
    def definition_one_per_language(
        cls, value: list[MultilingualString]
    ) -> list[MultilingualString]:
        return one_per_language(value, "definition")


class Relationship(BaseModel):
    id_: IRI = Field(
        alias=RDF["id_"],
        title="Object IRI (`@id`)",
        description="https://www.w3.org/TR/json-ld/#node-identifiers",
        example="http://data.europa.eu/xsp/cn2024/010021000090",
    )
    broader: list[Node] = Field(
        alias=str(RV.broader),
        default=[],
        title="SKOS broader",
        description="https://www.w3.org/TR/skos-primer/#sechierarchy",
        example=[{"@id": "http://data.europa.eu/xsp/cn2024/010021000090"}],
    )
    narrower: list[Node] = Field(
        alias=str(RV.narrower),
        default=[],
        title="SKOS narrower (use of `broader` is preferred; see docs)",
        description="https://www.w3.org/TR/skos-primer/#sechierarchy",
        example=[{"@id": "http://data.europa.eu/xsp/cn2024/010100000080"}],
    )
    exact_match: list[Node] = Field(
        alias=str(RV.exact_match),
        default=[],
        title="SKOS exact match",
        description="https://www.w3.org/TR/skos-primer/#secassociative",
        example=[{"@id": "http://data.europa.eu/xsp/cn2023/010100000080"}],
    )
    close_match: list[Node] = Field(
        alias=str(RV.close_match),
        default=[],
        title="SKOS close match",
        description="https://www.w3.org/TR/skos-primer/#secassociative",
        example=[{"@id": "http://data.europa.eu/xsp/cn2023/010100000080"}],
    )
    broad_match: list[Node] = Field(
        alias=str(RV.broad_match),
        default=[],
        title="SKOS broad match",
        description="https://www.w3.org/TR/skos-primer/#secassociative",
        example=[{"@id": "http://data.europa.eu/xsp/cn2023/010021000090"}],
    )
    narrow_match: list[Node] = Field(
        alias=str(RV.narrow_match),
        default=[],
        title="SKOS narrow match",
        description="https://www.w3.org/TR/skos-primer/#secassociative",
        example=[{"@id": "http://data.europa.eu/xsp/cn2023/010100000080"}],
    )
    related_match: list[Node] = Field(
        alias=str(RV.related_match),
        default=[],
        title="SKOS related match",
        description="https://www.w3.org/TR/skos-primer/#secassociative",
        example=[{"@id": "https://www.wikidata.org/wiki/Q726"}],
    )

    _RELATIONSHIP_FIELDS = (
        "broader",
        "narrower",
        "exact_match",
        "close_match",
        "broad_match",
        "narrow_match",
        "related_match",
    )

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    def model_dump(self, exclude_unset=True, by_alias=True, *args, **kwargs):
        return super().model_dump(*args, exclude_unset=exclude_unset, by_alias=by_alias, **kwargs)

    @model_validator(mode="after")
    def no_self_references(self) -> Self:
        for field in self._RELATIONSHIP_FIELDS:
            for obj in getattr(self, field, []):
                if obj.id_ == self.id_:
                    raise ValueError("Relationship has same source and target")

        return self

    @model_validator(mode="after")
    def two_relationships_of_same_type(self) -> Self:
        for field in self._RELATIONSHIP_FIELDS:
            if len(getattr(self, field, [])) > 1:
                raise ValueError(f"Found multiple relationships of type `{field}`")
        return self

    @model_validator(mode="after")
    def exactly_one_relationship_type(self) -> Self:
        truthy = sorted({field for field in self._RELATIONSHIP_FIELDS if getattr(self, field)})

        if len(truthy) > 1:
            raise ValueError(f"Found multiple relationships {truthy} where only one is allowed")
        elif not truthy:
            raise ValueError(f"Found zero relationships")

        return self


class Correspondence(ConceptSchemeCommon):
    definitions: list[MultilingualString] = Field(
        alias=RDF["definitions"],
        default=[],
        title="SKOS definition (one per language)",
        description="https://www.w3.org/TR/skos-primer/#secdocumentation",
        example=DEFINITION,
    )
    compares: conlist(Node, min_length=1) = Field(
        alias=f"{XKOS}compares",
        title="List of `ConceptScheme` objects being compared",
        description="https://rdf-vocabulary.ddialliance.org/xkos.html#correspondences",
        example=[
            {"@id": "http://data.europa.eu/xsp/cn2023/cn2023"},
            {"@id": "http://data.europa.eu/xsp/cn2024/cn2024"},
        ],
    )

    @field_validator("types", mode="after")
    @classmethod
    def type_includes_correspondence(cls, value: list[str]) -> list[str]:
        CONCEPT = f"{XKOS}Correspondence"
        if CONCEPT not in value:
            raise ValueError(f"`@type` values must include `{CONCEPT}`")
        return value

    @field_validator("definitions", mode="after")
    @classmethod
    def definition_one_per_language(
        cls, value: list[MultilingualString]
    ) -> list[MultilingualString]:
        return one_per_language(value, "definition")

    @model_validator(mode="before")
    @classmethod
    def check_no_made_of(cls, data: dict) -> dict:
        for key in data:
            if key == RDF["made_ofs"]:
                raise ValueError(
                    f"Found `{RDF['made_ofs']}` in new correspondence; use dedicated API calls for this data."
                )
        return data


class MadeOf(BaseModel):
    id_: IRI = Field(
        alias=RDF["id_"],
        title="Object IRI (`@id`)",
        description="https://www.w3.org/TR/json-ld/#node-identifiers",
        example="http://data.europa.eu/xsp/cn2024/010021000090",
    )
    made_ofs: list[Node] = Field(
        alias=RDF["made_ofs"],
        title="List of `ConceptAssociation` objects in a `Correspondence`",
        description="https://rdf-vocabulary.ddialliance.org/xkos.html#correspondences",
        example="http://data.europa.eu/xsp/cn2024/010021000090",
    )

    model_config = ConfigDict(extra="forbid")

    def model_dump(self, by_alias=True, *args, **kwargs):
        return super().model_dump(*args, by_alias=by_alias, **kwargs)


class Association(BaseModel):
    id_: IRI = Field(
        alias=RDF["id_"],
        title="Object IRI (`@id`)",
        description="https://www.w3.org/TR/json-ld/#node-identifiers",
        example="http://data.europa.eu/xsp/cn2023_cn2024/something",
    )
    types: conlist(item_type=IRI) = Field(
        alias=RDF["types"],
        title="Object `@type`",
        description="https://www.w3.org/TR/json-ld/#specifying-the-type",
        example=["http://rdf-vocabulary.ddialliance.org/xkos#ConceptAssociation"],
    )
    source_concepts: conlist(Node, min_length=1) = Field(
        alias=RDF["source_concepts"],
        title="List of source `Concept` objects",
        description="https://rdf-vocabulary.ddialliance.org/xkos.html#correspondences",
        example=[{"@id": "http://data.europa.eu/xsp/cn2023/010011000090"}],
    )
    target_concepts: conlist(Node, min_length=1) = Field(
        alias=RDF["target_concepts"],
        title="List of target `Concept` objects",
        description="https://rdf-vocabulary.ddialliance.org/xkos.html#correspondences",
        example=[{"@id": "http://data.europa.eu/xsp/cn2024/010011000090"}],
    )

    model_config = ConfigDict(extra="allow")

    def model_dump(self, exclude_unset=True, by_alias=True, *args, **kwargs):
        return super().model_dump(*args, exclude_unset=exclude_unset, by_alias=by_alias, **kwargs)

    @field_validator("types", mode="after")
    @classmethod
    def type_includes_association(cls, value: list[str]) -> list[str]:
        SCHEME = f"{XKOS}ConceptAssociation"
        if SCHEME not in value:
            raise ValueError(f"`@type` must include `{SCHEME}`")
        return value
