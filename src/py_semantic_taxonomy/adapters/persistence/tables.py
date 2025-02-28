from sqlalchemy import JSON, MetaData, Column, String, Table, Index

metadata_obj = MetaData()


concept_table = Table(
    "concept",
    metadata_obj,
    Column("id_", String, primary_key=True),
    Column("types", JSON, default=[]),
    Column("pref_labels", JSON, default=[]),
    Column("schemes", JSON, default=[]),
    Column("definitions", JSON, default=[]),
    Column("notations", JSON, default=[]),
    Column("alt_labels", JSON, default=[]),
    Column("hidden_labels", JSON, default=[]),
    Column("change_notes", JSON, default=[]),
    Column("history_notes", JSON, default=[]),
    Column("editorial_notes", JSON, default=[]),
    Column("extra", JSON, default={}),
)

Index(
    "concept_id_index",
    concept_table.c.id_
)
