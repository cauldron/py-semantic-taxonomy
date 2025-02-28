import json
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from rdflib import Graph
from sqlalchemy import insert

from py_semantic_taxonomy.application.services import GraphService
from py_semantic_taxonomy.domain.entities import Concept, GraphObject
from py_semantic_taxonomy.domain.ports import KOSGraph


@pytest.fixture
def fixtures_dir() -> Path:
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def cn(fixtures_dir: Path) -> list:
    graph = Graph().parse(fixtures_dir / "cn.ttl")
    # Sorted is top level concept, child concept, concept scheme
    return sorted(json.loads(graph.serialize(format="json-ld")), key=lambda x: x["@id"])


@pytest.fixture
def change_note(fixtures_dir: Path) -> dict:
    graph = Graph().parse(fixtures_dir / "change_note.ttl")
    dct = json.loads(graph.serialize(format="json-ld"))
    return [obj for obj in dct if obj["@id"][0] == "_"][0]


@pytest.fixture
def entities(cn) -> list[GraphObject]:
    return [Concept.from_json_ld(cn[0]), Concept.from_json_ld(cn[1])]


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
async def cn_db(entities: list) -> None:
    from py_semantic_taxonomy.adapters.persistence.database import (
        engine,
        drop_db,
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
            ]
        )
        await conn.commit()

    yield

    # Not sure why this is necessary, the in-memory SQLite should be recreated on each test, but...
    await drop_db()


@pytest.fixture
def client() -> TestClient:
    from py_semantic_taxonomy.app import create_app

    return TestClient(create_app())
