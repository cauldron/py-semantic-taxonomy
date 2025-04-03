from enum import StrEnum
from pathlib import Path as PathLib
from urllib.parse import unquote

import structlog
from fastapi import APIRouter, Depends, HTTPException, Path, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from py_semantic_taxonomy.dependencies import get_graph_service
from py_semantic_taxonomy.domain import entities as de

logger = structlog.get_logger("py-semantic-taxonomy")

router = APIRouter(prefix="/web", include_in_schema=False)

templates = Jinja2Templates(directory=str(PathLib(__file__).parent / "templates"))
templates.env.filters["split"] = lambda s, sep: s.split(sep)


class WebPaths(StrEnum):
    concept_schemes = "/concept_schemes/"
    concept_scheme_view = "/concept_scheme/{iri:path}"
    concept_view = "/concept/{iri:path}"


@router.get(
    WebPaths.concept_schemes,
    response_class=HTMLResponse,
)
async def web_concept_schemes(
    request: Request,
    service=Depends(get_graph_service),
) -> HTMLResponse:
    """List all concept schemes."""
    concept_schemes = await service.concept_scheme_list()
    concept_schemes_json = [cs.to_json_ld() for cs in concept_schemes]
    return templates.TemplateResponse(
        "concept_schemes.html",
        {
            "request": request,
            "concept_schemes": concept_schemes_json,
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
) -> HTMLResponse:
    """View a specific concept scheme."""
    try:
        decoded_iri = unquote(iri)
        concept_scheme = await service.concept_scheme_get(iri=decoded_iri)
        concepts = await service.concepts_get_for_scheme(concept_scheme_id=decoded_iri)
        concept_scheme_json = concept_scheme.to_json_ld()
        concepts_json = [c.to_json_ld() for c in concepts]
        return templates.TemplateResponse(
            "concept_scheme_view.html",
            {
                "request": request,
                "concept_scheme": concept_scheme_json,
                "concepts": concepts_json,
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
