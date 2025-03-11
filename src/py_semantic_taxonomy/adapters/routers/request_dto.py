from typing import Self

from pydantic import BaseModel, ConfigDict, Field, conlist, field_validator, model_validator

from py_semantic_taxonomy.adapters.routers.validation import (
    IRI,
    DateTime,
    MultilingualString,
    Node,
    NonLiteralNote,
    Notation,
    VersionString,
    one_per_language,
)
from py_semantic_taxonomy.domain.constants import SKOS, SKOS_RELATIONSHIP_PREDICATES


class KOSCommon(BaseModel):
    id_: IRI = Field(alias="@id")
    types: conlist(item_type=IRI) = Field(alias="@type")
    pref_labels: conlist(MultilingualString, min_length=1) = Field(alias=f"{SKOS}prefLabel")
    notations: list[Notation] = Field(alias=f"{SKOS}notation", default=[])
    change_notes: list[NonLiteralNote] = Field(alias=f"{SKOS}changeNote", default=[])
    history_notes: list[NonLiteralNote] = Field(alias=f"{SKOS}historyNote", default=[])
    editorial_notes: list[NonLiteralNote] = Field(alias=f"{SKOS}editorialNote", default=[])

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

    schemes: conlist(Node, min_length=1) = Field(alias=f"{SKOS}inScheme")
    # Can have multiple alternative labels per language, and multiple languages
    alt_labels: list[MultilingualString] = Field(alias=f"{SKOS}altLabel", default=[])
    # Can have multiple hidden labels per language, and multiple languages
    hidden_labels: list[MultilingualString] = Field(alias=f"{SKOS}hiddenLabel", default=[])
    # One definition per language, at least one definition
    definitions: list[MultilingualString] = Field(alias=f"{SKOS}definition", default=[])

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
    @model_validator(mode="after")
    def hierarchy_doesnt_reference_self(self) -> Self:
        for node in self.broader:
            if node.id_ == self.id_:
                raise ValueError("Concept can't have `broader` relationship to itself")
        for node in self.narrower:
            if node.id_ == self.id_:
                raise ValueError("Concept can't have `narrower` relationship to itself")
        return self

    broader: list[Node] = Field(alias=f"{SKOS}broader", default=[])
    narrower: list[Node] = Field(alias=f"{SKOS}narrower", default=[])


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


class ConceptScheme(KOSCommon):
    """Validation class for SKOS Concept Schemes.

    Checks that required fields are included and have correct type."""

    # One definition per language, at least one definition
    definitions: conlist(MultilingualString, min_length=1) = Field(
        alias=f"{SKOS}definition",
    )
    created: conlist(DateTime, min_length=1, max_length=1) = Field(
        alias="http://purl.org/dc/terms/created"
    )
    creators: list[Node] = Field(alias="http://purl.org/dc/terms/creator")
    version: conlist(VersionString, min_length=1, max_length=1) = Field(
        alias="http://www.w3.org/2002/07/owl#versionInfo"
    )

    @field_validator("types", mode="after")
    @classmethod
    def type_includes_concept(cls, value: list[str]) -> list[str]:
        SCHEME = f"{SKOS}ConceptScheme"
        if SCHEME not in value:
            raise ValueError(f"`@type` must include `{SCHEME}`")
        return value

    @field_validator("definitions", mode="after")
    @classmethod
    def definition_one_per_language(
        cls, value: list[MultilingualString]
    ) -> list[MultilingualString]:
        return one_per_language(value, "definition")

    @model_validator(mode="before")
    @classmethod
    def check_no_top_concept(cls, data: dict) -> dict:
        """skos:hasTopConcept has range skos:Concept, which we don't want. Create links later."""
        if f"{SKOS}hasTopConcept" in data:
            raise ValueError(
                f"Found `hasTopConcept` in concept scheme; Use specific API calls to create or update this relationship."
            )
        return data
