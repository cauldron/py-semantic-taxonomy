import json
from pathlib import Path

import pytest
from rdflib import Graph

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def cn() -> dict:
    graph = Graph().parse(FIXTURES_DIR / "cn.ttl")
    # Sorted is top level concept, child concept, concept scheme
    return sorted(json.loads(graph.serialize(format="json-ld")), key=lambda x: x["@id"])
