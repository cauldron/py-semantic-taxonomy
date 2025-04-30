from copy import copy
from dataclasses import asdict, dataclass, field, fields
from datetime import datetime
from urllib.parse import quote_plus, unquote

from py_semantic_taxonomy.domain.constants import (
    RDF_MAPPING,
    SKOS_RELATIONSHIP_PREDICATES,
    AssociationKind,
    RelationshipVerbs,
)
from py_semantic_taxonomy.domain.hash_utils import hash_fnv64


def select_string_for_language(objs: list[dict], language: str, concatenate: bool = False) -> str:
    strings = [
        obj["@value"] for obj in objs if obj["@language"].lower().startswith(language.lower())
    ]
    if concatenate:
        return " ".join(strings)
    return strings


def select_language(objs: list[dict], language: str) -> str:
    return [obj for obj in objs if obj["@language"].lower().startswith(language.lower())]


# Allow mixing non-default and default values in dataclasses
# See https://www.trueblade.com/blogs/news/python-3-10-new-dataclass-features
@dataclass(kw_only=True)
class Serializable:
    def to_db_dict(self) -> dict:
        return asdict(self)

    def to_json_ld(self, fields_: list[str] = [], extra: bool = True) -> dict:
        """Return this data formatted as (but not serialized to) SKOS expanded JSON LD"""
        class_fields = fields_ or {f.name for f in fields(self)}.difference({"extra"})
        dct = copy(self.extra) if extra else {}
        for attr, label in RDF_MAPPING.items():
            if attr not in class_fields:
                continue
            if value := getattr(self, attr):
                dct[label] = value

        return dct

    @classmethod
    def from_json_ld(cls, dict_: dict, fields_: list[str] = [], extra: bool = True) -> "SKOS":
        source_dict, data = copy(dict_), {}
        class_fields = fields_ or {f.name for f in fields(cls)}.difference({"extra"})
        for dataclass_label, skos_label in RDF_MAPPING.items():
            if dataclass_label in class_fields and skos_label in source_dict:
                data[dataclass_label] = source_dict.pop(skos_label)
        if extra:
            data["extra"] = {
                key: value
                for key, value in source_dict.items()
                if key not in SKOS_RELATIONSHIP_PREDICATES
            }
        return cls(**data)


@dataclass(kw_only=True)
class SKOS(Serializable):
    id_: str
    types: list[str]
    pref_labels: list[dict[str, str]]
    status: list[dict]
    notations: list[dict[str, str]] = field(default_factory=list)
    definitions: list[dict[str, str]] = field(default_factory=list)
    change_notes: list[dict] = field(default_factory=list)
    history_notes: list[dict] = field(default_factory=list)
    editorial_notes: list[dict] = field(default_factory=list)
    extra: dict = field(default_factory=dict)


@dataclass(kw_only=True)
class Concept(SKOS):
    schemes: list[dict]
    alt_labels: list[dict[str, str]] = field(default_factory=list)
    hidden_labels: list[dict[str, str]] = field(default_factory=list)
    top_concept_of: list[dict] = field(default_factory=list)

    def to_search_dict(self, language: str) -> dict:
        return {
            # Can't use URL as id, even if escaped:
            # https://github.com/typesense/typesense/issues/192
            "id": hash_fnv64(self.id_),
            "url": quote_plus(self.id_),
            "alt_labels": select_string_for_language(self.alt_labels, language),
            "hidden_labels": select_string_for_language(self.hidden_labels, language),
            # One per language but can have language variants
            "pref_label": select_string_for_language(self.pref_labels, language, concatenate=True),
            "definition": select_string_for_language(self.definitions, language, concatenate=True),
            # Not language-specific
            "notation": " ".join([obj["@value"] for obj in self.notations]),
            "all_languages_pref_labels": [obj["@value"] for obj in self.pref_labels],
        }

    def filter_language(self, language: str) -> "Concept":
        SAME_FIELDS = (
            "change_notes",
            "editorial_notes",
            "extra",
            "history_notes",
            "id_",
            "notations",
            "schemes",
            "status",
            "top_concept_of",
            "types",
        )
        return Concept(
            alt_labels=select_language(self.alt_labels, language),
            definitions=select_language(self.definitions, language),
            hidden_labels=select_language(self.hidden_labels, language),
            pref_labels=select_language(self.pref_labels, language),
            **{field: getattr(self, field) for field in SAME_FIELDS},
        )


@dataclass(kw_only=True)
class ConceptScheme(SKOS):
    created: list[datetime]
    creators: list[dict]
    version: list[str]

    def filter_language(self, language: str) -> "Concept":
        SAME_FIELDS = (
            "change_notes",
            "created",
            "creators",
            "editorial_notes",
            "extra",
            "history_notes",
            "id_",
            "notations",
            "status",
            "types",
            "version",
        )
        return ConceptScheme(
            definitions=select_language(self.definitions, language),
            pref_labels=select_language(self.pref_labels, language),
            **{field: getattr(self, field) for field in SAME_FIELDS},
        )


@dataclass(frozen=True)
class Relationship:
    source: str
    target: str
    predicate: RelationshipVerbs

    def to_db_dict(self) -> dict:
        return asdict(self)

    def to_json_ld(self) -> dict:
        """Return this data formatted as (but not serialized to) SKOS expanded JSON LD"""
        return {"@id": self.source, str(self.predicate): [{"@id": self.target}]}

    @classmethod
    def from_json_ld(cls, obj: dict) -> list["Relationship"]:
        def _get_object_id(obj: dict) -> str:
            try:
                return obj["@id"]
            except KeyError:
                raise ValueError(f"Can't find `@id` in given JSON-LD object: {obj}")

        result = set()
        mapping = {elem.value: elem for elem in RelationshipVerbs}
        source = _get_object_id(obj)

        for key, value in obj.items():
            if key == RelationshipVerbs.narrower:
                for elem in value:
                    result.add((_get_object_id(elem), RelationshipVerbs.broader, source))
            elif key in mapping:
                for elem in value:
                    result.add((source, mapping[key], _get_object_id(elem)))

        return sorted(
            [Relationship(source=s, target=o, predicate=p) for s, p, o in result],
            key=lambda x: (x.source, x.target, x.predicate),
        )

    @classmethod
    def from_json_ld_list(cls, obj: list[dict]) -> list["Relationship"]:
        return sorted(
            {rel for elem in obj for rel in cls.from_json_ld(elem)},
            key=lambda x: (x.source, x.target, x.predicate),
        )


@dataclass(kw_only=True)
class Correspondence(ConceptScheme):
    compares: list[dict]
    made_ofs: list[dict] = field(default_factory=list)


@dataclass(kw_only=True)
class MadeOf(Serializable):
    id_: str
    made_ofs: list[dict]

    def to_json_ld(self) -> dict:
        return super().to_json_ld(extra=False)

    @classmethod
    def from_json_ld(cls, dict_: dict) -> "Association":
        return super().from_json_ld(dict_=dict_, extra=False)


@dataclass(kw_only=True)
class Association(Serializable):
    id_: str
    types: list[str]
    source_concepts: list[dict]
    target_concepts: list[dict]
    kind: AssociationKind = AssociationKind.simple
    extra: dict = field(default_factory=dict)

    def __post_init__(self):
        self.kind = (
            AssociationKind.conditional if len(self.source_concepts) > 1 else AssociationKind.simple
        )

    def to_json_ld(self) -> dict:
        # Exclude `extra`
        return super().to_json_ld(fields_={"id_", "types", "source_concepts", "target_concepts"})

    @classmethod
    def from_json_ld(cls, dict_: dict) -> "Association":
        # Exclude `extra`
        return super().from_json_ld(
            dict_=dict_, fields_={"id_", "types", "source_concepts", "target_concepts"}
        )


# For type hinting
GraphObject = Concept | ConceptScheme | Correspondence | Association


@dataclass
class SearchResult:
    id_: str
    label: str
    highlight: str | None = None

    @staticmethod
    def from_typesense_results(results: dict) -> list["SearchResult"]:
        return [
            SearchResult(
                id_=unquote(res["document"]["url"]),
                label=res["document"]["pref_label"],
                highlight=(
                    res["highlight"]["pref_label"]["snippet"]
                    if "pref_label" in res["highlight"]
                    else None
                ),
            )
            for res in results["hits"]
        ]

    def to_json(self) -> dict:
        return asdict(self)


class NotFoundError(Exception):
    pass


class ConceptNotFoundError(NotFoundError):
    pass


class ConceptSchemeNotFoundError(NotFoundError):
    pass


class RelationshipNotFoundError(NotFoundError):
    pass


class CorrespondenceNotFoundError(NotFoundError):
    pass


class AssociationNotFoundError(NotFoundError):
    pass


class DuplicateIRI(Exception):
    pass


class DuplicateRelationship(Exception):
    pass


class HierarchicRelationshipAcrossConceptScheme(Exception):
    pass


class RelationshipsInCurrentConceptScheme(Exception):
    pass


class RelationshipsReferencesConceptScheme(Exception):
    pass


class ConceptSchemesNotInDatabase(Exception):
    pass


class HierarchyConflict(Exception):
    pass


class UnknownLanguage(Exception):
    pass


class SearchNotConfigured(Exception):
    pass
