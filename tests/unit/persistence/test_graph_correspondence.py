import pytest

from py_semantic_taxonomy.domain.entities import (
    Correspondence,
    CorrespondenceNotFoundError,
    MadeOf,
)


async def test_get_object_type_correspondence(sqlite, graph):
    corr = await graph.get_object_type(iri="http://data.europa.eu/xsp/cn2023/CN2023_CN2024")
    assert corr is Correspondence, "Wrong result type"


async def test_get_correspondence(sqlite, entities, graph):
    corr = await graph.correspondence_get(iri="http://data.europa.eu/xsp/cn2023/CN2023_CN2024")
    assert isinstance(corr, Correspondence), "Wrong result type"
    assert corr == entities[3]  # Check all data attributes correct


async def test_get_correspondence_not_found(sqlite, graph):
    with pytest.raises(CorrespondenceNotFoundError):
        await graph.correspondence_get(iri="http://pyst-tests.ninja/correspondence/missing")


async def test_get_all_correspondence(sqlite, entities, graph):
    corr = await graph.correspondence_get_all()
    assert isinstance(corr, list), "Wrong result type"
    assert len(corr) == 1, "Wrong number of results"
    assert isinstance(corr[0], Correspondence), "Wrong result element type"
    assert corr[0] == entities[3]  # Check all data attributes correct


async def test_create_correspondence(sqlite, cn, graph):
    cn.correspondence["@id"] = "http://pyst-tests.ninja/correspondence/new"
    expected = Correspondence.from_json_ld(cn.correspondence)

    response = await graph.correspondence_create(correspondence=expected)
    assert isinstance(response, Correspondence), "Wrong result type"
    assert response == expected, "Data attributes from database differ"

    given = await graph.correspondence_get(iri=cn.correspondence["@id"])
    assert given == expected, "Data attributes from database differ"


async def test_update_correspondence(sqlite, cn, graph):
    expected = Correspondence.from_json_ld(cn.correspondence)
    # This will be ignored
    expected.made_of = ["foo", "bar"]

    response = await graph.correspondence_update(correspondence=expected)
    assert isinstance(response, Correspondence), "Wrong result type"

    expected.made_of = []
    assert response == expected, "Data attributes from database differ"

    given = await graph.correspondence_get(iri=cn.correspondence["@id"])
    assert given == expected, "Data attributes from database differ"


async def test_update_correspondence_missing(sqlite, cn, graph):
    expected = Correspondence.from_json_ld(cn.correspondence)
    expected.id_ = "http://pyst-tests.ninja/correspondence/missing"
    with pytest.raises(CorrespondenceNotFoundError):
        await graph.correspondence_update(correspondence=expected)


async def test_delete_correspondence(sqlite, cn, graph):
    response = await graph.correspondence_delete(iri=cn.correspondence["@id"])
    assert response == 1, "Wrong number of deleted correspondences"

    response = await graph.correspondence_delete(iri=cn.correspondence["@id"])
    assert response == 0, "Wrong number of deleted correspondences"


async def test_add_made_ofs(sqlite, made_of, graph):
    corr = await graph.correspondence_get(iri="http://data.europa.eu/xsp/cn2023/CN2023_CN2024")
    assert not corr.made_ofs

    corr = await graph.made_of_add(made_of)
    assert corr.id_ == "http://data.europa.eu/xsp/cn2023/CN2023_CN2024"
    assert sorted(corr.made_ofs, key=lambda x: x["@id"]) == sorted(
        made_of.made_ofs, key=lambda x: x["@id"]
    )

    corr = await graph.correspondence_get(iri=corr.id_)
    assert len(corr.made_ofs) == 2


async def test_remove_made_ofs(sqlite, made_of, graph):
    corr = await graph.correspondence_get(iri="http://data.europa.eu/xsp/cn2023/CN2023_CN2024")
    assert not corr.made_ofs

    corr = await graph.made_of_add(made_of)
    assert len(corr.made_ofs) == 2

    new = MadeOf(
        id_=corr.id_,
        made_ofs=[
            {"@id": "http://data.europa.eu/xsp/cn2023/top_level_association"},
        ],
    )

    corr = await graph.made_of_remove(new)
    assert corr.made_ofs == [{"@id": "http://data.europa.eu/xsp/cn2023/lower_association"}]

    corr = await graph.correspondence_get(iri="http://data.europa.eu/xsp/cn2023/CN2023_CN2024")
    assert corr.made_ofs == [{"@id": "http://data.europa.eu/xsp/cn2023/lower_association"}]


async def test_update_correspondence_doesnt_overwrite_existing_made_ofs(sqlite, made_of, graph):
    corr = await graph.made_of_add(made_of)
    assert len(corr.made_ofs) == 2

    corr.made_ofs = []
    await graph.correspondence_update(corr)

    corr = await graph.correspondence_get(iri="http://data.europa.eu/xsp/cn2023/CN2023_CN2024")
    assert len(corr.made_ofs) == 2
