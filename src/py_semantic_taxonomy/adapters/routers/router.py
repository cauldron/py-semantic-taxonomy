from urllib.parse import urljoin

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse

import py_semantic_taxonomy.adapters.routers.response_dto as response
from py_semantic_taxonomy.application.services import GraphService
from py_semantic_taxonomy.domain import entities as de

router = APIRouter()


@router.get(
    "/concept/",
    summary="Get a Concept object",
    response_model=response.Concept,
)
async def get_concept(
    iri: str,
    service=Depends(GraphService),
) -> response.Concept:
    try:
        obj = await service.get_concept(iri=iri)
        return response.Concept(**obj.to_json_ld())
    except de.ConceptNotFoundError:
        raise HTTPException(status_code=404, detail=f"Concept with iri '{iri}' not found")


# TBD: Add in static route before generic catch-all function


@router.get(
    "/{_:path}",
    summary="Get a KOS graph object which shares the same base URL as PyST",
)
async def generic_get_from_iri(request: Request, _: str, service=Depends(GraphService)):
    try:
        iri = urljoin(str(request.base_url), request.url.path)
        object_type = await service.get_object_type(iri=iri)
        mapping = {de.Concept: "get_concept_from_iri"}
        return RedirectResponse(url=request.url_for(mapping[object_type], iri=iri))
    except de.NotFoundError:
        raise HTTPException(status_code=404, detail=f"KOS graph object with iri {iri} not found")
