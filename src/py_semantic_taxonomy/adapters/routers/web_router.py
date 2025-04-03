from enum import StrEnum
from pathlib import Path as PathLib

import structlog
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from py_semantic_taxonomy.dependencies import get_graph_service

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
