import pytest
from sqlalchemy import insert, select
from sqlalchemy.sql import text

from py_semantic_taxonomy.domain.entities import Concept

# Uncommenting this code will break all tests. I think this is because sqlalchemy uses
# magic to determine when indexes are defined (instead of explicitly adding them to the
# metadata object, like we do with tables), and so this code will add this index *to all
# tests*. This seems to cause a duplicate index error and general sadness.
# The definition isn't that difference from tables (tables take the metadata object,
# indexes take the table), but it feels like this is a side effect, and in any case it
# bit me here.
# The functionality in this test is covered by the next test so it doesn't matter in this
# case.
# @pytest.mark.postgres
# def test_index_definition_gives_correct_sql(postgres):
#     from sqlalchemy import Index
#     from sqlalchemy.dialects import postgresql
#     from sqlalchemy.schema import CreateIndex
#
#     from py_semantic_taxonomy.adapters.persistence.tables import concept_table
#
#     ind = Index(
#         "concept_concept_schemes_index",
#         concept_table.c.schemes,
#         postgresql_using="GIN",
#         postgresql_ops={
#             "schemes": "jsonb_path_ops",
#         },
#     )
#     expected = "CREATE INDEX concept_concept_schemes_index ON concept USING gin (schemes jsonb_path_ops)"
#     assert str(CreateIndex(ind).compile(dialect=postgresql.dialect())) == expected


@pytest.mark.postgres
async def test_concept_concept_scheme_index_created(postgres, cn_db_engine):
    SQL = """SELECT indexdef
        FROM pg_indexes
    WHERE schemaname = 'public'
        AND tablename = 'concept'
        AND indexname = 'concept_concept_schemes_index'"""

    async with cn_db_engine.connect() as conn:
        results = (await conn.execute(text(SQL))).first()

    expected = "CREATE INDEX concept_concept_schemes_index ON public.concept USING gin (schemes jsonb_path_ops)".lower()
    assert results[0].lower() == expected


@pytest.mark.postgres
async def test_concept_concept_scheme_query_uses_index(postgres, cn_plus_db_engine):
    SQL = """EXPLAIN
        SELECT id_
        FROM concept
        WHERE schemes @> '[{"@id": "http://data.europa.eu/xsp/cn2025/cn2025"}]'"""

    async with cn_plus_db_engine.connect() as conn:
        results = (await conn.execute(text(SQL))).fetchall()

    print(results)
    assert results[0][0].startswith("Bitmap Heap Scan on concept")
    assert "Bitmap Index Scan on concept_concept_schemes_index" in results[2][0]


@pytest.mark.postgres
async def test_concept_concept_scheme_results_when_complicated(postgres, cn_db_engine, graph):
    """
    Check to make sure that `@> '"[{'@id': 'foo'}]"'` doesn't exclude references
    to more complete objects.
    """
    from py_semantic_taxonomy.adapters.persistence.tables import concept_table

    concept = Concept(
        id_="http://example.com/meow",
        types=["http://www.w3.org/2004/02/skos/core#Concept"],
        schemes=[
            {"@id": "http://example.com/woof", "animal": "dog", "hair": True},
            {"@id": "http://example.com/pets", "domesticated": True},
        ],
        pref_labels=[],
        status=[],
    )

    async with cn_db_engine.connect() as conn:
        await conn.execute(insert(concept_table), [concept.to_db_dict()])
        await conn.commit()

        stmt = select(concept_table).where(
            concept_table.c.schemes.op("@>")([{"@id": "http://example.com/woof"}])
        )
        result = (await conn.execute(stmt.order_by(concept_table.c.id_))).fetchall()

    result = [Concept(**row._mapping) for row in result]
    assert result[0].id_ == "http://example.com/meow"
    assert len(result) == 1
