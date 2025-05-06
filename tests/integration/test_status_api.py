import pytest

from py_semantic_taxonomy.domain.url_utils import get_full_api_path
from py_semantic_taxonomy import __version__ as version


@pytest.mark.typesense
async def test_status_api(postgres, typesense, client):
    response = await client.get(
        get_full_api_path("status")
    )
    assert response.status_code == 200
    assert response.json() == {"version": version, "search": True}
