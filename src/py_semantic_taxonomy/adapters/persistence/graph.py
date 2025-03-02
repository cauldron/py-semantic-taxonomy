from sqlalchemy import func, insert, select

from py_semantic_taxonomy.adapters.persistence.database import engine
from py_semantic_taxonomy.adapters.persistence.tables import concept_table
from py_semantic_taxonomy.domain.entities import (
    Concept,
    ConceptNotFoundError,
    DuplicateIRI,
    GraphObject,
)


class PostgresKOSGraph:
    async def get_concept(self, iri: str) -> Concept:
        async with engine.connect() as conn:
            stmt = select(concept_table).where(concept_table.c.id_ == iri)
            result = (await conn.execute(stmt)).first()
            if not result:
                raise ConceptNotFoundError
            return Concept(**result._mapping)

    async def get_object_type(self, iri: str) -> GraphObject:
        async with engine.connect() as conn:
            stmt = select(func.count("*")).where(concept_table.c.id_ == iri)
            # TBD: This is ugly
            result = (await conn.execute(stmt)).first()[0]
            if result:
                return Concept

    async def create_concept(self, concept: Concept) -> Concept:
        async with engine.connect() as conn:
            await conn.execute(
                insert(concept_table),
                [concept.to_db_dict()],
            )
            await conn.commit()
        return concept
