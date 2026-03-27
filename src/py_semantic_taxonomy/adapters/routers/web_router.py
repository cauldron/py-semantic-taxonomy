from enum import StrEnum
from pathlib import Path as PathLib
from secrets import token_urlsafe
from urllib.parse import quote, unquote, urlencode

import rfc3987
import structlog
from fastapi import APIRouter, Depends, HTTPException, Path, Request, Body
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

dynamic_text_store = {
    "concept_schemes_description": "Browse and manage your semantic taxonomies"
}

def _is_iri(query: str) -> bool:
    """Check if query string is a valid HTTP/HTTPS IRI."""
    try:
        parsed = rfc3987.parse(query.strip(), rule="IRI")
        return parsed.get("scheme") in ("http", "https")
    except ValueError:
        return False


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

def scheme_list(obj: de.SKOS | str, cutoff: int = 40) -> str:
    """Return a comma-separated list of scheme IRIs (shortened)."""
    if isinstance(obj, str):
        return ""

    schemes = []
    for s in obj.schemes:
        iri = s.get("@id", "")
        if iri:
            # reuse your existing short_iri logic
            if len(iri) > cutoff:
                iri = iri[:20] + "..." + iri[-20:]
            schemes.append(iri)

    return ", ".join(schemes)

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
templates.env.filters["scheme_list"] = scheme_list
templates.env.filters["urlencode"] = quote
templates.env.globals["is_admin_request"] = (
    lambda request: bool(getattr(request, "session", {}).get("admin_user"))
)
templates.env.globals["admin_user_name"] = (
    lambda request: (getattr(request, "session", {}).get("admin_user") or {}).get("name", "Admin")
)


def ensure_admin_csrf_token(request: Request) -> str:
    csrf_token = request.session.get("admin_csrf_token")
    if not csrf_token:
        csrf_token = quote(token_urlsafe(32), safe="")
        request.session["admin_csrf_token"] = csrf_token
    return csrf_token


def format_languages(languages: list[str]) -> list[tuple[str, str]]:
    """Take a list of ISO 639 language codes and return (code, name)"""
    return [(code, Language.get(code).display_name(code).title()) for code in languages]


def build_language_selector(
    current_language: str,
    options: list[tuple[str, str]],
) -> list[tuple[str, str, bool]]:
    return [(url, label, code == current_language) for code, label, url in options]


async def _format_simple_associations(
    *,
    concept: de.Concept,
    service,
    get_concept_and_link,
) -> list[dict[str, str | de.Concept | None]]:
    outgoing = await service.association_get_all(source_concept_iri=concept.id_)
    incoming = await service.association_get_all(target_concept_iri=concept.id_)

    formatted = []
    seen = set()

    async def add_entry(
        association: de.Association,
        related_node: dict[str, str],
        *,
        direction: str,
    ) -> None:
        related_iri = related_node.get("@id")
        if not related_iri:
            return

        dedupe_key = (association.id_, related_iri, direction)
        if dedupe_key in seen:
            return
        seen.add(dedupe_key)

        url, assoc_concept = await get_concept_and_link(related_iri)
        formatted.append(
            {
                "url": url,
                "obj": assoc_concept,
                "conditional": None,
                "conversion": related_node.get(
                    "http://qudt.org/3.0.0/schema/qudt/conversionMultiplier"
                ),
                "direction": direction,
            }
        )

    for association in filter(lambda x: x.kind == AssociationKind.simple, outgoing):
        for target in association.target_concepts:
            await add_entry(association, target, direction="Outgoing")

    for association in filter(lambda x: x.kind == AssociationKind.simple, incoming):
        for source in association.source_concepts:
            if source.get("@id") != concept.id_:
                await add_entry(association, source, direction="Incoming")

    return formatted


class WebPaths(StrEnum):
    concept_schemes = "/concept_schemes/"
    concept_scheme_view = "/concept_scheme/{iri:path}"
    concept_view = "/concept/{iri:path}"
    search = "/search/"
    concept_children_fragment = "/fragment/concept/{iri:path}/children"
    concept_detail_fragment = "/fragment/concept/{iri:path}/detail"


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

    languages = build_language_selector(
        language,
        [
            (
                code,
                label,
                str(request.url_for("web_concept_schemes")) + "?language=" + quote(code),
            )
            for code, label in format_languages(settings.languages)
        ],
    )
    return templates.TemplateResponse(
        "concept_schemes.html",
        {
            "request": request,
            "concept_schemes": concept_schemes,
            "language_selector": languages,
            "language": language,
            "suggest_api_url": get_full_api_path("suggest"),
            "page_description": dynamic_text_store["concept_schemes_description"],
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

        languages = build_language_selector(
            language,
            [
                (
                    code,
                    label,
                    str(request.url_for("web_concept_scheme_view", iri=iri))
                    + "?language="
                    + quote(code),
                )
                for code, label in format_languages(settings.languages)
            ],
        )

        return templates.TemplateResponse(
            "concept_scheme_view.html",
            {
                "request": request,
                "concept_scheme": concept_scheme,
                "concepts": concepts,
                "language": language,
                "language_selector": languages,
                "suggest_api_url": get_full_api_path("suggest"),
                "csrf_token": ensure_admin_csrf_token(request),
            },
        )
    except de.ConceptSchemeNotFoundError:
        raise HTTPException(
            status_code=404, detail=f"Concept Scheme with IRI `{iri}` not found"
        )
    except de.ConceptSchemesNotInDatabase as e:
        logger.error(
            "Database error while fetching concept scheme", iri=iri, error=str(e)
        )
        raise HTTPException(
            status_code=500, detail="Database error while fetching concept scheme"
        )


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

        relationships = await service.relationships_get(
            iri=decoded_iri, source=True, target=True
        )
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
            (request.url_for("web_concept_view", iri=quote(s["@id"])), s)
            for s in concept.schemes
        ]

        formatted_associations = await _format_simple_associations(
            concept=concept,
            service=service,
            get_concept_and_link=get_concept_and_link,
        )

        languages = build_language_selector(
            language,
            [
                (
                    code,
                    label,
                    concept_view_url(
                        request,
                        concept.id_,
                        scheme.id_,
                        code,
                    ),
                )
                for code, label in format_languages(settings.languages)
            ],
        )

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
                "csrf_token": ensure_admin_csrf_token(request),
            },
        )
    except de.ConceptNotFoundError:
        raise HTTPException(status_code=404, detail=f"Concept with IRI `{iri}` not found")
    except de.ConceptSchemesNotInDatabase as e:
        logger.error(
            "Database error while fetching concept", iri=decoded_iri, error=str(e)
        )
        raise HTTPException(status_code=500, detail="Database error while fetching concept")


@router.get(
    WebPaths.concept_children_fragment,
    response_class=HTMLResponse,
)
async def web_concept_children_fragment(
    request: Request,
    iri: str = Path(..., description="The IRI of the parent concept"),
    concept_scheme: str | None = None,
    language: str | None = None,
    service=Depends(get_graph_service),
) -> HTMLResponse:
    """Return a partial HTML fragment listing the child concepts of a concept."""
    if not concept_scheme or not language:
        return HTMLResponse("Missing required parameters: concept_scheme and language", status_code=422)

    decoded_iri = unquote(iri)
    relationships = await service.relationships_get(iri=decoded_iri, source=True, target=True)

    children = []
    for obj in relationships:
        if obj.target == decoded_iri and obj.predicate == RelationshipVerbs.broader:
            try:
                child_concept = await service.concept_get(iri=obj.source)
                child_concept = child_concept.filter_language(language)
                children.append(child_concept)
            except de.ConceptNotFoundError:
                pass

    return templates.TemplateResponse(
        "_concept_tree_children.html",
        {
            "request": request,
            "children": children,
            "concept_scheme": concept_scheme,
            "language": language,
        },
    )


@router.get(
    WebPaths.concept_detail_fragment,
    response_class=HTMLResponse,
)
async def web_concept_detail_fragment(
    request: Request,
    iri: str = Path(..., description="The IRI of the concept"),
    concept_scheme: str | None = None,
    language: str | None = None,
    service=Depends(get_graph_service),
) -> HTMLResponse:
    """Return a partial HTML fragment with the full detail of a concept."""
    if not concept_scheme or not language:
        return HTMLResponse("Missing required parameters: concept_scheme and language", status_code=422)

    try:
        decoded_iri = unquote(iri)
        concept = await service.concept_get(iri=decoded_iri)
        concept = concept.filter_language(language)

        scheme = await service.concept_scheme_get(iri=unquote(concept_scheme))

        hierarchy = (
            await service.concept_broader_in_ascending_order(
                concept_iri=concept.id_, concept_scheme_iri=scheme.id_
            )
        )[::-1]
        hierarchy = [(concept_view_url(request, c.id_, scheme.id_, language), c) for c in hierarchy]

        async def get_concept_and_link(concept_iri: str) -> tuple[str, de.Concept | str]:
            try:
                c = (await service.concept_get(iri=concept_iri)).filter_language(language)
                url = concept_view_url(
                    request,
                    concept_iri,
                    (
                        scheme.id_
                        if any(scheme.id_ == os["@id"] for os in c.schemes)
                        else c.schemes[0]["@id"]
                    ),
                    language,
                )
                return url, c
            except de.ConceptNotFoundError:
                return concept_iri, concept_iri

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

        scheme_list_data = [
            (concept_scheme_view_url(request, s["@id"], language), s)
            for s in concept.schemes
        ]

        formatted_associations = await _format_simple_associations(
            concept=concept,
            service=service,
            get_concept_and_link=get_concept_and_link,
        )

        return templates.TemplateResponse(
            "_concept_detail_panel.html",
            {
                "request": request,
                "scheme": scheme,
                "scheme_url": concept_scheme_view_url(request, scheme.id_, language),
                "hierarchy": hierarchy,
                "scheme_list": scheme_list_data,
                "broader_concepts": broader,
                "narrower_concepts": narrower,
                "concept": concept,
                "language": language,
                "associations": formatted_associations,
                "concept_scheme_iri": concept_scheme,
                "suggest_api_url": get_full_api_path("suggest"),
                "csrf_token": ensure_admin_csrf_token(request),
            },
        )
    except de.ConceptNotFoundError:
        return HTMLResponse(
            "<div class='card px-4 py-5 text-center' style='color: var(--text-secondary)'>Concept not found.</div>",
            status_code=404,
        )
    except de.ConceptSchemesNotInDatabase as e:
        logger.error("Database error in detail fragment", iri=iri, error=str(e))
        return HTMLResponse(
            "<div class='card px-4 py-5 text-center' style='color: var(--text-secondary)'>Database error.</div>",
            status_code=500,
        )


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
    graph_service=Depends(get_graph_service),
    settings=Depends(get_settings),
) -> HTMLResponse:
    """Search for concepts."""
    # Check if query is an IRI and attempt direct lookup
    if query and _is_iri(query):
        # Try to get concept directly
        try:
            concept = await graph_service.concept_get(iri=query)
            # If found, redirect to concept page
            return RedirectResponse(
                url=concept_view_url(
                    request,
                    concept.id_,
                    concept.schemes[0]["@id"],
                    language,
                ),
                status_code=303,  # See Other
            )
        except de.ConceptNotFoundError:
            # Not a concept, try concept scheme
            try:
                concept_scheme = await graph_service.concept_scheme_get(iri=query)
                # If found, redirect to concept scheme page
                return RedirectResponse(
                    url=concept_scheme_view_url(request, concept_scheme.id_, language),
                    status_code=303,  # See Other
                )
            except de.ConceptSchemeNotFoundError:
                # IRI not found in database, fall through to regular search
                pass

    try:
        results = []
        if query:
            results = await search_service.search(query=query, language=language, semantic=semantic)

        languages = [(request.url, Language.get(language).display_name(language).title())] + [
            (
                str(request.url_for("web_search"))
                + "?"
                + urlencode({"query": query, "language": code, "semantic": semantic}),
                label,
            )
            for code, label in format_languages(settings.languages)
            if code != language
        ]

        return templates.TemplateResponse(
            "search.html",
            {
                "request": request,
                "query": query,
                "language": language,
                "language_selector": languages,
                "semantic": semantic,
                "results": results,
                "suggest_api_url": get_full_api_path("suggest"),
                "concept_api_base_url": get_full_api_path("concept_all"),
            },
        )
    except de.SearchNotConfigured:
        raise HTTPException(status_code=503, detail="Search engine not available")
    except de.UnknownLanguage:
        raise HTTPException(
            status_code=422, detail="Search engine not configured for given language"
        )

@router.post("/update_description/")
async def update_description(
    new_text: str = Body(..., embed=True)
):
    dynamic_text_store["concept_schemes_description"] = new_text
    return {"status": "ok", "new_text": new_text}
