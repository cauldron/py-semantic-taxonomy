from fastapi.params import Depends

from py_semantic_taxonomy.adapters.routers.dependencies import get_kos_graph
from py_semantic_taxonomy.domain.entities import Concept, GraphObject
from py_semantic_taxonomy.domain.ports import KOSGraph


class GraphService:
    def __init__(self, graph: KOSGraph = Depends(get_kos_graph)):
        self.graph = graph

    async def get_object_type(self, iri: str) -> GraphObject:
        return await self.graph.get_object_type(iri=iri)

    async def concept_get(self, iri: str) -> Concept:
        return await self.graph.concept_get(iri=iri)

    async def concept_create(self, concept: Concept) -> Concept:
        return await self.graph.concept_create(concept=concept)

    async def concept_update(self, concept: Concept) -> Concept:
        return await self.graph.concept_update(concept=concept)

    async def concept_delete(self, iri: str) -> int:
        return await self.graph.concept_delete(iri=iri)
