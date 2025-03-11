from copy import copy
from dataclasses import asdict, dataclass, field
from datetime import datetime

from py_semantic_taxonomy.domain.constants import SKOS, SKOS_RELATIONSHIP_PREDICATES

SKOS_MAPPING = {
    "id_": "@id",
    "types": "@type",
    "schemes": f"{SKOS}inScheme",
    "pref_labels": f"{SKOS}prefLabel",
    "definitions": f"{SKOS}definition",
    "notations": f"{SKOS}notation",
    "alt_labels": f"{SKOS}altLabel",
    "hidden_labels": f"{SKOS}hiddenLabel",
    "change_notes": f"{SKOS}changeNote",
    "history_notes": f"{SKOS}historyNote",
    "editorial_notes": f"{SKOS}editorialNote",
}


# Allow mixing non-default and default values in dataclasses
# See https://www.trueblade.com/blogs/news/python-3-10-new-dataclass-features
@dataclass(kw_only=True)
class SKOS:
    id_: str
    types: list[str]
    pref_labels: list[dict[str, str]]
    definitions: list[dict[str, str]] = field(default_factory=list)
    change_notes: list[dict] = field(default_factory=list)
    history_notes: list[dict] = field(default_factory=list)
    editorial_notes: list[dict] = field(default_factory=list)
    extra: dict = field(default_factory=dict)

    def to_db_dict(self) -> dict:
        return asdict(self)

    def to_json_ld(self) -> dict:
        """Return this data formatted as (but not serialized to) SKOS expanded JSON LD"""
        dct = copy(self.extra)
        for attr, label in SKOS_MAPPING.items():
            if value := getattr(self, attr):
                dct[label] = value

        return dct

    @classmethod
    def from_json_ld(cls, concept_dict: dict) -> "Concept":
        source_dict, data = copy(concept_dict), {}
        for dataclass_label, skos_label in SKOS_MAPPING.items():
            if skos_label in source_dict:
                data[dataclass_label] = source_dict.pop(skos_label)
        data["extra"] = {
            key: value
            for key, value in source_dict.items()
            if key not in SKOS_RELATIONSHIP_PREDICATES
        }
        return cls(**data)


@dataclass(kw_only=True)
class Concept(SKOS):
    schemes: list[dict]
    notations: list[dict[str, str]] = field(default_factory=list)
    alt_labels: list[dict[str, str]] = field(default_factory=list)
    hidden_labels: list[dict[str, str]] = field(default_factory=list)


@dataclass(kw_only=True)
class ConceptScheme(SKOS):
    created: list[datetime]
    creators: list[dict]
    version: list[str]


# For type hinting
# Will be Concept | ConceptScheme | Correspondence | Association
GraphObject = Concept | ConceptScheme


class NotFoundError(Exception):
    pass


class ConceptNotFoundError(NotFoundError):
    pass


class ConceptSchemeNotFoundError(NotFoundError):
    pass


class DuplicateIRI(Exception):
    pass
