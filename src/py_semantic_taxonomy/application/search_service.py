import structlog

from py_semantic_taxonomy.cfg import get_settings
from py_semantic_taxonomy.dependencies import get_search_engine
from py_semantic_taxonomy.domain.entities import (
    Concept,
    SearchNotConfigured,
    SearchResult,
    UnknownLanguage,
)
from py_semantic_taxonomy.domain.hash_utils import hash_fnv64
from py_semantic_taxonomy.domain.ports import SearchEngine

logger = structlog.get_logger("py-semantic-taxonomy")


def c(language: str) -> str:
    return f"pyst-concepts-{language}"


class SearchService:
    def __init__(self, engine: SearchEngine | None = None):
        self.settings = get_settings()
        self.languages = {lang: c(lang) for lang in self.settings.languages}

        if self.settings.typesense_url == "missing" or not self.settings.typesense_url:
            self.configured = False
            logger.warning("Typesense not configured; search functionality won't work.")
            return

        self.engine = engine or get_search_engine()
        self.configured = True

        logger.info("Typesense URL: %s", self.settings.typesense_url)
        logger.info("Typesense languages: %s", ",".join(self.languages))
        logger.info("Typesense embedding model: %s", self.settings.typesense_embedding_model)

    def is_configured(self) -> bool:
        return self.configured

    async def initialize(self) -> None:
        if not self.is_configured():
            raise SearchNotConfigured

        await self.engine.initialize(list(self.languages.values()))

    async def reset(self) -> None:
        if not self.is_configured():
            raise SearchNotConfigured

        await self.engine.reset()

    async def create_concept(self, concept: Concept) -> None:
        if not self.is_configured():
            raise SearchNotConfigured

        for language, collection in self.languages.items():
            dct = concept.to_search_dict(language)
            if not (self.settings.typesense_exclude_if_missing_for_language) or dct["pref_label"]:
                await self.engine.create_concept(dct, collection)

    async def update_concept(self, concept: Concept) -> None:
        if not self.is_configured():
            raise SearchNotConfigured

        for language, collection in self.languages.items():
            dct = concept.to_search_dict(language)
            if not (self.settings.typesense_exclude_if_missing_for_language) or dct["pref_label"]:
                await self.engine.update_concept(dct, collection)

    async def delete_concept(self, iri: str) -> None:
        if not self.is_configured():
            raise SearchNotConfigured

        for collection in self.languages.values():
            await self.engine.delete_concept(hash_fnv64(iri), collection)

    async def search(
        self, query: str, language: str, semantic: bool = True, prefix: bool = False
    ) -> list[SearchResult]:
        if not self.is_configured():
            raise SearchNotConfigured

        if language not in self.languages:
            raise UnknownLanguage

        if prefix:
            semantic = False

        return await self.engine.search(
            query=query, collection=self.languages[language], semantic=semantic, prefix=prefix
        )

    async def suggest(self, query: str, language: str) -> list[SearchResult]:
        return await self.search(query=query, language=language, prefix=True)
