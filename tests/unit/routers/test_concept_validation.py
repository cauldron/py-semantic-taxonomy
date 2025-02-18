from py_semantic_taxonomy.adapters.routers.request_dto import Concept


def test_top_level_concept(cn):
    assert Concept(**cn[0])


def test_child_concept(cn):
    assert Concept(**cn[1])
