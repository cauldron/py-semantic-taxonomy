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
    BIBO,
    SKOS,
    SKOS_RELATIONSHIP_PREDICATES,
)


class KOSCommon(BaseModel):
    id_: IRI = Field(alias="@id")
    types: conlist(item_type=IRI) = Field(alias="@type")
    pref_labels: conlist(MultilingualString, min_length=1) = Field(alias=f"{SKOS}prefLabel")
    status: conlist(Status, min_length=1) = Field(alias=f"{BIBO}status")
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


class Relationship(BaseModel):
    id_: IRI = Field(alias="@id")
    broader: list[Node] = Field(alias=f"{SKOS}broader", default=[])
    narrower: list[Node] = Field(alias=f"{SKOS}narrower", default=[])
    exact_match: list[Node] = Field(alias=f"{SKOS}exactMatch", default=[])
    close_match: list[Node] = Field(alias=f"{SKOS}closeMatch", default=[])
    broad_match: list[Node] = Field(alias=f"{SKOS}broadMatch", default=[])
    narrow_match: list[Node] = Field(alias=f"{SKOS}narrowMatch", default=[])
    related_match: list[Node] = Field(alias=f"{SKOS}relatedMatch", default=[])

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
