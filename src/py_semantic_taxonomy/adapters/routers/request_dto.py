from typing import Self

from pydantic import BaseModel, ConfigDict, Field, conlist, field_validator, model_validator

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
from py_semantic_taxonomy.domain.constants import (
    SKOS,
    SKOS_RELATIONSHIP_PREDICATES,
    XKOS,
    RDF_MAPPING as RDF,
    RelationshipVerbs as RV,
)


class KOSCommon(BaseModel):
    id_: IRI = Field(alias=RDF["id_"])
    types: conlist(item_type=IRI) = Field(alias=RDF["types"])
    pref_labels: conlist(MultilingualString, min_length=1) = Field(alias=RDF["pref_labels"])
    status: conlist(Status, min_length=1) = Field(alias=RDF["status"])
    notations: list[Notation] = Field(alias=RDF["notations"], default=[])
    change_notes: list[NonLiteralNote] = Field(alias=RDF["change_notes"], default=[])
    history_notes: list[NonLiteralNote] = Field(alias=RDF["history_notes"], default=[])
    editorial_notes: list[NonLiteralNote] = Field(alias=RDF["editorial_notes"], default=[])

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

    schemes: conlist(Node, min_length=1) = Field(alias=RDF["schemes"])
    # Can have multiple alternative labels per language, and multiple languages
    alt_labels: list[MultilingualString] = Field(alias=RDF["alt_labels"], default=[])
    # Can have multiple hidden labels per language, and multiple languages
    hidden_labels: list[MultilingualString] = Field(alias=RDF["hidden_labels"], default=[])
    # One definition per language, at least one definition
    definitions: list[MultilingualString] = Field(alias=RDF["definitions"], default=[])

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
    broader: list[Node] = Field(alias=RV.broader, default=[])
    narrower: list[Node] = Field(alias=RV.narrower, default=[])

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
        alias="http://purl.org/dc/terms/created"
    )
    creators: list[Node] = Field(alias="http://purl.org/dc/terms/creator")
    version: conlist(VersionString, min_length=1, max_length=1) = Field(
        alias="http://www.w3.org/2002/07/owl#versionInfo"
    )


class ConceptScheme(ConceptSchemeCommon):
    """Validation class for SKOS Concept Schemes.

    Checks that required fields are included and have correct type."""

    definitions: conlist(MultilingualString, min_length=1) = Field(
        alias=RDF["definitions"],
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
                f"Found `hasTopConcept` in concept scheme; Use specific API calls to create or update this relationship."
            )
        return data

    @field_validator("definitions", mode="after")
    @classmethod
    def definition_one_per_language(
        cls, value: list[MultilingualString]
    ) -> list[MultilingualString]:
        return one_per_language(value, "definition")


class Relationship(BaseModel):
    id_: IRI = Field(alias=RDF["id_"])
    broader: list[Node] = Field(alias=RV.broader, default=[])
    narrower: list[Node] = Field(alias=RV.narrower, default=[])
    exact_match: list[Node] = Field(alias=RV.exact_match, default=[])
    close_match: list[Node] = Field(alias=RV.close_match, default=[])
    broad_match: list[Node] = Field(alias=RV.broad_match, default=[])
    narrow_match: list[Node] = Field(alias=RV.narrow_match, default=[])
    related_match: list[Node] = Field(alias=RV.related_match, default=[])

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
    definitions: list[MultilingualString] = Field(alias=RDF["definitions"], default=[])
    compares: conlist(Node, min_length=1) = Field(alias=f"{XKOS}compares")

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
            if key == RDF["made_of"]:
                raise ValueError(
                    f"Found `{RDF['made_of']}` in new correspondence; use dedicated API calls for this data."
                )
        return data
