from sqlalchemy import Table, delete, func, insert, join, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine

from py_semantic_taxonomy.adapters.persistence.database import create_engine
from py_semantic_taxonomy.adapters.persistence.tables import (
    association_table,
    concept_scheme_table,
    concept_table,
    correspondence_table,
    relationship_table,
)
from py_semantic_taxonomy.domain.constants import (
    SKOS_HIERARCHICAL_RELATIONSHIP_PREDICATES,
    RelationshipVerbs,
)
from py_semantic_taxonomy.domain.entities import (
    Association,
    AssociationNotFoundError,
    Concept,
    ConceptNotFoundError,
    ConceptScheme,
    ConceptSchemeNotFoundError,
    Correspondence,
    CorrespondenceNotFoundError,
    DuplicateIRI,
    DuplicateRelationship,
    GraphObject,
    MadeOf,
    NotFoundError,
    Relationship,
)


class PostgresKOSGraph:
    def __init__(self, engine: AsyncEngine | None = None):
        self.engine = create_engine() if engine is None else engine

    async def get_object_type(self, iri: str) -> GraphObject:
        async with self.engine.connect() as conn:
            if await self._get_count_from_iri(conn, iri, concept_table):
                return Concept
            if await self._get_count_from_iri(conn, iri, concept_scheme_table):
                return ConceptScheme
            if await self._get_count_from_iri(conn, iri, correspondence_table):
                return Correspondence
            if await self._get_count_from_iri(conn, iri, association_table):
                return Association
        raise NotFoundError(f"Given IRI `{iri}` is not a known object")

    # Concepts

    async def _get_count_from_iri(self, connection: AsyncConnection, iri: str, table: Table) -> int:
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

    async def concept_scheme_get_all_iris(self) -> list[str]:
        async with self.engine.connect() as conn:
            stmt = select(concept_scheme_table.c.id_)
            result = (await conn.execute(stmt)).scalars()
            await conn.rollback()
        return list(result)

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

    async def known_concept_schemes_for_concept_hierarchical_relationships(
        self, iri: str
    ) -> list[str]:
        """Get list of all concept schemes for all known concepts with relationships to input iri"""
        h_verbs = [v for v in SKOS_HIERARCHICAL_RELATIONSHIP_PREDICATES if v in RelationshipVerbs]

        async with self.engine.connect() as conn:
            join_source = join(
                relationship_table,
                concept_table,
                relationship_table.c.source == concept_table.c.id_,
            )
            join_target = join(
                relationship_table,
                concept_table,
                relationship_table.c.target == concept_table.c.id_,
            )
            stmt = (
                select(concept_table.c.schemes)
                .select_from(join_source)
                .where(
                    relationship_table.c.target == iri,
                    relationship_table.c.predicate.in_(h_verbs),
                )
                .union(
                    select(concept_table.c.schemes)
                    .select_from(join_target)
                    .where(
                        relationship_table.c.source == iri,
                        relationship_table.c.predicate.in_(h_verbs),
                    )
                )
            )
            cursor = (await conn.execute(stmt)).scalars()
            results = {obj["@id"] for result in cursor for obj in result}
            await conn.rollback()
        return sorted(results)

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

    async def relationships_create(self, relationships: list[Relationship]) -> list[Relationship]:
        async with self.engine.connect() as conn:
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
            await conn.commit()
        return relationships

    async def relationships_delete(self, relationships: list[Relationship]) -> int:
        async with self.engine.connect() as conn:
            count = 0
            for rel in relationships:
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

    async def relationship_source_target_share_known_concept_scheme(
        self, relationship: Relationship
    ) -> bool:
        async with self.engine.connect() as conn:
            stmt = select(concept_table.c.schemes).where(
                concept_table.c.id_.in_([relationship.source, relationship.target])
            )
            cursor = (await conn.execute(stmt)).scalars()
            results = [{obj["@id"] for obj in result} for result in cursor]
            await conn.rollback()
        return bool((len(results) < 2) or results[0].intersection(results[1]))

    # Correspondence

    async def correspondence_get(self, iri: str) -> Correspondence:
        async with self.engine.connect() as conn:
            stmt = select(correspondence_table).where(correspondence_table.c.id_ == iri)
            result = (await conn.execute(stmt)).first()
            if not result:
                raise CorrespondenceNotFoundError
            await conn.rollback()
        return Correspondence(**result._mapping)

    async def correspondence_create(self, correspondence: Correspondence) -> Correspondence:
        async with self.engine.connect() as conn:
            count = await self._get_count_from_iri(conn, correspondence.id_, correspondence_table)
            if count:
                raise DuplicateIRI

            await conn.execute(
                insert(correspondence_table),
                [correspondence.to_db_dict()],
            )
            await conn.commit()
        return correspondence

    async def correspondence_update(self, correspondence: Correspondence) -> Correspondence:
        async with self.engine.connect() as conn:
            count = await self._get_count_from_iri(conn, correspondence.id_, correspondence_table)
            if not count:
                raise CorrespondenceNotFoundError

            # Updates to `made_of` can only come via dedicated API calls
            values = correspondence.to_db_dict()
            if "made_ofs" in values:
                del values["made_ofs"]

            await conn.execute(
                update(correspondence_table)
                .where(correspondence_table.c.id_ == correspondence.id_)
                .values(**values)
            )
            await conn.commit()
        return correspondence

    async def correspondence_delete(self, iri: str) -> int:
        async with self.engine.connect() as conn:
            result = await conn.execute(
                delete(correspondence_table).where(correspondence_table.c.id_ == iri)
            )
            await conn.commit()
        return result.rowcount

    async def made_of_add(self, made_of: MadeOf) -> Correspondence:
        corr = await self.correspondence_get(iri=made_of.id_)
        existing = {assoc["@id"] for assoc in corr.made_ofs}
        new = [assoc for assoc in made_of.made_ofs if assoc["@id"] not in existing]
        async with self.engine.connect() as conn:
            await conn.execute(
                update(correspondence_table)
                .where(correspondence_table.c.id_ == made_of.id_)
                .values(made_ofs=sorted(corr.made_ofs + new, key=lambda x: x["@id"]))
            )
            await conn.commit()
        return await self.correspondence_get(iri=made_of.id_)

    async def made_of_remove(self, made_of: MadeOf) -> Correspondence:
        corr = await self.correspondence_get(iri=made_of.id_)
        to_remove = {assoc["@id"] for assoc in made_of.made_ofs}
        remaining = sorted(
            [assoc for assoc in corr.made_ofs if assoc["@id"] not in to_remove],
            key=lambda x: x["@id"],
        )
        async with self.engine.connect() as conn:
            await conn.execute(
                update(correspondence_table)
                .where(correspondence_table.c.id_ == made_of.id_)
                .values(made_ofs=remaining)
            )
            await conn.commit()
        return await self.correspondence_get(iri=made_of.id_)

    # Association

    async def association_get(self, iri: str) -> Association:
        async with self.engine.connect() as conn:
            stmt = select(association_table).where(association_table.c.id_ == iri)
            result = (await conn.execute(stmt)).first()
            if not result:
                raise AssociationNotFoundError
            await conn.rollback()
        return Association(**result._mapping)

    async def association_create(self, association: Association) -> Association:
        async with self.engine.connect() as conn:
            count = await self._get_count_from_iri(conn, association.id_, association_table)
            if count:
                raise DuplicateIRI

            await conn.execute(
                insert(association_table),
                [association.to_db_dict()],
            )
            await conn.commit()
        return association

    async def association_delete(self, iri: str) -> int:
        async with self.engine.connect() as conn:
            result = await conn.execute(
                delete(association_table).where(association_table.c.id_ == iri)
            )
            await conn.commit()
        return result.rowcount
