import pytest

from py_semantic_taxonomy.adapters.routers.request_dto import Relationship
from py_semantic_taxonomy.domain.constants import RelationshipVerbs


def test_relationship(relationships):
    r = relationships[0]
    assert Relationship(id_=r.source, broader=[{"@id": r.target}])


def test_relationship_model_dump(relationships):
    r = Relationship(id_=relationships[0].source, broader=[{"@id": relationships[0].target}])
    assert r.model_dump() == {
        "@id": relationships[0].source,
        RelationshipVerbs.broader.value: [{"@id": relationships[0].target}],
    }


def test_relationship_one_relationship_type(relationships):
    with pytest.raises(ValueError) as excinfo:
        Relationship(
            id_=relationships[0].source,
            broader=[{"@id": relationships[0].target}],
            narrower=[{"@id": relationships[1].source}],
        )
    assert excinfo.match("Found multiple relationships")

    with pytest.raises(ValueError) as excinfo:
        Relationship(
            id_=relationships[0].source,
        )
    assert excinfo.match("Found zero relationships")


def test_relationship_self_reference(relationships):
    with pytest.raises(ValueError) as excinfo:
        Relationship(
            id_=relationships[0].source,
            broader=[{"@id": relationships[0].source}],
        )
    assert excinfo.match("Relationship has same source and target")


def test_relationship_multiple_same_type(relationships):
    with pytest.raises(ValueError) as excinfo:
        Relationship(
            id_=relationships[0].source,
            broader=[{"@id": relationships[1].source}, {"@id": relationships[0].target}],
        )
    assert excinfo.match("Found multiple relationships of type `broader`")
