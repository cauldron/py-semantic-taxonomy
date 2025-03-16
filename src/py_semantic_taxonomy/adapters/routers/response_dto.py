from pydantic import BaseModel, ConfigDict, Field

from py_semantic_taxonomy.domain.constants import RDF_MAPPING as RDF
from py_semantic_taxonomy.domain.constants import RelationshipVerbs as RV


class ErrorMessage(BaseModel):
    message: str
    detail: dict | None = None


class KOSCommon(BaseModel):
    id_: str = Field(alias=RDF["id_"])
    types: list[str] = Field(alias=RDF["types"])
    pref_labels: list[dict[str, str]] = Field(alias=RDF["pref_labels"])
    status: list[dict[str, str]] = Field(alias=RDF["status"])
    definitions: list[dict[str, str]] = Field(alias=RDF["definitions"], default=[])
    notations: list[dict[str, str]] = Field(alias=RDF["notations"], default=[])
    change_notes: list[dict] = Field(alias=RDF["change_notes"], default=[])
    history_notes: list[dict] = Field(alias=RDF["history_notes"], default=[])
    editorial_notes: list[dict] = Field(alias=RDF["editorial_notes"], default=[])

    model_config = ConfigDict(extra="allow")

    def model_dump(self, exclude_unset=True, by_alias=True, *args, **kwargs):
        return super().model_dump(*args, exclude_unset=exclude_unset, by_alias=by_alias, **kwargs)


class Concept(KOSCommon):
    schemes: list[dict] = Field(alias=RDF["schemes"])
    alt_labels: list[dict[str, str]] = Field(alias=RDF["alt_labels"], default=[])
    hidden_labels: list[dict[str, str]] = Field(alias=RDF["hidden_labels"], default=[])
    top_concept_of: list[dict] = Field(alias=RDF["top_concept_of"], default=[])


class ConceptScheme(KOSCommon):
    created: list[dict] = Field(alias="http://purl.org/dc/terms/created")
    creators: list[dict] = Field(alias="http://purl.org/dc/terms/creator")
    version: list[dict] = Field(alias="http://www.w3.org/2002/07/owl#versionInfo")


class Relationship(BaseModel):
    id_: str = Field(alias=RDF["id_"])
    broader: list[dict] = Field(alias=RV.broader, default=[])
    narrower: list[dict] = Field(alias=RV.narrower, default=[])
    exact_match: list[dict] = Field(alias=RV.exact_match, default=[])
    close_match: list[dict] = Field(alias=RV.close_match, default=[])
    broad_match: list[dict] = Field(alias=RV.broad_match, default=[])
    narrow_match: list[dict] = Field(alias=RV.narrow_match, default=[])
    related_match: list[dict] = Field(alias=RV.related_match, default=[])

    model_config = ConfigDict(extra="forbid")

    def model_dump(self, exclude_unset=True, by_alias=True, *args, **kwargs):
        return super().model_dump(*args, exclude_unset=exclude_unset, by_alias=by_alias, **kwargs)


class Correspondence(ConceptScheme):
    compares: list[dict] = Field(alias=RDF["compares"])
    made_ofs: list[dict] = Field(alias=RDF["made_ofs"], default=[])


class Association(BaseModel):
    id_: str = Field(alias=RDF["id_"])
    types: list[str] = Field(alias=RDF["types"])
    source_concepts: list[dict] = Field(alias=RDF["source_concepts"])
    target_concepts: list[dict] = Field(alias=RDF["target_concepts"])
