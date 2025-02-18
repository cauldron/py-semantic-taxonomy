from collections.abc import MutableMapping
from dataclasses import dataclass
from enum import Enum
from typing import Any, Generator


class Document(MutableMapping):
    """
    Store JSON-LD as a dictionary with some convenience methods.

    In any given document (such as Concept, ConceptScheme), there are some required fields, some
    optional fields, and the ability for the user to add additional fields. Therefore we work not on
    a fixed data schema but on the JSON-LD dictionary.

    Validation isn't needed as we do validation at data ingress.
    """

    def __init__(self, document: dict) -> None:
        self.document = document

    def __getitem__(self, key: Any) -> Any:
        return self.document[key]

    def __setitem__(self, key: Any, value: Any) -> None:
        self.document[key] = value

    def __delitem__(self, key: Any) -> None:
        del self.document[key]

    def __iter__(self) -> Generator:
        return iter(self.document)

    def __len__(self) -> int:
        return len(self.document)

    def __getattr__(self, key: Any) -> Any:
        try:
            return self.document[self.__config[key]["label"]]
        except KeyError:
            return super().__getattr__(key)

    def __setattr__(self, key: Any, value: Any) -> None:
        try:
            properties = self.__config[key]
            if properties["read-only"]:
                raise ValueError(f"Attribute {key} is read-only")
            self.document[properties["label"]] = value
        except KeyError:
            return super().__setattr__(key, value)


class Concept(Document):
    __config = {
        "id_": {"label": "@id", "read-only": True},
        "type_": {"label": "@type", "read-only": True},
        "pref_labels": {
            "label": "http://www.w3.org/2004/02/skos/core#prefLabel",
            "read-only": False,
        },
        "alt_labels": {"label": "http://www.w3.org/2004/02/skos/core#altLabel", "read-only": False},
        "hidden_labels": {
            "label": "http://www.w3.org/2004/02/skos/core#hiddenLabel",
            "read-only": False,
        },
        "definitions": {
            "label": "http://www.w3.org/2004/02/skos/core#definition",
            "read-only": False,
        },
    }


class ConceptScheme(Document):
    __config = {
        "id_": {"label": "@id", "read-only": True},
        "type_": {"label": "@type", "read-only": True},
        "pref_labels": {
            "label": "http://www.w3.org/2004/02/skos/core#prefLabel",
            "read-only": False,
        },
        "definitions": {
            "label": "http://www.w3.org/2004/02/skos/core#definition",
            "read-only": False,
        },
    }


class EdgeKind(Enum):
    in_scheme = "http://www.w3.org/2004/02/skos/core#inScheme"


@dataclass
class Edge:
    source: str  # IRI
    target: str  # IRI
    kind: EdgeKind
