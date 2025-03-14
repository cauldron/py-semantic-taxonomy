from sqlalchemy import JSON, Column, Enum, Index, Integer, MetaData, String, Table, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB

from py_semantic_taxonomy.domain.constants import RelationshipVerbs

BetterJSON = JSON().with_variant(JSONB(), "postgresql")

metadata_obj = MetaData()


concept_table = Table(
    "concept",
    metadata_obj,
    Column("id_", String, primary_key=True),
    Column("types", BetterJSON, default=[]),
    Column("pref_labels", BetterJSON, default=[]),
    Column("schemes", BetterJSON, default=[]),
    Column("definitions", BetterJSON, default=[]),
    Column("notations", BetterJSON, default=[]),
    Column("alt_labels", BetterJSON, default=[]),
    Column("hidden_labels", BetterJSON, default=[]),
    Column("change_notes", BetterJSON, default=[]),
    Column("history_notes", BetterJSON, default=[]),
    Column("editorial_notes", BetterJSON, default=[]),
    Column("status", BetterJSON, default=[]),
    Column("extra", BetterJSON, default={}),
)

Index("concept_id_index", concept_table.c.id_)


concept_scheme_table = Table(
    "concept_scheme",
    metadata_obj,
    Column("id_", String, primary_key=True),
    Column("types", BetterJSON, default=[]),
    Column("pref_labels", BetterJSON, default=[]),
    Column("created", BetterJSON, default=[]),
    Column("creators", BetterJSON, default=[]),
    Column("version", BetterJSON, default=[]),
    Column("definitions", BetterJSON, default=[]),
    Column("notations", BetterJSON, default=[]),
    Column("change_notes", BetterJSON, default=[]),
    Column("history_notes", BetterJSON, default=[]),
    Column("editorial_notes", BetterJSON, default=[]),
    Column("status", BetterJSON, default=[]),
    Column("extra", BetterJSON, default={}),
)

Index("concept_scheme_id_index", concept_scheme_table.c.id_)

relationship_table = Table(
    "relationship",
    metadata_obj,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("source", String, nullable=False),
    Column("target", String, nullable=False),
    # https://docs.sqlalchemy.org/en/20/core/type_basics.html#sqlalchemy.types.Enum
    Column("predicate", Enum(RelationshipVerbs, values_callable=lambda x: [i.value for i in x])),
    UniqueConstraint("source", "target", name="relationship_source_target_uniqueness"),
)

Index("relationship_source_index", relationship_table.c.source)
Index("relationship_target_index", relationship_table.c.target)
