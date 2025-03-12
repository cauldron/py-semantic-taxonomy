from sqlalchemy import JSON, Column, Index, MetaData, String, Table
from sqlalchemy.dialects.postgresql import JSONB

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
    Column("extra", BetterJSON, default={}),
)

Index("concept_scheme_id_index", concept_scheme_table.c.id_)
