from typing import Self

from py_semantic_taxonomy.domain.entities import Concept, GraphObject
from py_semantic_taxonomy.adapters.persistence.session import Session
from py_semantic_taxonomy.adapters.persistence.tables import Concept


class PostgresKOSGraph:
    def __init__(self) -> Self:
        pass

    async def get_concept(self, iri: str) -> Concept:
        pass

    async def get_object_type(self, iri: str) -> GraphObject:
        pass
