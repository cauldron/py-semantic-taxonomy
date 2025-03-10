import json
from pathlib import Path
from typing import Callable
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from rdflib import Graph
from sqlalchemy import insert
from starlette.datastructures import Headers
from starlette.requests import Request
from testcontainers.postgres import PostgresContainer

import py_semantic_taxonomy
from py_semantic_taxonomy.application.services import GraphService
from py_semantic_taxonomy.domain.entities import Concept, GraphObject
from py_semantic_taxonomy.domain.ports import KOSGraph


@pytest.fixture
def fixtures_dir() -> Path:
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def cn(fixtures_dir: Path) -> object:
    graph = Graph().parse(fixtures_dir / "cn.ttl")
    # Sorted is top level concept, child concept, concept scheme
    data = sorted(json.loads(graph.serialize(format="json-ld")), key=lambda x: x["@id"])

    class CN:
        concept_top = data[0]
        concept_mid = data[1]
        concept_low = data[2]
        scheme = data[3]

    return CN()


@pytest.fixture
def change_note(fixtures_dir: Path) -> dict:
    graph = Graph().parse(fixtures_dir / "change_note.ttl")
    dct = json.loads(graph.serialize(format="json-ld"))
    return [obj for obj in dct if obj["@id"][0] == "_"][0]


@pytest.fixture
def entities(cn) -> list[GraphObject]:
    return [Concept.from_json_ld(cn.concept_top), Concept.from_json_ld(cn.concept_mid)]


@pytest.fixture
def mock_kos_graph() -> AsyncMock:
    return AsyncMock(spec=KOSGraph)


@pytest.fixture
def graph_service(mock_kos_graph) -> GraphService:
    return GraphService(graph=mock_kos_graph)


@pytest.fixture
async def sqlite(monkeypatch) -> None:
    monkeypatch.setenv("PyST_db_backend", "sqlite")


@pytest.fixture
async def postgres(monkeypatch) -> None:
    postgres = PostgresContainer("postgres:16")
    postgres.start()

    monkeypatch.setenv("PyST_db_backend", "postgres")
    monkeypatch.setenv("PyST_db_user", postgres.username)
    monkeypatch.setenv("PyST_db_pass", postgres.password)
    monkeypatch.setenv("PyST_db_host", postgres.get_container_host_ip())
    monkeypatch.setenv("PyST_db_port", postgres.get_exposed_port(5432))
    monkeypatch.setenv("PyST_db_name", postgres.dbname)

    yield

    postgres.stop()


@pytest.fixture
async def cn_db(entities: list) -> None:
    from py_semantic_taxonomy.adapters.persistence.database import (
        drop_db,
        engine,
        init_db,
    )
    from py_semantic_taxonomy.adapters.persistence.tables import concept_table

    await init_db()

    async with engine.connect() as conn:
        await conn.execute(
            insert(concept_table),
            [
                entities[0].to_db_dict(),
                entities[1].to_db_dict(),
            ],
        )
        await conn.commit()

    yield

    # Not sure why this is necessary, the in-memory SQLite should be recreated on each test, but...
    await drop_db()


@pytest.fixture
def client() -> TestClient:
    from py_semantic_taxonomy.app import create_app

    return TestClient(create_app())


@pytest.fixture
def mock_request() -> Callable:
    # Stolen from https://stackoverflow.com/questions/62231022/how-to-programmatically-instantiate-starlettes-request-with-a-body
    def build_request(
        method: str = "GET",
        server: str = "http://example.com",
        path: str = "/",
        headers: dict | None = None,
        body: str | None = None,
    ) -> Request:
        if headers is None:
            headers = {}
        request = Request(
            {
                "type": "http",
                "path": path,
                "headers": Headers(headers).raw,
                "http_version": "1.1",
                "method": method,
                "scheme": "https",
                "client": ("127.0.0.1", 8080),
                "server": (server, 443),
            }
        )
        if body:

            async def request_body():
                return body

            request.body = request_body
        return request

    return build_request
