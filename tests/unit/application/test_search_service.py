import pytest

from py_semantic_taxonomy.domain.entities import SearchNotConfigured, UnknownLanguage


def test_search_service_instantiation(search_service):
    assert search_service.languages == {"en": "pyst-concepts-en", "de": "pyst-concepts-de"}
    assert search_service.configured
    assert search_service.is_configured()


async def test_search_service_initialize_search_index(search_service):
    await search_service.initialize()
    search_service.engine.initialize.assert_called_once_with(
        list(search_service.languages.values())
    )


async def test_search_service_initialize_search_index_error(search_service):
    search_service.configured = False
    with pytest.raises(SearchNotConfigured):
        await search_service.initialize()


async def test_search_service_reset_search_index(search_service):
    await search_service.reset()
    search_service.engine.reset.assert_called_once_with()


async def test_search_service_reset_search_index_error(search_service):
    search_service.configured = False
    with pytest.raises(SearchNotConfigured):
        await search_service.reset()


async def test_search_service_create_concept_error(search_service, entities):
    search_service.configured = False
    with pytest.raises(SearchNotConfigured):
        await search_service.create_concept(entities[0])


async def test_search_service_create_concept(search_service, entities):
    await search_service.create_concept(entities[0])
    search_service.engine.create_concept.assert_called_once()
    assert search_service.engine.create_concept.call_args[0][1] == "pyst-concepts-en"


async def test_search_service_create_concept_include_empties(search_service, entities):
    search_service.settings.typesense_exclude_if_missing_for_language = False
    await search_service.create_concept(entities[0])
    assert search_service.engine.create_concept.await_count == 2
    assert search_service.engine.create_concept.call_args[0][1] == "pyst-concepts-de"


async def test_search_service_update_concept_error(search_service, entities):
    search_service.configured = False
    with pytest.raises(SearchNotConfigured):
        await search_service.update_concept(entities[0])


async def test_search_service_update_concept(search_service, entities):
    await search_service.update_concept(entities[0])
    search_service.engine.update_concept.assert_called_once()
    assert search_service.engine.update_concept.call_args[0][1] == "pyst-concepts-en"


async def test_search_service_update_concept_include_empties(search_service, entities):
    search_service.settings.typesense_exclude_if_missing_for_language = False
    await search_service.update_concept(entities[0])
    assert search_service.engine.update_concept.await_count == 2
    assert search_service.engine.update_concept.call_args[0][1] == "pyst-concepts-de"


async def test_search_service_delete_concept_error(search_service, entities):
    search_service.configured = False
    with pytest.raises(SearchNotConfigured):
        await search_service.delete_concept(entities[0].id_)


async def test_search_service_delete_concept(search_service, entities):
    await search_service.delete_concept(entities[0].id_)
    assert search_service.engine.delete_concept.await_count == 2
    assert search_service.engine.delete_concept.call_args[0][1] == "pyst-concepts-de"


async def test_search_service_search_configured_error(search_service):
    search_service.configured = False
    with pytest.raises(SearchNotConfigured):
        await search_service.search("q", "l")


async def test_search_service_search_language_error(search_service):
    with pytest.raises(UnknownLanguage):
        await search_service.search("foo", "kz")


async def test_search_service_search_default(search_service):
    await search_service.search("foo", "de")
    search_service.engine.search.assert_called_once_with(
        query="foo", collection=search_service.languages["de"], semantic=True, prefix=False
    )


async def test_search_service_search_semantic(search_service):
    await search_service.search("foo", "de", False)
    search_service.engine.search.assert_called_once_with(
        query="foo", collection=search_service.languages["de"], semantic=False, prefix=False
    )


async def test_search_service_search_suggest(search_service):
    await search_service.suggest("foo", "de")
    search_service.engine.search.assert_called_once_with(
        query="foo", collection=search_service.languages["de"], semantic=False, prefix=True
    )
