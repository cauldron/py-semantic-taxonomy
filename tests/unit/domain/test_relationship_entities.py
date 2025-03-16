from py_semantic_taxonomy.domain.constants import RelationshipVerbs
from py_semantic_taxonomy.domain.entities import Relationship


def test_relationship_to_db_dict(relationships):
    first = relationships[3]

    assert first.to_db_dict() == dict(
        source="http://data.europa.eu/xsp/cn2024/010021000090",
        target="http://data.europa.eu/xsp/cn2024/010011000090",
        predicate=RelationshipVerbs.broader,
    ), "Conversion to database dict failed"


def test_relationship_to_json_ld(relationships):
    first = relationships[3]

    assert first.to_json_ld() == {
        "@id": "http://data.europa.eu/xsp/cn2024/010021000090",
        RelationshipVerbs.broader.value: [{"@id": "http://data.europa.eu/xsp/cn2024/010011000090"}],
    }, "Conversion to JSON-LD failed"


def test_relationship_from_json_ld(relationships):
    given = Relationship.from_json_ld(
        {
            "@id": "a",
            RelationshipVerbs.broader.value: [{"@id": "b"}],
        }
    )
    assert given == [Relationship(source="a", target="b", predicate=RelationshipVerbs.broader)]


def test_relationship_from_json_ld_multiple_identical(relationships):
    given = Relationship.from_json_ld(
        {
            "@id": "a",
            RelationshipVerbs.broader.value: [{"@id": "b"}, {"@id": "b"}],
        }
    )
    assert given == [Relationship(source="a", target="b", predicate=RelationshipVerbs.broader)]


def test_relationship_from_json_ld_multiple(relationships):
    given = Relationship.from_json_ld(
        {
            "@id": "a",
            RelationshipVerbs.broader.value: [{"@id": "b"}, {"@id": "d"}],
            RelationshipVerbs.exact_match.value: [{"@id": "c"}],
        }
    )
    assert given == [
        Relationship(source="a", target="b", predicate=RelationshipVerbs.broader),
        Relationship(source="a", target="c", predicate=RelationshipVerbs.exact_match),
        Relationship(source="a", target="d", predicate=RelationshipVerbs.broader),
    ]


def test_relationship_from_json_ld_narrower(relationships):
    given = Relationship.from_json_ld(
        {
            "@id": "b",
            RelationshipVerbs.narrower.value: [{"@id": "a"}],
        }
    )
    assert given == [Relationship(source="a", target="b", predicate=RelationshipVerbs.broader)]


def test_relationship_from_json_ld_list(relationships):
    given = Relationship.from_json_ld_list(
        [
            {
                "@id": "a",
                RelationshipVerbs.broader.value: [{"@id": "b"}, {"@id": "d"}],
                RelationshipVerbs.exact_match.value: [{"@id": "c"}],
            },
            {
                "@id": "b",
                RelationshipVerbs.narrower.value: [{"@id": "e"}],
            },
            {
                "@id": "e",
                RelationshipVerbs.broader.value: [{"@id": "b"}],
            },
        ]
    )
    assert given == [
        Relationship(source="a", target="b", predicate=RelationshipVerbs.broader),
        Relationship(source="a", target="c", predicate=RelationshipVerbs.exact_match),
        Relationship(source="a", target="d", predicate=RelationshipVerbs.broader),
        Relationship(source="e", target="b", predicate=RelationshipVerbs.broader),
    ]
