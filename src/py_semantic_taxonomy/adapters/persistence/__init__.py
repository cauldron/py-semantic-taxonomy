from py_semantic_taxonomy.domain.entities import Concept, GraphObject


class PostgresKOSGraph:
    async def get_concept(self, iri: str) -> Concept:
        pass

    async def get_object_type(self, iri: str) -> GraphObject:
        pass
