from enum import StrEnum
from urllib.parse import urljoin

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse

import py_semantic_taxonomy.adapters.routers.request_dto as req
import py_semantic_taxonomy.adapters.routers.response_dto as response
from py_semantic_taxonomy.application.services import GraphService
from py_semantic_taxonomy.domain import entities as de

router = APIRouter()


class Paths(StrEnum):
    concept = "/concept/"
    catchall = "/{_:path}"


"""
In some cases, we will define a function input argument as a Pydantic class, but not use that
Pydantic class in the function code itself. This is because of the way we have defined our
Pydantic classes, which use child Pydantic models extensively, and our needs to use aliases. Aliases
are necessary because JSON-LD has keys like `@id` and
`http://www.w3.org/2004/02/skos/core#prefLabel`, which can't be used as Python identifiers.

When serializing data from Pydantic models, the behaviour of aliases is inconsistent. For example,
even if you specify `by_alias` true by default in child model `model_dump` functions, these nested
`model_dump` functions are actually not called when serializing the parent model, so `by_alias` is
not used.

The recommended solution is to use a custom `model_serializer`:

https://github.com/pydantic/pydantic/issues/8792

This approach would require duplicating `model_dump`, and would cause continuous frustration.

It's possible that this will change in the future:

https://github.com/pydantic/pydantic/issues/8379
"""


@router.get(
    Paths.concept,
    summary="Get a Concept object",
    response_model=response.Concept,
    responses={404: {"model": response.ErrorMessage}},
)
async def concept_get(
    iri: str,
    service=Depends(GraphService),
) -> response.Concept:
    try:
        obj = await service.concept_get(iri=iri)
        return response.Concept(**obj.to_json_ld())
    except de.ConceptNotFoundError:
        return JSONResponse(
            status_code=404,
            content={"message": f"Concept with IRI '{iri}' not found", "detail": {"iri": iri}},
        )


@router.post(
    Paths.concept,
    summary="Create a Concept object",
    response_model=response.Concept,
)
async def concept_create(
    request: Request,
    concept: req.ConceptCreate,
    service=Depends(GraphService),
) -> response.Concept:
    try:
        concept = de.Concept.from_json_ld(await request.json())
        result = await service.concept_create(concept)
        return response.Concept(**result.to_json_ld())
    except de.DuplicateIRI:
        return JSONResponse(
            status_code=409,
            content={
                "message": f"Resource with `@id` already exists",
                "detail": {"@id": concept.id_},
            },
        )


@router.put(
    Paths.concept,
    summary="Update a Concept object",
    response_model=response.Concept,
)
async def concept_update(
    request: Request,
    concept: req.ConceptUpdate,
    service=Depends(GraphService),
) -> response.Concept:
    try:
        concept_obj = de.Concept.from_json_ld(await request.json())
        result = await service.concept_update(concept_obj)
        return response.Concept(**result.to_json_ld())
    except de.ConceptNotFoundError:
        return JSONResponse(
            status_code=404,
            content={
                "message": f"Concept with `@id` {concept.id_} not present",
                "detail": {"@id": concept.id_},
            },
        )


@router.delete(
    Paths.concept,
    summary="Delete a Concept object",
)
async def concept_delete(
    iri: str,
    service=Depends(GraphService),
) -> JSONResponse:
    count = await service.concept_delete(iri=iri)
    # TBD: 404 if not found?
    return JSONResponse(
        status_code=200,
        content={
            "message": f"Concept (possibly) deleted",
            "count": count,
        },
    )


# TBD: Add in static route before generic catch-all function


@router.get(
    Paths.catchall,
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
