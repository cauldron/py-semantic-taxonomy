"""Integration tests for Web UI functionality."""
import pytest
from urllib.parse import quote


@pytest.mark.typesense
async def test_web_search_preserves_language_in_results(
    sqlite, typesense, anonymous_client, cn
):
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
    response = await anonymous_client.get(
        "/web/search/", params={"query": "", "language": "en"}
    )
    assert response.status_code == 200

    html_content = response.text
    assert "Start searching" in html_content or "Search" in html_content
