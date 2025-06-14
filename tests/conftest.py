import json
from pathlib import Path
from typing import Callable
from unittest.mock import AsyncMock, Mock

import httpx
import pytest
from faker import Faker
from fastapi.testclient import TestClient
from rdflib import Graph
from sqlalchemy import insert
from starlette.datastructures import Headers
from starlette.requests import Request
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs
from testcontainers.postgres import PostgresContainer

from py_semantic_taxonomy.application.graph_service import GraphService
from py_semantic_taxonomy.application.search_service import SearchService
from py_semantic_taxonomy.domain.constants import RelationshipVerbs
from py_semantic_taxonomy.domain.entities import (
    Association,
    Concept,
    ConceptScheme,
    Correspondence,
    GraphObject,
    MadeOf,
    Relationship,
)
from py_semantic_taxonomy.domain.ports import KOSGraphDatabase, SearchEngine
from py_semantic_taxonomy.domain.ports import SearchService as SearchServicePort


@pytest.fixture
def fixtures_dir() -> Path:
    return Path(__file__).parent / "fixtures"


@pytest.fixture(autouse=True)
def auth_token(monkeypatch):
    monkeypatch.setenv("PyST_auth_token", "testrunner")


@pytest.fixture
def cn(fixtures_dir: Path) -> object:
    graph = Graph().parse(fixtures_dir / "cn.ttl")
    # Sorted is top level concept, child concept, concept scheme
    data = sorted(json.loads(graph.serialize(format="json-ld")), key=lambda x: x["@id"])

    class CN:
        concept_top = data[6]
        concept_mid = data[7]
        concept_low = data[8]
        scheme = data[9]
        correspondence = data[2]
        concept_2023_top = data[0]
        concept_2023_low = data[1]
        scheme_2023 = data[3]
        association_low = data[4]
        association_top = data[5]

    return CN()


@pytest.fixture
def change_note(fixtures_dir: Path) -> dict:
    graph = Graph().parse(fixtures_dir / "change_note.ttl")
    dct = json.loads(graph.serialize(format="json-ld"))
    return [obj for obj in dct if obj["@id"][0] == "_"][0]


@pytest.fixture
def relationships(fixtures_dir: Path) -> list[Relationship]:
    graph = Graph().parse(fixtures_dir / "cn.ttl")
    mapping = {elem.value: elem for elem in RelationshipVerbs}
    return sorted(
        [
            Relationship(source=str(s), target=str(o), predicate=mapping[str(p)])
            for s, p, o in graph
            if str(p) in mapping
        ],
        key=lambda x: (x.source, x.target),
    )


@pytest.fixture
def made_of() -> MadeOf:
    return MadeOf(
        id_="http://data.europa.eu/xsp/cn2023/CN2023_CN2024",
        made_ofs=[
            {"@id": "http://data.europa.eu/xsp/cn2023/top_level_association"},
            {"@id": "http://data.europa.eu/xsp/cn2023/lower_association"},
        ],
    )


@pytest.fixture
def entities(cn) -> list[GraphObject]:
    return [
        Concept.from_json_ld(cn.concept_top),
        Concept.from_json_ld(cn.concept_mid),
        ConceptScheme.from_json_ld(cn.scheme),
        Correspondence.from_json_ld(cn.correspondence),
        ConceptScheme.from_json_ld(cn.scheme_2023),
        Concept.from_json_ld(cn.concept_2023_top),
        Concept.from_json_ld(cn.concept_2023_low),
        Association.from_json_ld(cn.association_low),
        Association.from_json_ld(cn.association_top),
    ]


@pytest.fixture
def mock_kos_graph() -> AsyncMock:
    return AsyncMock(spec=KOSGraphDatabase)


@pytest.fixture
def mock_search_engine() -> Mock:
    return AsyncMock(spec=SearchEngine)


@pytest.fixture()
def search_service(mock_search_engine, monkeypatch) -> SearchService:
    monkeypatch.setenv("PyST_typesense_url", "ts_url_test")
    monkeypatch.setenv("PyST_typesense_api_key", "ts_api_key_test")
    monkeypatch.setenv("PyST_typesense_embedding_model", "ts_embedding_test")
    monkeypatch.setenv("PyST_languages", '["en", "de"]')
    return SearchService(engine=mock_search_engine)


@pytest.fixture
def graph_service(mock_kos_graph, search_service) -> GraphService:
    return GraphService(graph=mock_kos_graph, search=AsyncMock(spec=SearchServicePort))


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
async def cn_db_engine(entities: list, relationships: list):
    from py_semantic_taxonomy.adapters.persistence.database import (
        create_engine,
        drop_db,
        init_db,
    )
    from py_semantic_taxonomy.adapters.persistence.tables import (
        association_table,
        concept_scheme_table,
        concept_table,
        correspondence_table,
        relationship_table,
    )

    engine = create_engine()
    await init_db(engine)

    async with engine.connect() as conn:
        await conn.execute(
            insert(concept_scheme_table),
            [
                entities[2].to_db_dict(),
                entities[4].to_db_dict(),
            ],
        )
        await conn.execute(
            insert(concept_table),
            [
                entities[0].to_db_dict(),
                entities[1].to_db_dict(),
                entities[5].to_db_dict(),
                entities[6].to_db_dict(),
            ],
        )
        await conn.execute(
            insert(correspondence_table),
            [
                entities[3].to_db_dict(),
            ],
        )
        await conn.execute(insert(relationship_table), [obj.to_db_dict() for obj in relationships])
        await conn.execute(
            insert(association_table),
            [
                entities[7].to_db_dict(),
                entities[8].to_db_dict(),
            ],
        )
        await conn.commit()

    yield engine

    # Not sure why this is necessary, the in-memory SQLite should be recreated on each test, but...
    await drop_db(engine)


@pytest.fixture
async def cn_plus_db_engine(cn_db_engine, entities):
    from py_semantic_taxonomy.adapters.persistence.tables import concept_table

    fake = Faker()

    def fake_concept():
        return {
            "id_": "http://example.com/" + fake.unique.doi(),
            "types": ["http://www.w3.org/2004/02/skos/core#Concept"],
            "pref_labels": [{"@language": "en", "@value": fake.name()}],
            "schemes": [{"@id": entities[2].id_}],
            "top_concept_of": [],
            "definitions": [],
            "notations": [],
            "alt_labels": [],
            "hidden_labels": [],
            "change_notes": [],
            "editorial_notes": [],
            "extra": {},
            "status": [],
        }

    async with cn_db_engine.connect() as conn:
        for x in range(5):
            await conn.execute(insert(concept_table), [fake_concept() for i in range(500)])
        await conn.commit()

    yield cn_db_engine


@pytest.fixture
def typesense_container(monkeypatch, test_password: str = "123abc"):
    container = DockerContainer("typesense/typesense:28.0")
    container.with_exposed_ports(8108)
    # Giving the API key in `with_command` in a pytest fixture doesn't work...
    container.with_env("TYPESENSE_API_KEY", test_password)
    container.with_command("--data-dir /home --enable-cors")
    container.start()
    wait_for_logs(container, "Peer refresh succeeded")

    ip = container.get_container_host_ip()
    port = container.get_exposed_port(8108)

    check_response = httpx.get(f"http://{ip}:{port}/health")
    if not check_response.status_code == 200:
        raise OSError("Typesense container can't start")

    monkeypatch.setenv("PyST_typesense_url", f"http://{ip}:{port}")
    monkeypatch.setenv("PyST_typesense_api_key", test_password)
    monkeypatch.setenv("PyST_languages", '["en", "de"]')

    yield

    container.stop()


@pytest.fixture
async def typesense(typesense_container, entities):
    from py_semantic_taxonomy.dependencies import get_search_service

    ts = get_search_service()
    await ts.initialize()

    for i in [0, 1, 5, 6]:
        await ts.create_concept(entities[i])


@pytest.fixture
async def typesense_container_with_prefix(monkeypatch, test_password: str = "123abc"):
    container = DockerContainer("typesense/typesense:28.0")
    container.with_exposed_ports(8108)
    # Giving the API key in `with_command` in a pytest fixture doesn't work...
    container.with_env("TYPESENSE_API_KEY", test_password)
    container.with_command("--data-dir /home --enable-cors")
    container.start()
    wait_for_logs(container, "Peer refresh succeeded")

    ip = container.get_container_host_ip()
    port = container.get_exposed_port(8108)

    check_response = httpx.get(f"http://{ip}:{port}/health")
    if not check_response.status_code == 200:
        raise OSError("Typesense container can't start")

    monkeypatch.setenv("PyST_typesense_url", f"http://{ip}:{port}")
    monkeypatch.setenv("PyST_typesense_api_key", test_password)
    monkeypatch.setenv("PyST_languages", '["en", "de"]')
    monkeypatch.setenv("PyST_typesense_prefix", "prefixtest")

    yield

    container.stop()


@pytest.fixture
async def typesense_with_prefix(typesense_container_with_prefix, entities):
    from py_semantic_taxonomy.dependencies import get_search_service

    ts = get_search_service()
    await ts.initialize()

    for i in [0, 1, 5, 6]:
        await ts.create_concept(entities[i])


@pytest.fixture
async def client() -> TestClient:
    from httpx import ASGITransport, AsyncClient

    from py_semantic_taxonomy.app import test_app

    async with AsyncClient(
        transport=ASGITransport(app=test_app()),
        base_url="http://test.ninja",
        headers={"X-PyST-Auth-Token": "testrunner"},
    ) as ac:
        yield ac


@pytest.fixture
async def anonymous_client() -> TestClient:
    from httpx import ASGITransport, AsyncClient

    from py_semantic_taxonomy.app import test_app

    async with AsyncClient(
        transport=ASGITransport(app=test_app()),
        base_url="http://test.ninja",
    ) as ac:
        yield ac


@pytest.fixture
def mock_request() -> Callable:
    # Stolen from https://stackoverflow.com/questions/62231022/how-to-programmatically-instantiate-starlettes-request-with-a-body
    def build_request(
        method: str = "GET",
        server: str = "http://example.com",
        path: str = "/",
        headers: dict | None = None,
        body: str | None = None,
        query_string: str = "",
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
                "query_string": query_string,
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


@pytest.fixture
def graph(cn_db_engine):
    # Defer import until environment is patched
    from py_semantic_taxonomy.adapters.persistence.graph import PostgresKOSGraphDatabase

    return PostgresKOSGraphDatabase(engine=cn_db_engine)
