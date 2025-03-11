from typing import Protocol, runtime_checkable

from py_semantic_taxonomy.domain.entities import Concept, GraphObject


@runtime_checkable
class KOSGraph(Protocol):
    async def get_object_type(self, iri: str) -> GraphObject: ...

    async def concept_get(self, iri: str) -> Concept: ...

    async def concept_create(self, concept: Concept) -> Concept: ...

    async def concept_update(self, concept: Concept) -> Concept: ...
