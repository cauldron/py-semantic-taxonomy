from fastapi.params import Depends

from py_semantic_taxonomy.adapters.routers.dependencies import get_kos_graph
from py_semantic_taxonomy.domain.entities import Concept, ConceptScheme, GraphObject, Relationship
from py_semantic_taxonomy.domain.ports import KOSGraph


class GraphService:
    def __init__(self, graph: KOSGraph = Depends(get_kos_graph)):
        self.graph = graph

    async def get_object_type(self, iri: str) -> GraphObject:
        return await self.graph.get_object_type(iri=iri)

    # Concept

    async def concept_get(self, iri: str) -> Concept:
        return await self.graph.concept_get(iri=iri)

    async def concept_create(self, concept: Concept) -> Concept:
        return await self.graph.concept_create(concept=concept)

    async def concept_update(self, concept: Concept) -> Concept:
        return await self.graph.concept_update(concept=concept)

    async def concept_delete(self, iri: str) -> int:
        return await self.graph.concept_delete(iri=iri)

    # Concept Scheme

    async def concept_scheme_get(self, iri: str) -> ConceptScheme:
        return await self.graph.concept_scheme_get(iri=iri)

    async def concept_scheme_create(self, concept_scheme: ConceptScheme) -> ConceptScheme:
        return await self.graph.concept_scheme_create(concept_scheme=concept_scheme)

    async def concept_scheme_update(self, concept_scheme: ConceptScheme) -> ConceptScheme:
        return await self.graph.concept_scheme_update(concept_scheme=concept_scheme)

    async def concept_scheme_delete(self, iri: str) -> int:
        return await self.graph.concept_scheme_delete(iri=iri)

    # Relationships

    async def relationships_get(
        self, iri: str, only_source: bool = False, only_target: bool = False
    ) -> list[Relationship]:
        return await self.graph.relationships_get(
            iri=iri, only_source=only_source, only_target=only_target
        )
