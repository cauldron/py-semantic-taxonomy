from sqlalchemy import Connection, Table, delete, func, insert, select, update
from sqlalchemy.exc import IntegrityError
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
    RelationshipNotFoundError,
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

    async def concept_create(
        self, concept: Concept, relationships: list[Relationship] = []
    ) -> Concept:
        async with self.engine.connect() as conn:
            count = await self._get_count_from_iri(conn, concept.id_, concept_table)
            if count:
                raise DuplicateIRI

            await conn.execute(
                insert(concept_table),
                [concept.to_db_dict()],
            )
            if relationships:
                await self._relationships_create(relationships, conn)
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
        self, iri: str, source: bool = True, target: bool = False
    ) -> list[Relationship]:
        if not source and not target:
            raise ValueError("Must choose at least one of source or target")
        async with self.engine.connect() as conn:
            rels = []
            if source:
                stmt = select(
                    # Exclude id field
                    relationship_table.c.source,
                    relationship_table.c.target,
                    relationship_table.c.predicate,
                ).where(relationship_table.c.source == iri)
                result = await conn.execute(stmt)
                rels.extend([Relationship(**line._mapping) for line in result])
            if target:
                stmt = select(
                    relationship_table.c.source,
                    relationship_table.c.target,
                    relationship_table.c.predicate,
                ).where(relationship_table.c.target == iri)
                result = await conn.execute(stmt)
                rels.extend([Relationship(**line._mapping) for line in result])
            await conn.rollback()
        return rels

    async def _relationships_create(
        self, relationships: list[Relationship], conn: Connection
    ) -> list[Relationship]:
        try:
            await conn.execute(
                insert(relationship_table), [obj.to_db_dict() for obj in relationships]
            )
        except IntegrityError as exc:
            await conn.rollback()
            err = exc._message()
            if (
                # SQLite: Unit tests
                "UNIQUE constraint failed: relationship.source, relationship.target"
                in err
            ) or (
                # Postgres: Integration tests
                'duplicate key value violates unique constraint "relationship_source_target_uniqueness"'
                in err
            ):
                # Provide useful feedback by identifying which relationship already exists
                for obj in relationships:
                    stmt = select(func.count("*")).where(
                        relationship_table.c.source == obj.source,
                        relationship_table.c.target == obj.target,
                    )
                    count = (await conn.execute(stmt)).first()[0]
                    if count:
                        raise DuplicateRelationship(
                            f"Relationship between source `{obj.source}` and target `{obj.target}` already exists"
                        )
            # Fallback - should never happen, but no one is perfect
            raise exc
        return relationships

    async def relationships_create(self, relationships: list[Relationship]) -> list[Relationship]:
        async with self.engine.connect() as conn:
            result = await self._relationships_create(relationships, conn)
            await conn.commit()
        return result

    async def _get_relationship_count(self, source: str, target: str, conn: Connection) -> int:
        stmt = select(func.count("*")).where(
            relationship_table.c.source == source, relationship_table.c.target == target
        )
        return (await conn.execute(stmt)).first()[0]

    async def relationships_update(self, relationships: list[Relationship]) -> list[Relationship]:
        async with self.engine.connect() as conn:
            for rel in relationships:
                count = await self._get_relationship_count(rel.source, rel.target, conn)
                if not count:
                    conn.rollback()
                    raise RelationshipNotFoundError(
                        f"Can't update non-existent relationship between source `{rel.source}` and target `{rel.target}`"
                    )
                await conn.execute(
                    update(relationship_table)
                    .where(
                        relationship_table.c.source == rel.source,
                        relationship_table.c.target == rel.target,
                    )
                    .values(predicate=rel.predicate)
                )
            await conn.commit()
        return relationships

    async def relationships_delete(self, relationships: list[Relationship]) -> int:
        async with self.engine.connect() as conn:
            count = 0
            for rel in relationships:
                print(rel, type(rel))
                result = await conn.execute(
                    delete(relationship_table).where(
                        relationship_table.c.source == rel.source,
                        relationship_table.c.target == rel.target,
                        relationship_table.c.predicate == rel.predicate,
                    )
                )
                count += result.rowcount
            await conn.commit()
        return count
