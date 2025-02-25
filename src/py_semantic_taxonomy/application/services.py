from fastapi.params import Depends

from py_semantic_taxonomy.routers.dependencies import get_kos_graph
from py_semantic_taxonomy.domain.entities import Concept, GraphObject
from py_semantic_taxonomy.domain.ports import KOSGraph


class GraphService:
    def __init__(self, graph: KOSGraph = Depends(get_kos_graph)):
        self.graph = graph

    async def get_concept(self, iri: str) -> Concept:
        return await self.graph.get_concept(iri=iri)

    async def get_object_type(self, iri: str) -> GraphObject:
        return await self.graph.get_object_type(iri=iri)
