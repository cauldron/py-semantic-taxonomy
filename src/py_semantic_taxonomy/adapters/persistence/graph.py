from sqlalchemy import Connection, func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncEngine

from py_semantic_taxonomy.adapters.persistence.database import create_engine
from py_semantic_taxonomy.adapters.persistence.tables import concept_table
from py_semantic_taxonomy.domain.entities import (
    Concept,
    ConceptNotFoundError,
    DuplicateIRI,
    GraphObject,
)


class PostgresKOSGraph:
    def __init__(self, engine: AsyncEngine | None = None):
        self.engine = create_engine() if engine is None else engine

    async def get_object_type(self, iri: str) -> GraphObject:
        async with self.engine.connect() as conn:
            is_concept = await self._get_concept_count_from_iri(conn, iri)
            if is_concept:
                return Concept

    # Concepts

    async def _get_concept_count_from_iri(self, connection: Connection, iri: str) -> int:
        stmt = select(func.count("*")).where(concept_table.c.id_ == iri)
        # TBD: This is ugly
        return (await connection.execute(stmt)).first()[0]

    async def concept_get(self, iri: str) -> Concept:
        async with self.engine.connect() as conn:
            stmt = select(concept_table).where(concept_table.c.id_ == iri)
            result = (await conn.execute(stmt)).first()
            if not result:
                raise ConceptNotFoundError
            await conn.rollback()
        return Concept(**result._mapping)

    async def concept_create(self, concept: Concept) -> Concept:
        async with self.engine.connect() as conn:
            count = await self._get_concept_count_from_iri(conn, concept.id_)
            if count:
                raise DuplicateIRI

            await conn.execute(
                insert(concept_table),
                [concept.to_db_dict()],
            )
            await conn.commit()
        return concept

    async def concept_update(self, concept: Concept) -> Concept:
        async with self.engine.connect() as conn:
            count = await self._get_concept_count_from_iri(conn, concept.id_)
            if not count:
                raise ConceptNotFoundError

            await conn.execute(
                update(concept_table)
                .where(concept_table.c.id_ == concept.id_)
                .values(**concept.to_db_dict())
            )
            await conn.commit()
        return concept
