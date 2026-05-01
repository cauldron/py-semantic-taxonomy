from sqlalchemy import DateTime, JSON, Column, Enum, Index, Integer, MetaData, String, Table, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB

from py_semantic_taxonomy.domain.constants import AssociationKind, RelationshipVerbs

BetterJSON = JSON().with_variant(JSONB(), "postgresql")

metadata_obj = MetaData()


concept_table = Table(
    "concept",
    metadata_obj,
    Column("id_", String, primary_key=True, index=True),
    Column("types", BetterJSON, default=[]),
    Column("pref_labels", BetterJSON, default=[]),
    Column("schemes", BetterJSON, default=[]),
    Column("top_concept_of", BetterJSON, default=[]),
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

Index(
    "concept_concept_schemes_index",
    concept_table.c.schemes,
    postgresql_using="GIN",
    postgresql_ops={
        "schemes": "jsonb_path_ops",
    },
)

concept_scheme_table = Table(
    "concept_scheme",
    metadata_obj,
    Column("id_", String, primary_key=True, index=True),
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


relationship_table = Table(
    "relationship",
    metadata_obj,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("source", String, nullable=False, index=True),
    Column("target", String, nullable=False, index=True),
    # https://docs.sqlalchemy.org/en/20/core/type_basics.html#sqlalchemy.types.Enum
    Column("predicate", Enum(RelationshipVerbs, values_callable=lambda x: [i.value for i in x])),
    UniqueConstraint("source", "target", name="relationship_source_target_uniqueness"),
)


correspondence_table = Table(
    "correspondence",
    metadata_obj,
    Column("id_", String, primary_key=True),
    Column("types", BetterJSON, default=[]),
    Column("compares", BetterJSON, default=[]),
    Column("made_ofs", BetterJSON, default=[]),
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

association_table = Table(
    "association",
    metadata_obj,
    Column("id_", String, primary_key=True),
    Column("types", BetterJSON, default=[]),
    Column("source_concepts", BetterJSON, default=[]),
    Column("target_concepts", BetterJSON, default=[]),
    Column("kind", Enum(AssociationKind, values_callable=lambda x: [i.value for i in x])),
    Column("extra", BetterJSON, default={}),
)

contributor_claim_table = Table(
    "contributor_claim",
    metadata_obj,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("kind", String, nullable=False, index=True),
    Column("status", String, nullable=False, index=True, default="pending"),
    Column("title", String, nullable=False),
    Column("target_iri", String, nullable=True, index=True),
    Column("payload", BetterJSON, default={}),
    Column("submitted_by", BetterJSON, default={}),
    Column("review", BetterJSON, default={}),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("reviewed_at", DateTime(timezone=True), nullable=True),
)

Index(
    "association_source_concepts_index",
    association_table.c.source_concepts,
    postgresql_using="GIN",
    postgresql_ops={
        "source_concepts": "jsonb_path_ops",
    },
)
Index(
    "association_target_concepts_index",
    association_table.c.target_concepts,
    postgresql_using="GIN",
    postgresql_ops={
        "target_concepts": "jsonb_path_ops",
    },
)
