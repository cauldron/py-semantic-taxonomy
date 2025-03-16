from copy import copy
from dataclasses import asdict, dataclass, field, fields
from datetime import datetime

from py_semantic_taxonomy.domain.constants import (
    RDF_MAPPING,
    SKOS_RELATIONSHIP_PREDICATES,
    AssociationKind,
    RelationshipVerbs,
)


# Allow mixing non-default and default values in dataclasses
# See https://www.trueblade.com/blogs/news/python-3-10-new-dataclass-features
@dataclass(kw_only=True)
class SKOS:
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

    def to_db_dict(self) -> dict:
        return asdict(self)

    def to_json_ld(self) -> dict:
        """Return this data formatted as (but not serialized to) SKOS expanded JSON LD"""
        dct = copy(self.extra)
        class_fields = {f.name for f in fields(self)}.difference({"extra"})
        for attr, label in RDF_MAPPING.items():
            if attr not in class_fields:
                continue
            if value := getattr(self, attr):
                dct[label] = value

        return dct

    @classmethod
    def from_json_ld(cls, dict_: dict) -> "SKOS":
        source_dict, data = copy(dict_), {}
        class_fields = {f.name for f in fields(cls)}.difference({"extra"})
        for dataclass_label, skos_label in RDF_MAPPING.items():
            if dataclass_label in class_fields and skos_label in source_dict:
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
    alt_labels: list[dict[str, str]] = field(default_factory=list)
    hidden_labels: list[dict[str, str]] = field(default_factory=list)


@dataclass(kw_only=True)
class ConceptScheme(SKOS):
    created: list[datetime]
    creators: list[dict]
    version: list[str]


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
    made_of: list[dict] = field(default_factory=list)


@dataclass(kw_only=True)
class Association:
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

    def to_db_dict(self) -> dict:
        return asdict(self)

    def to_json_ld(self) -> dict:
        """Return this data formatted as (but not serialized to) SKOS expanded JSON LD"""
        dct = copy(self.extra)
        class_fields = {"id_", "types", "source_concepts", "target_concepts"}
        for attr, label in RDF_MAPPING.items():
            if attr not in class_fields:
                continue
            if value := getattr(self, attr):
                dct[label] = value

        return dct

    @classmethod
    def from_json_ld(cls, dict_: dict) -> "Association":
        source_dict, data = copy(dict_), {}
        class_fields = {"id_", "types", "source_concepts", "target_concepts"}
        for dataclass_label, skos_label in RDF_MAPPING.items():
            if dataclass_label in class_fields and skos_label in source_dict:
                data[dataclass_label] = source_dict.pop(skos_label)
        data["extra"] = {key: value for key, value in source_dict.items()}
        return cls(**data)


# For type hinting
GraphObject = Concept | ConceptScheme | Correspondence | Association


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
