from copy import copy
from dataclasses import dataclass


@dataclass
class Concept:
    id_: str
    types: list[str]
    pref_labels: list[dict[str, str]]
    schemes: list[dict]
    definitions: list[dict[str, str]] = []
    notations: list[dict[str, str]] = []
    alt_labels: list[dict[str, str]] = []
    hidden_labels: list[dict[str, str]] = []
    change_notes: list[dict] = []
    history_notes: list[dict] = []
    editorial_notes: list[dict] = []
    extra: dict = {}

    def json_ld(self) -> dict:
        """Return this data formatted as (but not serialized to) SKOS expanded JSON LD"""
        skos = "http://www.w3.org/2004/02/skos/core#"
        mapping = {
            "id_": "@id",
            "types": "@type",
            "pref_labels": f"{skos}prefLabel",
            "definitions": f"{skos}definition",
            "notations": f"{skos}notation",
            "pref_labels": f"{skos}altLabel",
            "hidden_labels": f"{skos}hiddenLabel",
            "change_notes": f"{skos}changeNote",
            "history_notes": f"{skos}historyNote",
            "editorial_notes": f"{skos}editorialNote",
        }
        dct = copy(self.extra)
        for attr, label in mapping.items():
            if value := getattr(self, attr):
                dct[label] = value

        return dct


# Will be Concept | ConceptScheme | Correspondence | Association
GraphObject = Concept


class NotFoundError(Exception):
    pass


class ConceptNotFoundError(NotFoundError):
    pass
