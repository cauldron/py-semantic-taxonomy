from dataclasses import fields

from py_semantic_taxonomy.adapters.routers import request_dto as request
from py_semantic_taxonomy.adapters.routers import response_dto as response
from py_semantic_taxonomy.domain.constants import AssociationKind
from py_semantic_taxonomy.domain.entities import Association


def test_association_post_init():
    assoc = Association(
        id_="http://example.com/a/one",
        types=["http://rdf-vocabulary.ddialliance.org/xkos#ConceptAssociation"],
        source_concepts=[
            {
                "@id": "http://example.com/c/one",
            }
        ],
        target_concepts=[
            {
                "@id": "http://example.com/c/two",
            }
        ],
    )
    assert assoc.kind == AssociationKind.simple

    assoc = Association(
        id_="http://example.com/a/one",
        types=["http://rdf-vocabulary.ddialliance.org/xkos#ConceptAssociation"],
        source_concepts=[
            {
                "@id": "http://example.com/c/one",
            },
            {
                "@id": "http://example.com/c/three",
            },
        ],
        target_concepts=[
            {
                "@id": "http://example.com/c/two",
            }
        ],
    )
    assert assoc.kind == AssociationKind.conditional


def test_association_domain_request_dto_same_fields():
    domain_fields = {f.name for f in fields(Association)}
    request_fields = set(request.Association.model_fields)
    assert domain_fields.difference(request_fields) == {
        "extra",
        "kind",
    }, "Request validation and domain `Association` model fields differ"
    assert not request_fields.difference(
        domain_fields
    ), "Request validation and domain `Association` model fields differ"


def test_association_domain_response_dto_same_fields():
    domain_fields = {f.name for f in fields(Association)}
    response_fields = set(response.Association.model_fields)
    assert domain_fields.difference(response_fields) == {
        "extra",
        "kind",
    }, "Response validation and domain `Association` model fields differ"
    assert not response_fields.difference(
        domain_fields
    ), "Response validation and domain `Association` model fields differ"


def test_association_to_db_dict(cn):
    given = Association.from_json_ld(cn.association_top).to_db_dict()
    expected = dict(
        id_="http://data.europa.eu/xsp/cn2023/top_level_association",
        types=["http://rdf-vocabulary.ddialliance.org/xkos#ConceptAssociation"],
        kind=AssociationKind.simple,
        extra={},
        source_concepts=[
            {
                "@id": "http://data.europa.eu/xsp/cn2023/010011000090",
            }
        ],
        target_concepts=[
            {
                "@id": "http://data.europa.eu/xsp/cn2024/010011000090",
            }
        ],
    )
    assert given == expected, "Conversion to database dict failed"


def test_association_from_json_ld(cn):
    given = Association.from_json_ld(cn.association_top)
    expected = Association(
        id_="http://data.europa.eu/xsp/cn2023/top_level_association",
        types=["http://rdf-vocabulary.ddialliance.org/xkos#ConceptAssociation"],
        source_concepts=[
            {
                "@id": "http://data.europa.eu/xsp/cn2023/010011000090",
            }
        ],
        target_concepts=[
            {
                "@id": "http://data.europa.eu/xsp/cn2024/010011000090",
            }
        ],
    )
    assert given == expected, "Conversion from JSON-LD failed"


def test_association_to_json_ld(cn):
    cn.association_top["foo"] = "bar"

    assert Association.from_json_ld(cn.association_top).extra["foo"] == "bar"
    given = Association.from_json_ld(cn.association_top).to_json_ld()
    assert given["foo"] == "bar"
    assert given == cn.association_top, "Conversion to JSON-LD failed"
