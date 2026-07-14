from py_semantic_taxonomy import __version__ as version
from py_semantic_taxonomy.adapters.routers.api_router import server_status


class FakeSearchService:
    def __init__(self, configured: bool):
        self.configured = configured

    def is_configured(self) -> bool:
        return self.configured


async def test_server_status_search_configured():
    result = await server_status(search=FakeSearchService(True))
    assert result.version == version
    assert result.search is True


async def test_server_status_search_not_configured():
    result = await server_status(search=FakeSearchService(False))
    assert result.search is False
