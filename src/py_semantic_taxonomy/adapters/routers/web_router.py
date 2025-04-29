from enum import StrEnum
from pathlib import Path as PathLib
from urllib.parse import quote, unquote

import structlog
from fastapi import APIRouter, Depends, HTTPException, Path, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from langcodes import Language

from py_semantic_taxonomy.cfg import get_settings
from py_semantic_taxonomy.dependencies import get_graph_service, get_search_service
from py_semantic_taxonomy.domain import entities as de

logger = structlog.get_logger("py-semantic-taxonomy")

router = APIRouter(prefix="/web", include_in_schema=False)


def value_for_language(value: list[dict[str, str]], lang: str) -> str:
    """Get the `@value` for a list of multilingual strings with correct `@language` value"""
    for dct in value:
        if dct.get("@language") == lang:
            return dct.get("@value", "")
    return ""


def best_label(obj: de.SKOS) -> str:
    """Get the best available short label"""
    for notation_obj in obj.notations:
        if value := notation_obj.get("@value"):
            return value
    return obj.pref_labels[0]["@value"][:25]


templates = Jinja2Templates(directory=str(PathLib(__file__).parent / "templates"))
templates.env.filters["split"] = lambda s, sep: s.split(sep)
templates.env.filters["lang"] = value_for_language
templates.env.filters["best_label"] = best_label


def format_languages(languages: list[str]) -> list[tuple[str, str]]:
    """Take a list of ISO 639 language codes and return (code, name)"""
    return [(code, Language.get(code).display_name(code).title()) for code in languages]


class WebPaths(StrEnum):
    concept_schemes = "/concept_schemes/"
    concept_scheme_view = "/concept_scheme/{iri:path}"
    concept_view = "/concept/{iri:path}"
    search = "/search/"


@router.get("/")
async def redirect_blank_web_page(
    request: Request,
) -> RedirectResponse:
    return RedirectResponse(request.url_for("web_concept_schemes"))


@router.get(
    WebPaths.concept_schemes,
    response_class=HTMLResponse,
)
async def web_concept_schemes(
    request: Request,
    service=Depends(get_graph_service),
    settings=Depends(get_settings),
) -> HTMLResponse:
    """List all concept schemes."""
    concept_schemes = await service.concept_scheme_list()
    return templates.TemplateResponse(
        "concept_schemes.html",
        {
            "request": request,
            "concept_schemes": concept_schemes,
            "languages": format_languages(settings.languages),
        },
    )


@router.get(
    WebPaths.concept_scheme_view,
    response_class=HTMLResponse,
)
async def web_concept_scheme_view(
    request: Request,
    iri: str = Path(..., description="The IRI of the concept scheme"),
    service=Depends(get_graph_service),
    settings=Depends(get_settings),
) -> HTMLResponse:
    """View a specific concept scheme."""
    try:
        decoded_iri = unquote(iri)
        concept_scheme = await service.concept_scheme_get(iri=decoded_iri)
        concepts = await service.concepts_get_for_scheme(
            concept_scheme_iri=decoded_iri, top_concepts_only=True
        )
        return templates.TemplateResponse(
            "concept_scheme_view.html",
            {
                "request": request,
                "concept_scheme": concept_scheme,
                "concepts": concepts,
                "languages": format_languages(settings.languages),
            },
        )
    except de.ConceptSchemeNotFoundError:
        raise HTTPException(status_code=404, detail=f"Concept Scheme with IRI `{iri}` not found")
    except de.ConceptSchemesNotInDatabase as e:
        logger.error("Database error while fetching concept scheme", iri=iri, error=str(e))
        raise HTTPException(status_code=500, detail="Database error while fetching concept scheme")


def concept_view_url(request: Request, concept_iri: str, concept_scheme_iri: str) -> str:
    return (
        str(request.url_for("web_concept_view", iri=quote(concept_iri)))
        + "?concept_scheme="
        + quote(concept_scheme_iri, safe="")
    )


@router.get(
    WebPaths.concept_view,
    response_class=HTMLResponse,
)
async def web_concept_view(
    request: Request,
    iri: str = Path(..., description="The IRI of the concept to view"),
    concept_scheme: str | None = None,
    service=Depends(get_graph_service),
    settings=Depends(get_settings),
) -> HTMLResponse:
    """View a specific concept."""
    try:
        decoded_iri = unquote(iri)
        concept = await service.concept_get(iri=decoded_iri)
        if not concept_scheme:
            return RedirectResponse(
                concept_view_url(request, concept.id_, concept.schemes[0]["@id"])
            )
        scheme = await service.concept_scheme_get(iri=unquote(concept_scheme))
        relationships = await service.relationships_get(iri=decoded_iri, source=True, target=True)
        broader = await service.concept_broader_in_ascending_order(
            concept_iri=concept.id_, concept_scheme_iri=scheme.id_
        )
        relationships = await service.relationships_get(iri=decoded_iri, source=True, target=True)

        relationships_data = []
        for rel in relationships:
            relationships_data.append(
                {"source": rel.source, "target": rel.target, "predicate": rel.predicate}
            )

        related_concepts = {}
        for rel in relationships:
            related_iri = rel.target if rel.source == decoded_iri else rel.source
            if related_iri not in related_concepts:
                try:
                    related_concept = await service.concept_get(iri=related_iri)
                    related_concepts[related_iri] = related_concept.to_json_ld()
                except de.ConceptNotFoundError:
                    logger.warning(
                        "Related concept not found",
                        concept_iri=iri,
                        related_iri=related_iri,
                    )

        scheme_list = [
            (request.url_for("web_concept_scheme_view", iri=quote(s["@id"])), s)
            for s in concept.schemes
        ]
        broader_list = [(concept_view_url(request, c.id_, scheme.id_), c) for c in broader[::-1]]
        return templates.TemplateResponse(
            "concept_view.html",
            {
                "request": request,
                "scheme": scheme,
                "scheme_url": request.url_for("web_concept_scheme_view", iri=quote(scheme.id_)),
                "broader_list": broader_list,
                "scheme_list": scheme_list,
                "relationships": relationships_data,
                "related_concepts": related_concepts,
                "concept": concept,
                "languages": format_languages(settings.languages),
            },
        )
    except de.ConceptNotFoundError:
        raise HTTPException(status_code=404, detail=f"Concept with IRI `{iri}` not found")
    except de.ConceptSchemesNotInDatabase as e:
        logger.error("Database error while fetching concept", iri=decoded_iri, error=str(e))
        raise HTTPException(status_code=500, detail="Database error while fetching concept")


@router.get(
    WebPaths.search,
    response_class=HTMLResponse,
)
async def web_search(
    request: Request,
    query: str = "",
    language: str = "en",
    semantic: bool = True,
    search_service=Depends(get_search_service),
) -> HTMLResponse:
    """Search for concepts."""
    try:
        results = []
        if query:
            results = await search_service.search(query=query, language=language, semantic=semantic)
        return templates.TemplateResponse(
            "search.html",
            {
                "request": request,
                "query": query,
                "language": language,
                "semantic": semantic,
                "results": results,
            },
        )
    except de.SearchNotConfigured:
        raise HTTPException(status_code=503, detail="Search engine not available")
    except de.UnknownLanguage:
        raise HTTPException(
            status_code=422, detail="Search engine not configured for given language"
        )
