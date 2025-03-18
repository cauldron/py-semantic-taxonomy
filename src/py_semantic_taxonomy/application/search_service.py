import functools
from urllib.parse import quote, urlparse

import structlog
import typesense

from py_semantic_taxonomy.cfg import get_settings
from py_semantic_taxonomy.domain.entities import (
    Concept,
    SearchNotConfigured,
    SearchResult,
    UnknownLanguage,
)

logger = structlog.get_logger("py-semantic-taxonomy")


def c(language: str) -> str:
    return f"pyst-concepts-{language}"


class TypesenseSearch:
    def __init__(self):
        settings = get_settings()

        if settings.typesense_url == "missing" or not settings.typesense_url:
            self.configured = False
            logger.warning("Typesense not configured; search functionality won't work.")
            return
        else:
            self.configured = True

        url = urlparse(settings.typesense_url)
        self.client = typesense.Client(
            {
                "api_key": settings.typesense_api_key,
                "nodes": [{"host": url.hostname, "port": url.port, "protocol": url.scheme}],
                "connection_timeout_seconds": 10,
            }
        )
        self.languages = settings.languages
        self.embedding_model = settings.typesense_embedding_model
        self.exclude_if_language_missing = settings.typesense_exclude_if_language_missing

        logger.info("Typesense URL: %s", settings.typesense_url)
        logger.info("Typesense language: %s", self.languages)
        logger.info("Typesense embedding model: %s", self.embedding_model)

    def is_configured(self) -> bool:
        return self.configured

    async def initialize(self) -> None:
        if not self.is_configured():
            raise SearchNotConfigured

        collections = await self.client.collections.retrieve()
        collection_labels = [obj["name"] for obj in collections]
        logger.info("Existing typesense collections: %s", collection_labels)

        for language in self.languages:
            if (name := c(language)) not in collection_labels:
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
                        ],
                    }
                )

    async def reset(self) -> None:
        if not self.is_configured():
            raise SearchNotConfigured

        logger.warning("Resetting all Typesense collections")
        collection_labels = await self.client.collections.retrieve()
        for collection in collection_labels:
            await self.client.collections[collection].delete()

    async def create_concept(self, concept: Concept) -> None:
        if not self.is_configured():
            raise SearchNotConfigured

        for language in self.languages:
            dct = concept.to_search_dict(language)
            if dct["pref_label"] or not self.exclude_if_language_missing:
                await self.client.collections[c(language)].documents.create(dct)

    async def update_concept(self, concept: Concept) -> None:
        if not self.is_configured():
            raise SearchNotConfigured

        for language in self.languages:
            await self.client.collections[c(language)].documents.update(
                concept.to_search_dict(language)
            )

    async def delete_concept(self, iri: str) -> None:
        if not self.is_configured():
            raise SearchNotConfigured

        for language in self.languages:
            await self.client.collections[c(language)].documents[quote(iri)].delete(
                ignore_not_found=True
            )

    async def search(
        self, query: str, language: str, semantic: bool = True, prefix: bool = False
    ) -> list[SearchResult]:
        if not self.is_configured():
            raise SearchNotConfigured
        if language not in self.languages:
            raise UnknownLanguage

        if prefix:
            semantic = False

        without_semantic = (
            "pref_label,alt_labels,hidden_labels,notation,definition,all_languages_pref_labels"
        )
        with_semantic = "pref_label,pref_label_embedding,alt_labels,hidden_labels,notation,definition,all_languages_pref_labels"

        results = await self.client.collections[c(language)].documents.search(
            {
                "q": query,
                "query_by": with_semantic if semantic else without_semantic,
                "per_page": 50,
                "prefix": prefix,
                "exclude_fields": "pref_label_embedding",
            }
        )
        return SearchResult.from_typesense_results(results)

    async def suggest(self, query: str, language: str) -> list[SearchResult]:
        return await self.search(query=query, language=language, prefix=True)
