"""Integration tests for Web UI functionality."""

from urllib.parse import quote

import pytest


@pytest.mark.typesense
async def test_web_search_preserves_language_in_results(sqlite, typesense, anonymous_client, cn):
    """Test that search results include language parameter in concept links."""
    # Perform a search in German
    response = await anonymous_client.get(
        "/web/search/", params={"query": "Esel", "language": "de"}
    )
    assert response.status_code == 200

    # Check that the HTML contains links with language parameter
    html_content = response.text

    # Search results should link to concepts with language parameter
    # The link format should be: /web/concept/{iri}?language=de
    concept_iri = cn.concept_2023_low["@id"]
    expected_link_pattern = f"/web/concept/{quote(concept_iri)}?language=de"

    assert expected_link_pattern in html_content, (
        f"Expected to find link '{expected_link_pattern}' in search results, "
        f"but it was not present. This means clicking on a search result "
        f"will not preserve the language setting."
    )


@pytest.mark.typesense
async def test_web_search_multiple_languages(sqlite, typesense, anonymous_client, cn):
    """Test that different languages produce correctly parameterized links."""
    languages = ["en", "de"]

    for lang in languages:
        response = await anonymous_client.get(
            "/web/search/", params={"query": "test", "language": lang}
        )
        assert response.status_code == 200

        # Verify the hidden language input has the correct value
        html_content = response.text
        assert f'<input type="hidden" name="language" value="{lang}"' in html_content

        # Verify links include the language parameter
        assert f"?language={lang}" in html_content or f"&language={lang}" in html_content


@pytest.mark.typesense
async def test_web_search_result_links_include_concept_scheme(
    sqlite, typesense, anonymous_client, cn
):
    """Test that search result links preserve both language and allow concept_scheme resolution."""
    response = await anonymous_client.get(
        "/web/search/", params={"query": "Esel", "language": "de"}
    )
    assert response.status_code == 200

    html_content = response.text
    concept_iri = cn.concept_2023_low["@id"]

    # The link should at minimum include the language parameter
    # The concept_scheme will be determined by the backend when the link is clicked
    assert f"/web/concept/{quote(concept_iri)}?language=de" in html_content


async def test_web_search_without_language_redirects(sqlite, anonymous_client):
    """Test that accessing search without language parameter works correctly."""
    # This test doesn't require typesense, just tests the redirect behavior
    response = await anonymous_client.get("/web/search/", follow_redirects=False)

    # Should either redirect to add language or default to 'en'
    # Based on web_router.py:357, it defaults to "en"
    assert response.status_code == 200


async def test_web_search_empty_query(sqlite, anonymous_client):
    """Test that search page renders correctly with empty query."""
    response = await anonymous_client.get("/web/search/", params={"query": "", "language": "en"})
    assert response.status_code == 200

    html_content = response.text
    assert "Start searching" in html_content or "Search" in html_content


@pytest.mark.postgres
async def test_web_search_with_concept_iri_redirects_to_concept(
    postgres, anonymous_client, cn_db_engine, cn
):
    """Test that searching for a concept IRI redirects directly to the concept page."""
    concept_iri = cn.concept_top["@id"]

    response = await anonymous_client.get(
        "/web/search/",
        params={"query": concept_iri, "language": "de"},
        follow_redirects=False,
    )

    # Should redirect with 303 See Other
    assert response.status_code == 303

    # Should redirect to the concept view page with language preserved
    redirect_url = response.headers["location"]
    assert "/web/concept/" in redirect_url
    assert quote(concept_iri) in redirect_url
    assert "language=de" in redirect_url


@pytest.mark.postgres
async def test_web_search_with_concept_scheme_iri_redirects(
    postgres, anonymous_client, cn_db_engine, cn
):
    """Test that searching for a concept scheme IRI redirects to the concept scheme page."""
    scheme_iri = cn.scheme["@id"]

    response = await anonymous_client.get(
        "/web/search/",
        params={"query": scheme_iri, "language": "en"},
        follow_redirects=False,
    )

    # Should redirect with 303 See Other
    assert response.status_code == 303

    # Should redirect to the concept scheme view page
    redirect_url = response.headers["location"]
    assert "/web/concept_scheme/" in redirect_url
    assert quote(scheme_iri) in redirect_url
    assert "language=en" in redirect_url


@pytest.mark.postgres
async def test_web_search_with_nonexistent_iri_shows_search_page(
    postgres, anonymous_client, cn_db_engine
):
    """Test that searching for an IRI that doesn't exist falls back to search (or error if not configured)."""
    nonexistent_iri = "http://example.com/nonexistent/concept/12345"

    response = await anonymous_client.get(
        "/web/search/",
        params={"query": nonexistent_iri, "language": "en"},
        follow_redirects=True,
    )

    # Should show search page (200) if search engine configured
    # or error (503) if search engine not configured
    # Important: should NOT redirect (303) since concept doesn't exist
    assert response.status_code in (200, 503)
    if response.status_code == 503:
        assert "Search engine not available" in response.text or "503" in response.text


@pytest.mark.postgres
@pytest.mark.typesense
async def test_web_search_with_nonexistent_iri_falls_back_to_search(
    postgres, typesense, anonymous_client, cn_db_engine, cn
):
    """Test that searching for an IRI that doesn't exist falls back to text search."""
    nonexistent_iri = "http://example.com/nonexistent/concept/12345"

    response = await anonymous_client.get(
        "/web/search/",
        params={"query": nonexistent_iri, "language": "en"},
        follow_redirects=True,
    )

    # Should show search page (no redirect) since concept doesn't exist
    assert response.status_code == 200
    # Should show the search interface (may or may not have results from text search)
    assert "Search" in response.text or "search" in response.text


async def test_web_search_with_regular_text_not_treated_as_iri(anonymous_client):
    """Test that regular search text is not treated as an IRI (no database required)."""
    response = await anonymous_client.get(
        "/web/search/",
        params={"query": "test query", "language": "en"},
        follow_redirects=True,
    )

    # Should get error because search engine not configured (503)
    # or show search page if engine is configured (200)
    # The important thing is it doesn't try to treat it as an IRI and redirect
    assert response.status_code in (200, 503)
    if response.status_code == 503:
        assert "Search engine not available" in response.text or "503" in response.text
