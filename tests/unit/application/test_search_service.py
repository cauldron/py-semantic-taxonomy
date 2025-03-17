from unittest.mock import AsyncMock, Mock

import pytest

from py_semantic_taxonomy.application.search_service import TypesenseSearch, c, typesense
from py_semantic_taxonomy.domain.entities import SearchNotConfigured, UnknownLanguage


@pytest.fixture
def ts_client(monkeypatch):
    monkeypatch.setenv("PyST_typesense_url", "http://example.com:1234/")
    monkeypatch.setenv("PyST_typesense_api_key", "abc123")
    monkeypatch.setenv("PyST_languages", '["en", "de"]')

    client = Mock()
    monkeypatch.setattr(typesense, "Client", client)
    return client


async def test_search_init(ts_client):
    ts = TypesenseSearch()
    assert ts.configured
    assert ts.languages == ["en", "de"]
    assert ts.embedding_model == "ts/all-MiniLM-L12-v2"
    given = {
        "api_key": "abc123",
        "nodes": [{"host": "example.com", "port": 1234, "protocol": "http"}],
        "connection_timeout_seconds": 10,
    }
    ts_client.assert_called_with(given)


async def test_search_db_initialization_not_configured(ts_client):
    ts = TypesenseSearch()
    ts.configured = False
    with pytest.raises(SearchNotConfigured):
        await ts.initialize()


async def test_search_db_initialization_no_language_intersection(ts_client):
    ts = TypesenseSearch()
    ts.client.collections = AsyncMock()
    ts.client.collections.retrieve.return_value = [c("de"), c("fr"), c("en")]
    await ts.initialize()
    ts.client.collections.create.assert_not_called()


async def test_search_db_initialization_language_intersection(ts_client):
    ts = TypesenseSearch()
    ts.client.collections = AsyncMock()
    ts.client.collections.retrieve.return_value = [c("de"), c("fr")]
    await ts.initialize()
    ts.client.collections.create.assert_called_once()


async def test_search_reset_not_configured(ts_client):
    ts = TypesenseSearch()
    ts.configured = False
    with pytest.raises(SearchNotConfigured):
        await ts.reset()


@pytest.mark.skip(
    reason="Can't figure out how to get async fixture into `client.collections[collection]`"
)
async def test_search_reset(ts_client):
    ts = TypesenseSearch()
    ts.client.collections = AsyncMock()
    ts.client.collections.retrieve.return_value = [c("de")]
    await ts.reset()
    ts.client.collections.create.assert_called_with(c("de"))


async def test_search_create_concept_not_configured(ts_client):
    ts = TypesenseSearch()
    ts.configured = False
    with pytest.raises(SearchNotConfigured):
        await ts.create_concept(None)


async def test_search_update_concept_not_configured(ts_client):
    ts = TypesenseSearch()
    ts.configured = False
    with pytest.raises(SearchNotConfigured):
        await ts.update_concept(None)


async def test_search_delete_concept_not_configured(ts_client):
    ts = TypesenseSearch()
    ts.configured = False
    with pytest.raises(SearchNotConfigured):
        await ts.delete_concept(None)
