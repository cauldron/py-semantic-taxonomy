from sqlalchemy import select

from py_semantic_taxonomy.adapters.persistence.database import bound_async_sessionmaker as Session
from py_semantic_taxonomy.adapters.persistence.tables import Concept as ConceptTable
from py_semantic_taxonomy.domain.entities import Concept, ConceptNotFoundError, GraphObject


class PostgresKOSGraph:
    async def get_concept(self, iri: str) -> Concept:
        async with Session() as session:
            stmt = select(ConceptTable).where(ConceptTable.id_ == iri)
            connection = await session.connection()
            result = (await connection.execute(stmt)).first()
            if not result:
                raise ConceptNotFoundError
            return Concept(**result._mapping)

    async def get_object_type(self, iri: str) -> GraphObject:
        async with Session() as session:
            stmt = select(ConceptTable).where(ConceptTable.id_ == iri)
            connection = await session.connection()
            result = (await connection.execute(stmt)).rowcount
            if result:
                return Concept
