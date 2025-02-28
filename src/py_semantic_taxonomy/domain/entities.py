from copy import copy
from dataclasses import asdict, dataclass, field

SKOS = "http://www.w3.org/2004/02/skos/core#"
CONCEPT_MAPPING = {
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


@dataclass
class Concept:
    id_: str
    types: list[str]
    pref_labels: list[dict[str, str]]
    schemes: list[dict]
    definitions: list[dict[str, str]] = field(default_factory=list)
    notations: list[dict[str, str]] = field(default_factory=list)
    alt_labels: list[dict[str, str]] = field(default_factory=list)
    hidden_labels: list[dict[str, str]] = field(default_factory=list)
    change_notes: list[dict] = field(default_factory=list)
    history_notes: list[dict] = field(default_factory=list)
    editorial_notes: list[dict] = field(default_factory=list)
    extra: dict = field(default_factory=dict)

    def to_db_dict(self) -> dict:
        return asdict(self)

    def to_json_ld(self) -> dict:
        """Return this data formatted as (but not serialized to) SKOS expanded JSON LD"""
        dct = copy(self.extra)
        for attr, label in CONCEPT_MAPPING.items():
            if value := getattr(self, attr):
                dct[label] = value

        return dct

    @staticmethod
    def from_json_ld(concept_dict: dict) -> "Concept":
        source_dict, data = copy(concept_dict), {}
        for dataclass_label, skos_label in CONCEPT_MAPPING.items():
            if skos_label in source_dict:
                data[dataclass_label] = source_dict.pop(skos_label)
        data["extra"] = source_dict
        return Concept(**data)


# Will be Concept | ConceptScheme | Correspondence | Association
GraphObject = Concept


class NotFoundError(Exception):
    pass


class ConceptNotFoundError(NotFoundError):
    pass


class DuplicateIRI(Exception):
    pass
