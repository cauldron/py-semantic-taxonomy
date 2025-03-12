from sqlalchemy import Connection, Table, delete, func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncEngine

from py_semantic_taxonomy.adapters.persistence.database import create_engine
from py_semantic_taxonomy.adapters.persistence.tables import (
    concept_scheme_table,
    concept_table,
    relationship_table,
)
from py_semantic_taxonomy.domain.entities import (
    Concept,
    ConceptNotFoundError,
    ConceptScheme,
    ConceptSchemeNotFoundError,
    DuplicateIRI,
    DuplicateRelationship,
    GraphObject,
    Relationship,
)


class PostgresKOSGraph:
    def __init__(self, engine: AsyncEngine | None = None):
        self.engine = create_engine() if engine is None else engine

    async def get_object_type(self, iri: str) -> GraphObject:
        async with self.engine.connect() as conn:
            is_concept = await self._get_count_from_iri(conn, iri, concept_table)
            if is_concept:
                return Concept
            is_cs = await self._get_count_from_iri(conn, iri, concept_scheme_table)
            if is_cs:
                return ConceptScheme

    # Concepts

    async def _get_count_from_iri(self, connection: Connection, iri: str, table: Table) -> int:
        stmt = select(func.count("*")).where(table.c.id_ == iri)
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
            count = await self._get_count_from_iri(conn, concept.id_, concept_table)
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
            count = await self._get_count_from_iri(conn, concept.id_, concept_table)
            if not count:
                raise ConceptNotFoundError

            await conn.execute(
                update(concept_table)
                .where(concept_table.c.id_ == concept.id_)
                .values(**concept.to_db_dict())
            )
            await conn.commit()
        return concept

    async def concept_delete(self, iri: str) -> int:
        async with self.engine.connect() as conn:
            result = await conn.execute(delete(concept_table).where(concept_table.c.id_ == iri))
            await conn.commit()
        return result.rowcount

    # ConceptScheme

    async def concept_scheme_get(self, iri: str) -> ConceptScheme:
        async with self.engine.connect() as conn:
            stmt = select(concept_scheme_table).where(concept_scheme_table.c.id_ == iri)
            result = (await conn.execute(stmt)).first()
            if not result:
                raise ConceptSchemeNotFoundError
            await conn.rollback()
        return ConceptScheme(**result._mapping)

    async def concept_scheme_create(self, concept_scheme: ConceptScheme) -> ConceptScheme:
        async with self.engine.connect() as conn:
            count = await self._get_count_from_iri(conn, concept_scheme.id_, concept_scheme_table)
            if count:
                raise DuplicateIRI

            await conn.execute(
                insert(concept_scheme_table),
                [concept_scheme.to_db_dict()],
            )
            await conn.commit()
        return concept_scheme

    async def concept_scheme_update(self, concept_scheme: ConceptScheme) -> ConceptScheme:
        async with self.engine.connect() as conn:
            count = await self._get_count_from_iri(conn, concept_scheme.id_, concept_scheme_table)
            if not count:
                raise ConceptSchemeNotFoundError

            await conn.execute(
                update(concept_scheme_table)
                .where(concept_scheme_table.c.id_ == concept_scheme.id_)
                .values(**concept_scheme.to_db_dict())
            )
            await conn.commit()
        return concept_scheme

    async def concept_scheme_delete(self, iri: str) -> int:
        async with self.engine.connect() as conn:
            result = await conn.execute(
                delete(concept_scheme_table).where(concept_scheme_table.c.id_ == iri)
            )
            await conn.commit()
        return result.rowcount

    # Relationship

    async def relationships_get(
        self, iri: str, only_source: bool = False, only_target: bool = False
    ) -> list[Relationship]:
        return
