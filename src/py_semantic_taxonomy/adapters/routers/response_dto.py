from pydantic import BaseModel, ConfigDict, Field

from py_semantic_taxonomy.domain.constants import SKOS


class ErrorMessage(BaseModel):
    message: str
    detail: dict | None = None


class KOSCommon(BaseModel):
    id_: str = Field(alias="@id")
    types: list[str] = Field(alias="@type")
    pref_labels: list[dict[str, str]] = Field(alias=f"{SKOS}prefLabel")
    definitions: list[dict[str, str]] = Field(alias=f"{SKOS}definition", default=[])
    notations: list[dict[str, str]] = Field(alias=f"{SKOS}notation", default=[])
    change_notes: list[dict] = Field(alias=f"{SKOS}changeNote", default=[])
    history_notes: list[dict] = Field(alias=f"{SKOS}historyNote", default=[])
    editorial_notes: list[dict] = Field(alias=f"{SKOS}editorialNote", default=[])

    model_config = ConfigDict(extra="allow")

    def model_dump(self, exclude_unset=True, by_alias=True, *args, **kwargs):
        return super().model_dump(*args, exclude_unset=exclude_unset, by_alias=by_alias, **kwargs)


class Concept(KOSCommon):
    schemes: list[dict] = Field(alias=f"{SKOS}inScheme")
    alt_labels: list[dict[str, str]] = Field(alias=f"{SKOS}altLabel", default=[])
    hidden_labels: list[dict[str, str]] = Field(alias=f"{SKOS}hiddenLabel", default=[])


class ConceptScheme(KOSCommon):
    created: list[dict] = Field(alias="http://purl.org/dc/terms/created")
    creators: list[dict] = Field(alias="http://purl.org/dc/terms/creator")
    version: list[dict] = Field(alias="http://www.w3.org/2002/07/owl#versionInfo")


class Relationship(BaseModel):
    id_: str = Field(alias="@id")
    broader: list[dict] = Field(alias=f"{SKOS}broader", default=[])
    narrower: list[dict] = Field(alias=f"{SKOS}narrower", default=[])
    exact_match: list[dict] = Field(alias=f"{SKOS}exactMatch", default=[])
    close_match: list[dict] = Field(alias=f"{SKOS}closeMatch", default=[])
    broad_match: list[dict] = Field(alias=f"{SKOS}broadMatch", default=[])
    narrow_match: list[dict] = Field(alias=f"{SKOS}narrowMatch", default=[])
    related_match: list[dict] = Field(alias=f"{SKOS}relatedMatch", default=[])

    model_config = ConfigDict(extra="forbid")

    def model_dump(self, exclude_unset=True, by_alias=True, *args, **kwargs):
        return super().model_dump(*args, exclude_unset=exclude_unset, by_alias=by_alias, **kwargs)
