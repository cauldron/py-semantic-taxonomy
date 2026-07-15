from urllib.parse import quote

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, RedirectResponse

from py_semantic_taxonomy.dependencies import get_graph_service
from py_semantic_taxonomy.domain import entities as de

router = APIRouter(include_in_schema=False)


@router.get("/")
async def redirect_main_page(
    request: Request,
) -> RedirectResponse:
    return RedirectResponse(request.url_for("web_concept_schemes"))


def _wants_html(request: Request) -> bool:
    return "text/html" in request.headers.get("accept", "")


@router.get("/{path:path}", response_model=None)
async def resolve_iri(
    request: Request,
    service=Depends(get_graph_service),
) -> JSONResponse | RedirectResponse:
    """Resolve an object's own IRI.

    Objects are identified by IRIs which are (when deployed correctly) served by this
    application. Following such an IRI in a browser should show the web UI; a request for
    JSON(-LD) should return the machine-readable data instead of a 404.
    """
    iri = str(request.url).split("?")[0]

    try:
        obj = await service.concept_scheme_get(iri=iri)
        if _wants_html(request):
            return RedirectResponse(request.url_for("web_concept_scheme_view", iri=quote(iri)))
        return JSONResponse(obj.to_json_ld())
    except de.ConceptSchemeNotFoundError:
        pass

    try:
        obj = await service.concept_get(iri=iri)
        if _wants_html(request):
            return RedirectResponse(request.url_for("web_concept_view", iri=quote(iri)))
        return JSONResponse(obj.to_json_ld())
    except de.ConceptNotFoundError:
        pass

    try:
        # No web UI for correspondences, so always return JSON-LD.
        obj = await service.correspondence_get(iri=iri)
        return JSONResponse(obj.to_json_ld())
    except de.CorrespondenceNotFoundError:
        pass

    return JSONResponse({"detail": f"No object found with IRI `{iri}`"}, status_code=404)
