import pytest

from py_semantic_taxonomy.adapters.routers import admin_router
from py_semantic_taxonomy.cfg import Settings


class _GitLabResponse:
    def __init__(self, status_code: int, payload: dict | None = None):
        self.status_code = status_code
        self._payload = payload or {}

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class _GitLabClient:
    response = _GitLabResponse(200)
    requested_url = ""

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return None

    async def get(self, url, headers):
        self.__class__.requested_url = url
        return self.__class__.response


@pytest.mark.parametrize(
    ("access_level", "expected"),
    [
        (30, False),
        (40, True),
        (50, True),
    ],
)
async def test_gitlab_group_member_requires_minimum_access_level(
    access_level, expected, monkeypatch
):
    monkeypatch.setattr(admin_router.httpx, "AsyncClient", _GitLabClient)
    _GitLabClient.response = _GitLabResponse(200, {"access_level": access_level})

    settings = Settings(
        gitlab_admin_group="parent/group",
        gitlab_admin_min_access_level=40,
    )

    assert await admin_router._gitlab_group_member(123, "token", settings) is expected
    assert "/groups/parent%2Fgroup/members/all/123" in _GitLabClient.requested_url


async def test_gitlab_group_member_returns_false_when_user_is_not_member(monkeypatch):
    monkeypatch.setattr(admin_router.httpx, "AsyncClient", _GitLabClient)
    _GitLabClient.response = _GitLabResponse(404)

    settings = Settings(gitlab_admin_group="parent/group")

    assert await admin_router._gitlab_group_member(123, "token", settings) is False
