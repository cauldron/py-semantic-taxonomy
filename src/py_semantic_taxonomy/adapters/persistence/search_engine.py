from typing import Iterable
from urllib.parse import urlparse

import structlog
import typesense

from py_semantic_taxonomy.domain.entities import SearchResult

logger = structlog.get_logger("py-semantic-taxonomy")


def c(language: str) -> str:
    return f"pyst-concepts-{language}"


class TypesenseSearchEngine:
    def __init__(self, url: str, api_key: str, embedding_model: str):
        url = urlparse(url)
        self.client = typesense.Client(
            {
                "api_key": api_key,
                "nodes": [{"host": url.hostname, "port": url.port, "protocol": url.scheme}],
                "connection_timeout_seconds": 10,
            }
        )
        self.embedding_model = embedding_model

    async def _collection_labels(self) -> list[str]:
        collections = await self.client.collections.retrieve()
        return sorted([obj["name"] for obj in collections])

    async def initialize(self, collections: Iterable[str]) -> None:
        collection_labels = await self._collection_labels()
        logger.info("Existing typesense collections: %s", collection_labels)

        for name in collections:
            if name not in collection_labels:
                logger.info("Creating typesense collection %s", name)
                await self.client.collections.create(
                    {
                        "name": name,
                        "fields": [
                            {"name": "pref_label", "type": "string"},
                            {
                                "name": "pref_label_embedding",
                                "type": "float[]",
                                "embed": {
                                    "from": ["pref_label"],
                                    "model_config": {"model_name": self.embedding_model},
                                },
                            },
                            {"name": "alt_labels", "type": "string[]"},
                            {
                                "name": "alt_label_embedding",
                                "type": "float[]",
                                "embed": {
                                    "from": ["alt_labels"],
                                    "model_config": {"model_name": self.embedding_model},
                                },
                            },
                            {"name": "hidden_labels", "type": "string[]"},
                            {"name": "definition", "type": "string"},
                            {"name": "notation", "type": "string"},
                            {"name": "all_languages_pref_labels", "type": "string[]"},
                            {"name": "url", "type": "string"},
                        ],
                    }
                )

    async def reset(self) -> None:
        logger.warning("Resetting all Typesense collections")
        collection_labels = await self._collection_labels()
        for collection in collection_labels:
            await self.client.collections[collection].delete()

    # Can't use upsert because we have nested arrays:
    # https://github.com/typesense/typesense/issues/1043
    async def create_concept(self, concept: dict, collection: str) -> None:
        logger.debug("Creating concept %s in %s", concept["id"], collection)
        await self.client.collections[collection].documents.create(concept)

    async def update_concept(self, concept: dict, collection: str) -> None:
        logger.debug("Updating concept %s in %s", concept["id"], collection)
        await self.client.collections[collection].documents[concept.pop("id")].update(concept)

    async def delete_concept(self, id_: str, collection: str) -> None:
        logger.debug("Deleting concept %s in %s", id_, collection)
        await self.client.collections[collection].documents[id_].delete({"ignore_not_found": True})

    async def search(
        self, query: str, collection: str, semantic: bool, prefix: bool
    ) -> list[SearchResult]:
        without_semantic = (
            "pref_label,alt_labels,hidden_labels,notation,definition,all_languages_pref_labels"
        )
        with_semantic = "pref_label,pref_label_embedding,alt_labels,hidden_labels,notation,definition,all_languages_pref_labels"

        results = await self.client.collections[collection].documents.search(
            {
                "q": query,
                "query_by": with_semantic if semantic else without_semantic,
                "per_page": 50,
                "prefix": prefix,
                "exclude_fields": "pref_label_embedding",
            }
        )
        return SearchResult.from_typesense_results(results)
