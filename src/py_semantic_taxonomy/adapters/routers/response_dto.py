from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ErrorMessage(BaseModel):
    message: str
    detail: dict | None = None


class KOSCommon(BaseModel):
    id_: str = Field(alias="@id")
    types: list[str] = Field(alias="@type")
    pref_labels: list[dict[str, str]] = Field(alias="http://www.w3.org/2004/02/skos/core#prefLabel")
    definitions: list[dict[str, str]] = Field(
        alias="http://www.w3.org/2004/02/skos/core#definition", default=[]
    )
    notations: list[dict[str, str]] = Field(
        alias="http://www.w3.org/2004/02/skos/core#notation", default=[]
    )
    change_notes: list[dict] = Field(
        alias="http://www.w3.org/2004/02/skos/core#changeNote", default=[]
    )
    history_notes: list[dict] = Field(
        alias="http://www.w3.org/2004/02/skos/core#historyNote", default=[]
    )
    editorial_notes: list[dict] = Field(
        alias="http://www.w3.org/2004/02/skos/core#editorialNote", default=[]
    )

    model_config = ConfigDict(extra="allow")

    def model_dump(self, exclude_unset=True, by_alias=True, *args, **kwargs):
        return super().model_dump(*args, exclude_unset=exclude_unset, by_alias=by_alias, **kwargs)


class Concept(KOSCommon):
    schemes: list[dict] = Field(alias="http://www.w3.org/2004/02/skos/core#inScheme")
    alt_labels: list[dict[str, str]] = Field(
        alias="http://www.w3.org/2004/02/skos/core#altLabel", default=[]
    )
    hidden_labels: list[dict[str, str]] = Field(
        alias="http://www.w3.org/2004/02/skos/core#hiddenLabel", default=[]
    )


class ConceptScheme(KOSCommon):
    created: list[dict] = Field(alias="http://purl.org/dc/terms/created")
    creators: list[dict] = Field(alias="http://purl.org/dc/terms/creator")
    version: list[dict] = Field(alias="http://www.w3.org/2002/07/owl#versionInfo")
