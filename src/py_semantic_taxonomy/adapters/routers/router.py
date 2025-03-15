from enum import StrEnum
from urllib.parse import quote_plus, urljoin

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse

import py_semantic_taxonomy.adapters.routers.request_dto as req
import py_semantic_taxonomy.adapters.routers.response_dto as response
from py_semantic_taxonomy.application.services import GraphService
from py_semantic_taxonomy.domain import entities as de

router = APIRouter()


class Paths(StrEnum):
    concept = "/concept/"
    concept_scheme = "/concept_scheme/"
    catchall = "/{_:path}"
    relationship = "/relationships/"
    correspondence = "/correspondence"


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

# Concept


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
        incoming_data = await request.json()
        concept = de.Concept.from_json_ld(incoming_data)
        relationships = de.Relationship.from_json_ld(incoming_data)
        result = await service.concept_create(concept=concept, relationships=relationships)
        return response.Concept(**result.to_json_ld())
    except de.DuplicateIRI:
        return JSONResponse(
            status_code=409,
            content={
                "message": f"Resource with `@id` already exists",
                "detail": {"@id": concept.id_},
            },
        )
    except (
        de.HierarchicRelationshipAcrossConceptScheme,
        de.DuplicateRelationship,
        de.ConceptSchemesNotInDatabase,
    ) as exc:
        return JSONResponse(
            status_code=422,
            content={
                "message": str(exc),
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
    except (
        de.RelationshipsInCurrentConceptScheme,
        de.ConceptSchemesNotInDatabase,
    ) as exc:
        return JSONResponse(
            status_code=422,
            content={
                "message": str(exc),
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
            "message": "Concept (possibly) deleted",
            "count": count,
        },
    )


# Concept Scheme


@router.get(
    Paths.concept_scheme,
    summary="Get a ConceptScheme object",
    response_model=response.ConceptScheme,
    responses={404: {"model": response.ErrorMessage}},
)
async def concept_scheme_get(
    iri: str,
    service=Depends(GraphService),
) -> response.ConceptScheme:
    try:
        obj = await service.concept_scheme_get(iri=iri)
        return response.ConceptScheme(**obj.to_json_ld())
    except de.ConceptSchemeNotFoundError:
        return JSONResponse(
            status_code=404,
            content={
                "message": f"Concept Scheme with IRI '{iri}' not found",
                "detail": {"iri": iri},
            },
        )


@router.post(
    Paths.concept_scheme,
    summary="Create a Concept Scheme object",
    response_model=response.ConceptScheme,
)
async def concept_scheme_create(
    request: Request,
    concept_scheme: req.ConceptScheme,
    service=Depends(GraphService),
) -> response.ConceptScheme:
    try:
        cs = de.ConceptScheme.from_json_ld(await request.json())
        result = await service.concept_scheme_create(cs)
        return response.ConceptScheme(**result.to_json_ld())
    except de.DuplicateIRI:
        return JSONResponse(
            status_code=409,
            content={
                "message": f"Resource with `@id` already exists",
                "detail": {"@id": cs.id_},
            },
        )


@router.put(
    Paths.concept_scheme,
    summary="Update a Concept Scheme object",
    response_model=response.ConceptScheme,
)
async def concept_scheme_update(
    request: Request,
    concept_scheme: req.ConceptScheme,
    service=Depends(GraphService),
) -> response.ConceptScheme:
    try:
        cs = de.ConceptScheme.from_json_ld(await request.json())
        result = await service.concept_scheme_update(cs)
        return response.ConceptScheme(**result.to_json_ld())
    except de.ConceptSchemeNotFoundError:
        return JSONResponse(
            status_code=404,
            content={
                "message": f"Concept Scheme with `@id` {cs.id_} not present",
                "detail": {"@id": cs.id_},
            },
        )


@router.delete(
    Paths.concept_scheme,
    summary="Delete a Concept Scheme object",
)
async def concept_scheme_delete(
    iri: str,
    service=Depends(GraphService),
) -> JSONResponse:
    count = await service.concept_scheme_delete(iri=iri)
    # TBD: 404 if not found?
    return JSONResponse(
        status_code=200,
        content={
            "message": "Concept Scheme (possibly) deleted",
            "count": count,
        },
    )


# Relationship


@router.get(
    Paths.relationship,
    summary="Get a list of Relationship objects",
    response_model=list[response.Relationship],
    response_model_exclude_unset=True,
)
async def relationships_get(
    iri: str,
    source: bool = True,
    target: bool = False,
    service=Depends(GraphService),
) -> list[response.Relationship]:
    lst = await service.relationships_get(iri=iri, source=source, target=target)
    return [response.Relationship(**obj.to_json_ld()) for obj in lst]


@router.post(
    Paths.relationship,
    summary="Create a list of Relationship objects",
    response_model=list[response.Relationship],
    response_model_exclude_unset=True,
)
async def relationships_create(
    request: Request,
    relationships: list[req.Relationship],
    service=Depends(GraphService),
) -> response.Concept:
    try:
        incoming = de.Relationship.from_json_ld_list(await request.json())
        lst = await service.relationships_create(incoming)
        return [response.Relationship(**obj.to_json_ld()) for obj in lst]
    except de.DuplicateRelationship as exc:
        return JSONResponse(
            status_code=409,
            content={
                "message": str(exc),
            },
        )
    except (
        de.HierarchicRelationshipAcrossConceptScheme,
        de.RelationshipsReferencesConceptScheme,
    ) as exc:
        return JSONResponse(
            status_code=422,
            content={
                "message": str(exc),
            },
        )


@router.put(
    Paths.relationship,
    summary="Update a list of Relationship objects",
    response_model=list[response.Relationship],
    response_model_exclude_unset=True,
)
async def relationships_update(
    request: Request,
    relationships: list[req.Relationship],
    service=Depends(GraphService),
) -> response.Concept:
    try:
        incoming = de.Relationship.from_json_ld_list(await request.json())
        lst = await service.relationships_update(incoming)
        return [response.Relationship(**obj.to_json_ld()) for obj in lst]
    except de.RelationshipNotFoundError as exc:
        return JSONResponse(
            status_code=404,
            content={
                "message": str(exc),
            },
        )
    except de.HierarchicRelationshipAcrossConceptScheme as exc:
        return JSONResponse(
            status_code=422,
            content={
                "message": str(exc),
            },
        )


@router.delete(
    Paths.relationship,
    summary="Delete a list of Relationship objects",
)
async def relationship_delete(
    request: Request,
    relationships: list[req.Relationship],
    service=Depends(GraphService),
) -> JSONResponse:
    incoming = de.Relationship.from_json_ld_list(await request.json())
    count = await service.relationships_delete(incoming)
    return JSONResponse(
        status_code=200,
        content={
            "message": "Relationships (possibly) deleted",
            "count": count,
        },
    )


# Correspondence


@router.get(
    Paths.correspondence,
    summary="Get a Correspondence object",
    response_model=response.Correspondence,
    responses={404: {"model": response.ErrorMessage}},
)
async def correspondence_get(
    iri: str,
    service=Depends(GraphService),
) -> response.Correspondence:
    try:
        obj = await service.correspondence_get(iri=iri)
        return response.Correspondence(**obj.to_json_ld())
    except de.CorrespondenceNotFoundError:
        return JSONResponse(
            status_code=404,
            content={
                "message": f"Correspondence with IRI '{iri}' not found",
                "detail": {"iri": iri},
            },
        )


@router.post(
    Paths.correspondence,
    summary="Create a Correspondence object",
    response_model=response.Correspondence,
)
async def correspondence_create(
    request: Request,
    correspondence: req.Correspondence,
    service=Depends(GraphService),
) -> response.Correspondence:
    try:
        corr = de.Correspondence.from_json_ld(await request.json())
        result = await service.correspondence_create(corr)
        return response.Correspondence(**result.to_json_ld())
    except de.DuplicateIRI:
        return JSONResponse(
            status_code=409,
            content={
                "message": f"Resource with `@id` already exists",
                "detail": {"@id": corr.id_},
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
        mapping = {
            de.Concept: "concept_get",
            de.ConceptScheme: "concept_scheme_get",
        }
        return RedirectResponse(
            url="{}?iri={}".format(request.url_for(mapping[object_type]), quote_plus(iri))
        )
    except de.NotFoundError:
        raise HTTPException(status_code=404, detail=f"KOS graph object with iri `{iri}` not found")
