from functools import partial
from unittest.mock import AsyncMock
import json
from pathlib import Path

import pytest
from rdflib import Graph

from py_semantic_taxonomy.application.services import GraphService
from py_semantic_taxonomy.domain.ports import KOSGraph
from py_semantic_taxonomy.domain.entities import Concept, GraphObject


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
    from py_semantic_taxonomy.adapters.persistence.engine import create_engine, DatabaseChoice

    engine = await create_engine(database=DatabaseChoice.sqlite, echo=True)
    monkeypatch.setattr("py_semantic_taxonomy.adapters.persistence.session.engine", engine)
