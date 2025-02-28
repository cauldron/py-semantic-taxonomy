from pydantic import BaseModel, ConfigDict, Field


class Concept(BaseModel):
    id_: str = Field(alias="@id")
    types: list[str] = Field(alias="@type")
    pref_labels: list[dict[str, str]] = Field(alias="http://www.w3.org/2004/02/skos/core#prefLabel")
    schemes: list[dict] = Field(alias="http://www.w3.org/2004/02/skos/core#inScheme")
    definitions: list[dict[str, str]] = Field(
        alias="http://www.w3.org/2004/02/skos/core#definition", default=[]
    )
    notations: list[dict[str, str]] = Field(
        alias="http://www.w3.org/2004/02/skos/core#notation", default=[]
    )
    alt_labels: list[dict[str, str]] = Field(
        alias="http://www.w3.org/2004/02/skos/core#altLabel", default=[]
    )
    hidden_labels: list[dict[str, str]] = Field(
        alias="http://www.w3.org/2004/02/skos/core#hiddenLabel", default=[]
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
