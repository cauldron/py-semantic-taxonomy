from py_semantic_taxonomy.adapters.routers.request_dto import ConceptScheme


def test_concept_scheme(cn):
    assert ConceptScheme(**cn[2])
