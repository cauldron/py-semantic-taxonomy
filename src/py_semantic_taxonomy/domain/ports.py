from typing import Protocol, runtime_checkable

from py_semantic_taxonomy.domain.constants import RelationshipVerbs
from py_semantic_taxonomy.domain.entities import (
    Association,
    Concept,
    ConceptScheme,
    Correspondence,
    GraphObject,
    MadeOf,
    Relationship,
    SearchResult,
)


@runtime_checkable
class KOSGraphDatabase(Protocol):
    async def get_object_type(self, iri: str) -> GraphObject: ...

    async def concept_get(self, iri: str) -> Concept: ...

    async def concept_create(self, concept: Concept) -> Concept: ...

    async def concept_update(self, concept: Concept) -> Concept: ...

    async def concept_delete(self, iri: str) -> int: ...

    async def concept_scheme_get(self, iri: str) -> ConceptScheme: ...

    async def concept_scheme_get_all_iris(self) -> list[str]: ...

    async def concept_scheme_create(self, concept_scheme: ConceptScheme) -> ConceptScheme: ...

    async def concept_scheme_update(self, concept_scheme: ConceptScheme) -> ConceptScheme: ...

    async def concept_scheme_delete(self, iri: str) -> int: ...

    async def relationships_get(
        self, iri: str, source: bool, target: bool
    ) -> list[Relationship]: ...

    async def relationships_create(
        self, relationships: list[Relationship]
    ) -> list[Relationship]: ...

    async def relationships_delete(self, relationships: list[Relationship]) -> int: ...

    async def relationship_source_target_share_known_concept_scheme(
        self, relationship: Relationship
    ) -> bool: ...

    async def known_concept_schemes_for_concept_hierarchical_relationships(
        self, iri: str
    ) -> list[str]: ...

    async def correspondence_get(self, iri: str) -> Correspondence: ...

    async def correspondence_create(self, correspondence: Correspondence) -> Correspondence: ...

    async def correspondence_update(self, correspondence: Correspondence) -> Correspondence: ...

    async def correspondence_delete(self, iri: str) -> int: ...

    async def association_get(self, iri: str) -> Association: ...

    async def association_create(self, association: Association) -> Association: ...

    async def association_delete(self, iri: str) -> int: ...

    async def made_of_add(self, made_of: MadeOf) -> Correspondence: ...

    async def made_of_remove(self, made_of: MadeOf) -> Correspondence: ...


@runtime_checkable
class GraphService(Protocol):
    async def get_object_type(self, iri: str) -> GraphObject: ...

    async def concept_get(self, iri: str) -> Concept: ...

    async def concept_create(
        self, concept: Concept, relationships: list[Relationship] = []
    ) -> Concept: ...

    async def concept_update(self, concept: Concept) -> Concept: ...

    async def concept_delete(self, iri: str) -> None: ...

    async def concept_scheme_get(self, iri: str) -> ConceptScheme: ...

    async def concept_scheme_get_all_iris(self) -> list[str]: ...

    async def concept_scheme_create(self, concept_scheme: ConceptScheme) -> ConceptScheme: ...

    async def concept_scheme_update(self, concept_scheme: ConceptScheme) -> ConceptScheme: ...

    async def concept_scheme_delete(self, iri: str) -> None: ...

    async def relationships_get(
        self,
        iri: str,
        source: bool = True,
        target: bool = False,
        verb: RelationshipVerbs | None = None,
    ) -> list[Relationship]: ...

    async def relationships_create(
        self, relationships: list[Relationship]
    ) -> list[Relationship]: ...

    async def relationships_delete(self, relationships: list[Relationship]) -> int: ...

    async def correspondence_get(self, iri: str) -> Correspondence: ...

    async def correspondence_create(self, correspondence: Correspondence) -> Correspondence: ...

    async def correspondence_update(self, correspondence: Correspondence) -> Correspondence: ...

    async def correspondence_delete(self, iri: str) -> None: ...

    async def made_of_add(self, made_of: MadeOf) -> Correspondence: ...

    async def made_of_remove(self, made_of: MadeOf) -> Correspondence: ...

    async def association_get(self, iri: str) -> Association: ...

    async def association_create(self, association: Association) -> Association: ...

    async def association_delete(self, iri: str) -> None: ...


@runtime_checkable
class SearchEngine(Protocol):
    async def initialize(self, collections: list[str]) -> None: ...

    async def reset(self) -> None: ...

    async def create_concept(self, concept: dict, collection: str) -> None: ...

    async def update_concept(self, concept: dict, collection: str) -> None: ...

    async def delete_concept(self, id_: str, collection: str) -> None: ...

    async def search(
        self, query: str, collection: str, semantic: bool, prefix: bool
    ) -> list[SearchResult]: ...


@runtime_checkable
class SearchService(Protocol):
    def is_configured(self) -> bool: ...

    async def initialize(self) -> None: ...

    async def reset(self) -> None: ...

    async def create_concept(self, concept: Concept) -> None: ...

    async def update_concept(self, concept: Concept) -> None: ...

    async def delete_concept(self, iri: str) -> None: ...

    async def search(
        self, query: str, language: str, semantic: bool = True, prefix: bool = False
    ) -> list[SearchResult]: ...

    async def suggest(self, query: str, language: str) -> list[SearchResult]: ...
