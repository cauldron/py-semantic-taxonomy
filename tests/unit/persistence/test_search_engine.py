import pytest

from py_semantic_taxonomy.dependencies import get_search_engine


@pytest.mark.typesense
async def test_search_engine(typesense, entities):
    engine = get_search_engine()
    collections = await engine._collection_labels()
    assert collections == ["pyst-concepts-de", "pyst-concepts-en"]

    await engine.reset()

    assert not await engine._collection_labels()

    await engine.initialize(collections)
    collections = await engine._collection_labels()
    assert collections == ["pyst-concepts-de", "pyst-concepts-en"]

    sd_en = entities[1].to_search_dict("en")
    await engine.create_concept(sd_en, "pyst-concepts-en")

    assert await engine.client.collections["pyst-concepts-en"].documents[sd_en["id"]].retrieve()

    results = await engine.search("moo", "pyst-concepts-en", True, False)
    assert results[0].id_ == entities[1].id_

    results = await engine.search("moo", "pyst-concepts-en", False, False)
    assert not results

    results = await engine.search("anim", "pyst-concepts-en", False, True)
    assert results[0].id_ == entities[1].id_

    updated = {
        "id": sd_en["id"],
        "url": "http%3A%2F%2Fdata.europa.eu%2Fxsp%2Fcn2024%2F010021000090",
        "alt_labels": ["CHAPTER 1 - BIG TRUCKS GO VROOM VROOM"],
        "hidden_labels": [],
        "pref_label": "CHAPTER 1 - TRUCKS",
        "definition": "",
        "notation": "01",
        "all_languages_pref_labels": ["CHAPTER 1 - LIVE ANIMALS", "CAPÍTULO 1 - ANIMAIS VIVOS"],
    }
    await engine.update_concept(updated, "pyst-concepts-en")

    results = await engine.search("diesel", "pyst-concepts-en", True, False)
    assert results[0].id_ == entities[1].id_
    assert results[0].label == "CHAPTER 1 - TRUCKS"

    await engine.delete_concept(sd_en["id"], "pyst-concepts-en")

    results = await engine.search("diesel", "pyst-concepts-en", True, False)
    assert not results


@pytest.mark.typesense
async def test_search_engine_collection_prefix(typesense_with_prefix, entities):
    engine = get_search_engine()
    collections = await engine._collection_labels()
    assert collections == ["prefixtest-pyst-concepts-de", "prefixtest-pyst-concepts-en"]
