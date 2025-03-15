from typing import Protocol, runtime_checkable

from py_semantic_taxonomy.domain.entities import (
    Concept,
    ConceptScheme,
    Correspondence,
    GraphObject,
    Relationship,
)


@runtime_checkable
class KOSGraph(Protocol):
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

    async def relationships_update(
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
