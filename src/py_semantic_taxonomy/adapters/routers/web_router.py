from enum import StrEnum
from pathlib import Path as PathLib
from urllib.parse import quote, unquote, urlencode

import structlog
from fastapi import APIRouter, Depends, HTTPException, Path, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from langcodes import Language

from py_semantic_taxonomy.cfg import get_settings
from py_semantic_taxonomy.dependencies import get_graph_service, get_search_service
from py_semantic_taxonomy.domain import entities as de
from py_semantic_taxonomy.domain.constants import (
    AssociationKind,
    RelationshipVerbs,
)
from py_semantic_taxonomy.domain.url_utils import get_full_api_path

logger = structlog.get_logger("py-semantic-taxonomy")

router = APIRouter(prefix="/web", include_in_schema=False)


def value_for_language(value: list[dict[str, str]], lang: str) -> str:
    """Get the `@value` for a list of multilingual strings with correct `@language` value"""
    for dct in value:
        if dct.get("@language") == lang:
            return dct.get("@value", "")
    return ""


def best_label(obj: de.SKOS | str, lang: str) -> str:
    """Get the best available short label"""
    # External IRI without data
    if isinstance(obj, str):
        return obj
    for label_obj in obj.pref_labels:
        if label_obj["@language"] == lang:
            return label_obj["@value"]
    return "(label unavailable)"


def short_iri(iri: str) -> str:
    if len(iri) < 45:
        return iri
    return iri[:20] + "..." + iri[-20:]


def best_short_label(obj: de.SKOS | str, lang: str, cutoff: int = 30) -> str:
    """Get the best available short label"""
    # External IRI without data
    if isinstance(obj, str):
        return obj
    for notation_obj in obj.notations:
        if value := notation_obj.get("@value"):
            return value
    for label_obj in obj.pref_labels:
        if label_obj["@language"] == lang:
            if len(label_obj["@value"]) > cutoff:
                return label_obj["@value"][:cutoff] + "..."
            return label_obj["@value"]
    return "(label unavailable)"


templates = Jinja2Templates(directory=str(PathLib(__file__).parent / "templates"))
templates.env.filters["split"] = lambda s, sep: s.split(sep)
templates.env.filters["lang"] = value_for_language
templates.env.filters["best_label"] = best_label
templates.env.filters["best_short_label"] = best_short_label
templates.env.filters["short_iri"] = short_iri


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


def concept_scheme_view_url(request: Request, concept_scheme_iri: str, language: str) -> str:
    params = {"language": language}
    return (
        str(request.url_for("web_concept_scheme_view", iri=quote(concept_scheme_iri)))
        + "?"
        + urlencode(params)
    )


@router.get(
    WebPaths.concept_schemes,
    response_class=HTMLResponse,
)
async def web_concept_schemes(
    request: Request,
    language: str | None = None,
    service=Depends(get_graph_service),
    settings=Depends(get_settings),
) -> HTMLResponse:
    """List all concept schemes."""
    if not language:
        return RedirectResponse(
            str(request.url_for("web_concept_schemes"))
            + "?language="
            + quote(settings.languages[0])
        )

    concept_schemes = await service.concept_scheme_get_all()
    for scheme in concept_schemes:
        scheme.url = concept_scheme_view_url(request, scheme.id_, language)

    languages = [(request.url, Language.get(language).display_name(language).title())] + [
        (str(request.url_for("web_concept_schemes")) + "?language=" + quote(code), label)
        for code, label in format_languages(settings.languages)
        if code != language
    ]
    return templates.TemplateResponse(
        "concept_schemes.html",
        {
            "request": request,
            "concept_schemes": concept_schemes,
            "language_selector": languages,
            "language": language,
            "suggest_api_url": get_full_api_path("suggest"),
        },
    )


@router.get(
    WebPaths.concept_scheme_view,
    response_class=HTMLResponse,
)
async def web_concept_scheme_view(
    request: Request,
    iri: str = Path(..., description="The IRI of the concept scheme"),
    language: str | None = None,
    service=Depends(get_graph_service),
    settings=Depends(get_settings),
) -> HTMLResponse:
    """View a specific concept scheme."""
    try:
        if not language:
            return RedirectResponse(
                str(request.url_for("web_concept_scheme_view", iri=iri))
                + "?language="
                + quote(settings.languages[0])
            )

        decoded_iri = unquote(iri)
        concept_scheme = await service.concept_scheme_get(iri=decoded_iri)
        concepts = await service.concept_get_all(
            concept_scheme_iri=decoded_iri, top_concepts_only=True
        )
        for concept in concepts:
            concept.url = concept_view_url(request, concept.id_, concept_scheme.id_, language)

        languages = [(request.url, Language.get(language).display_name(language).title())] + [
            (
                str(request.url_for("web_concept_scheme_view", iri=iri))
                + "?language="
                + quote(code),
                label,
            )
            for code, label in format_languages(settings.languages)
            if code != language
        ]

        return templates.TemplateResponse(
            "concept_scheme_view.html",
            {
                "request": request,
                "concept_scheme": concept_scheme,
                "concepts": concepts,
                "language": language,
                "language_selector": languages,
                "suggest_api_url": get_full_api_path("suggest"),
            },
        )
    except de.ConceptSchemeNotFoundError:
        raise HTTPException(status_code=404, detail=f"Concept Scheme with IRI `{iri}` not found")
    except de.ConceptSchemesNotInDatabase as e:
        logger.error("Database error while fetching concept scheme", iri=iri, error=str(e))
        raise HTTPException(status_code=500, detail="Database error while fetching concept scheme")


def concept_view_url(
    request: Request, concept_iri: str, concept_scheme_iri: str, language: str
) -> str:
    params = {"concept_scheme": concept_scheme_iri, "language": language}
    return (
        str(request.url_for("web_concept_view", iri=quote(concept_iri))) + "?" + urlencode(params)
    )


@router.get(
    WebPaths.concept_view,
    response_class=HTMLResponse,
)
async def web_concept_view(
    request: Request,
    iri: str = Path(..., description="The IRI of the concept to view"),
    concept_scheme: str | None = None,
    language: str | None = None,
    service=Depends(get_graph_service),
    settings=Depends(get_settings),
) -> HTMLResponse:
    """View a specific concept."""
    try:
        decoded_iri = unquote(iri)
        concept = await service.concept_get(iri=decoded_iri)
        if not concept_scheme:
            return RedirectResponse(
                concept_view_url(
                    request,
                    concept.id_,
                    concept.schemes[0]["@id"],
                    language or settings.languages[0],
                )
            )

        if not language:
            return RedirectResponse(
                concept_view_url(
                    request, concept.id_, concept.schemes[0]["@id"], settings.languages[0]
                )
            )
        concept = concept.filter_language(language)

        scheme = await service.concept_scheme_get(iri=unquote(concept_scheme))

        hierarchy = (
            await service.concept_broader_in_ascending_order(
                concept_iri=concept.id_, concept_scheme_iri=scheme.id_
            )
        )[::-1]
        hierarchy = [(concept_view_url(request, c.id_, scheme.id_, language), c) for c in hierarchy]

        async def get_concept_and_link(iri: str) -> (str, de.Concept | str):
            try:
                concept = (await service.concept_get(iri=iri)).filter_language(language)
                url = concept_view_url(
                    request,
                    iri,
                    (
                        scheme.id_
                        if any(scheme.id_ == os["@id"] for os in concept.schemes)
                        else concept.schemes[0]["@id"]
                    ),
                    language,
                )
                return url, concept
            except de.ConceptNotFoundError:
                return iri, iri

        relationships = await service.relationships_get(iri=decoded_iri, source=True, target=True)
        broader = [
            (await get_concept_and_link(obj.target))
            for obj in relationships
            if obj.source == concept.id_ and obj.predicate == RelationshipVerbs.broader
        ]
        narrower = [
            (await get_concept_and_link(obj.source))
            for obj in relationships
            if obj.target == concept.id_ and obj.predicate == RelationshipVerbs.broader
        ]

        scheme_list = [
            (request.url_for("web_concept_view", iri=quote(s["@id"])), s) for s in concept.schemes
        ]

        associations = await service.association_get_all(source_concept_iri=concept.id_)
        formatted_associations = []
        for obj in filter(lambda x: x.kind == AssociationKind.simple, associations):
            for target in obj.target_concepts:
                try:
                    url, assoc_concept = await get_concept_and_link(target["@id"])
                    formatted_associations.append(
                        {
                            "url": url,
                            "obj": assoc_concept,
                            "conditional": None,
                            "conversion": target.get(
                                "http://qudt.org/3.0.0/schema/qudt/conversionMultiplier"
                            ),
                        }
                    )
                except de.ConceptNotFoundError:
                    formatted_associations.append(
                        {
                            "url": target["@id"],
                            "obj": target["@id"],
                            "conditional": None,
                            "conversion": target.get(
                                "http://qudt.org/3.0.0/schema/qudt/conversionMultiplier"
                            ),
                        }
                    )

        languages = [(request.url, Language.get(language).display_name(language).title())] + [
            (
                concept_view_url(
                    request,
                    concept.id_,
                    scheme.id_,
                    code,
                ),
                label,
            )
            for code, label in format_languages(settings.languages)
            if code != language
        ]

        return templates.TemplateResponse(
            "concept_view.html",
            {
                "request": request,
                "scheme": scheme,
                "scheme_url": concept_scheme_view_url(request, scheme.id_, language),
                "hierarchy": hierarchy,
                "scheme_list": scheme_list,
                "broader_concepts": broader,
                "narrower_concepts": narrower,
                "concept": concept,
                "language_selector": languages,
                "language": language,
                "associations": formatted_associations,
                # "conditional_associations": conditional_associations,
                "suggest_api_url": get_full_api_path("suggest"),
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
                "suggest_api_url": get_full_api_path("suggest"),
                "concept_api_url": get_full_api_path("concept"),
            },
        )
    except de.SearchNotConfigured:
        raise HTTPException(status_code=503, detail="Search engine not available")
    except de.UnknownLanguage:
        raise HTTPException(
            status_code=422, detail="Search engine not configured for given language"
        )
