import pytest

from py_semantic_taxonomy.domain.entities import (
    Correspondence,
    CorrespondenceNotFoundError,
)


async def test_get_object_type_correspondence(sqlite, graph):
    corr = await graph.get_object_type(iri="http://pyst-tests.ninja/correspondence/cn2023_cn2024")
    assert corr is Correspondence, "Wrong result type"


async def test_get_correspondence(sqlite, entities, graph):
    corr = await graph.correspondence_get(
        iri="http://pyst-tests.ninja/correspondence/cn2023_cn2024"
    )
    assert isinstance(corr, Correspondence), "Wrong result type"
    assert corr == entities[3]  # Check all data attributes correct


async def test_get_correspondence_not_found(sqlite, graph):
    with pytest.raises(CorrespondenceNotFoundError):
        await graph.correspondence_get(iri="http://pyst-tests.ninja/correspondence/missing")


async def test_create_correspondence(sqlite, cn, entities, graph):
    cn.correspondence["@id"] = "http://pyst-tests.ninja/correspondence/new"
    expected = Correspondence.from_json_ld(cn.correspondence)

    response = await graph.correspondence_create(correspondence=expected)
    assert isinstance(response, Correspondence), "Wrong result type"
    assert response == expected, "Data attributes from database differ"

    given = await graph.correspondence_get(iri=cn.correspondence["@id"])
    assert given == expected, "Data attributes from database differ"


# async def test_create_correspondence_duplicate(sqlite, cn, entities, graph):
#     with pytest.raises(DuplicateIRI):
#         await graph.correspondence_create(correspondence=correspondence.from_json_ld(cn.correspondence_top))


# async def test_update_correspondence(sqlite, cn, entities, graph):
#     expected = correspondence.from_json_ld(cn.correspondence_top)
#     expected.alt_labels = [{"@value": "Dream a little dream", "@language": "en"}]

#     response = await graph.correspondence_update(correspondence=expected)
#     assert isinstance(response, correspondence), "Wrong result type"
#     assert response == expected, "Data attributes from database differ"

#     given = await graph.correspondence_get(iri=cn.correspondence_top["@id"])
#     assert given == expected, "Data attributes from database differ"


# async def test_update_correspondence_missing(sqlite, cn, entities, graph):
#     expected = correspondence.from_json_ld(cn.correspondence_low)
#     with pytest.raises(correspondenceNotFoundError):
#         await graph.correspondence_update(correspondence=expected)


# async def test_delete_correspondence(sqlite, cn, entities, graph):
#     response = await graph.correspondence_delete(iri=cn.correspondence_mid["@id"])
#     assert response == 1, "Wrong number of deleted correspondences"

#     response = await graph.correspondence_delete(iri=cn.correspondence_mid["@id"])
#     assert response == 0, "Wrong number of deleted correspondences"
