from py_semantic_taxonomy.domain.constants import API_VERSION_PREFIX, APIPaths
from py_semantic_taxonomy.domain.url_utils import get_full_api_path


def test_get_full_api_path_simple():
    assert get_full_api_path("concept_all") == (API_VERSION_PREFIX + str(APIPaths.concept_all))


def test_get_full_api_path_interpolation():
    assert get_full_api_path("concept", iri="https://www.example.com/") == (
        API_VERSION_PREFIX + str(APIPaths.concept_all) + "https%3A//www.example.com/"
    )
