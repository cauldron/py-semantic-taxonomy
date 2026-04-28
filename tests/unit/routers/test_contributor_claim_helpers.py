import pytest

from py_semantic_taxonomy.adapters.routers import contributor_router
from py_semantic_taxonomy.domain.constants import RelationshipVerbs


def test_build_claim_payload_uses_guided_concept_data():
    payload, mode = contributor_router._build_claim_payload(
        "add_concept",
        rationale="Need a new concept",
        form_data={
            "concept_iri": "http://example.com/concepts/new",
            "scheme_iri": "http://example.com/schemes/main",
            "concept_language": "en",
            "concept_label": "New concept",
            "concept_notation": "NEW",
            "concept_definition": "A useful new concept",
            "broader_iri": "http://example.com/concepts/root",
        },
        payload_text="",
        csv_text="",
        csv_file_name="",
        csv_import_name="",
    )

    assert mode == "guided"
    assert payload["rationale"] == "Need a new concept"
    assert payload["change"]["entity_type"] == "concept"
    assert payload["change"]["concept"]["pref_label"]["value"] == "New concept"
    assert payload["change"]["broader_iri"] == "http://example.com/concepts/root"


def test_build_claim_payload_uses_csv_rows_for_bulk_import():
    payload, mode = contributor_router._build_claim_payload(
        "bulk_tree_import",
        rationale="Import a tree",
        form_data={},
        payload_text="",
        csv_text="code,parent_code,name,level\nROOT,,Root,0\nCHILD,ROOT,Child,1\n",
        csv_file_name="tree_demo.csv",
        csv_import_name="demo-tree",
    )

    assert mode == "csv"
    assert payload["change"]["import_kind"] == "tree"
    assert payload["change"]["file_name"] == "tree_demo.csv"
    assert payload["change"]["columns"] == ["code", "parent_code", "name", "level"]
    assert payload["change"]["rows"][1]["parent_code"] == "ROOT"


def test_build_claim_payload_rejects_raw_json_submission():
    with pytest.raises(ValueError, match="no longer supported"):
        contributor_router._build_claim_payload(
            "add_relationship",
            rationale="Override structured fields",
            form_data={
                "relationship_source_iri": "http://example.com/a",
                "relationship_target_iri": "http://example.com/b",
                "relationship_predicate": str(RelationshipVerbs.broader),
            },
            payload_text='{"custom": true}',
            csv_text="",
            csv_file_name="",
            csv_import_name="",
        )


def test_parse_csv_rows_requires_header_and_data():
    with pytest.raises(ValueError, match="header row"):
        contributor_router._parse_csv_rows("")

    with pytest.raises(ValueError, match="at least one data row"):
        contributor_router._parse_csv_rows("code,name\n")
