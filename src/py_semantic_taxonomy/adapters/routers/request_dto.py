from pydantic import BaseModel, ConfigDict, Field, conlist, field_validator

from py_semantic_taxonomy.adapters.routers.validation import (
    IRI,
    DateTime,
    MultilingualString,
    Node,
    VersionString,
    one_per_language,
)


class KOSCommon(BaseModel):
    id_: IRI = Field(alias="@id")
    types_: conlist(item_type=IRI) = Field(alias="@type")
    pref_labels: conlist(MultilingualString, min_length=1) = Field(
        alias="http://www.w3.org/2004/02/skos/core#prefLabel"
    )
    # One definition per language, at least one definition
    definitions: conlist(MultilingualString, min_length=1) = Field(
        alias="http://www.w3.org/2004/02/skos/core#definition", default=[]
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

    @field_validator("definitions", mode="after")
    @classmethod
    def definition_one_per_language(
        cls, value: list[MultilingualString]
    ) -> list[MultilingualString]:
        return one_per_language(value, "definition")


class Concept(KOSCommon):
    """Validation class for SKOS Concepts.

    Checks that required fields are included and have correct type."""

    schemes: list[Node] = Field(alias="http://www.w3.org/2004/02/skos/core#inScheme")
    # Can have multiple alternative labels per language, and multiple languages
    alt_labels: list[MultilingualString] = Field(
        alias="http://www.w3.org/2004/02/skos/core#altLabel", default=[]
    )
    # Can have multiple hidden labels per language, and multiple languages
    hidden_labels: list[MultilingualString] = Field(
        alias="http://www.w3.org/2004/02/skos/core#hiddenLabel", default=[]
    )
    broader: list[Node] = Field(alias="http://www.w3.org/2004/02/skos/core#broader", default=[])
    narrower: list[Node] = Field(alias="http://www.w3.org/2004/02/skos/core#narrower", default=[])

    @field_validator("types_", mode="after")
    @classmethod
    def type_includes_concept(cls, value: list[str]) -> list[str]:
        CONCEPT = "http://www.w3.org/2004/02/skos/core#Concept"
        if CONCEPT not in value:
            raise ValueError(f"`@type` must include `{CONCEPT}`")
        return value


class ConceptScheme(KOSCommon):
    """Validation class for SKOS Concept Schemes.

    Checks that required fields are included and have correct type."""

    created: conlist(DateTime, min_length=1, max_length=1) = Field(
        alias="http://purl.org/dc/terms/created"
    )
    creators: list[Node] = Field(alias="http://purl.org/dc/terms/creator")
    version: conlist(VersionString, min_length=1, max_length=1) = Field(
        alias="http://www.w3.org/2002/07/owl#versionInfo"
    )
    # Range is an object, so `{"@id": "foo"}` instead of `"foo"`.
    top_concepts: list[Node] = Field(alias="http://www.w3.org/2004/02/skos/core#hasTopConcept")
    pref_labels: conlist(MultilingualString, min_length=1) = Field(
        alias="http://www.w3.org/2004/02/skos/core#prefLabel"
    )
    # One definition per language
    definitions: conlist(MultilingualString, min_length=1) = Field(
        alias="http://www.w3.org/2004/02/skos/core#definition"
    )

    @field_validator("types_", mode="after")
    @classmethod
    def type_includes_concept(cls, value: list[str]) -> list[str]:
        SCHEME = "http://www.w3.org/2004/02/skos/core#ConceptScheme"
        if SCHEME not in value:
            raise ValueError(f"`@type` must include `{SCHEME}`")
        return value
