from enum import StrEnum
from urllib.parse import quote_plus, urljoin

from fastapi import APIRouter, Depends, HTTPException, Request, status
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
    correspondence = "/correspondence/"
    association = "/association/"


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
)
async def concept_get(
    iri: str,
    service=Depends(GraphService),
) -> response.Concept:
    try:
        obj = await service.concept_get(iri=iri)
        return response.Concept(**obj.to_json_ld())
    except de.ConceptNotFoundError:
        raise HTTPException(status_code=404, detail=f"Concept with IRI `{iri}` not found")


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
        concept_obj = de.Concept.from_json_ld(incoming_data)
        relationships = de.Relationship.from_json_ld(incoming_data)
        result = await service.concept_create(concept=concept_obj, relationships=relationships)
        return response.Concept(**result.to_json_ld())
    except de.DuplicateIRI:
        raise HTTPException(
            status_code=409, detail=f"Concept with IRI `{concept_obj.id_}` already exists"
        )
    except (
        de.HierarchicRelationshipAcrossConceptScheme,
        de.DuplicateRelationship,
        de.ConceptSchemesNotInDatabase,
    ) as err:
        raise HTTPException(status_code=422, detail=str(err))


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
        raise HTTPException(
            status_code=404, detail=f"Concept with IRI `{concept_obj.id_}` not found"
        )
    except (
        de.RelationshipsInCurrentConceptScheme,
        de.ConceptSchemesNotInDatabase,
    ) as err:
        raise HTTPException(status_code=422, detail=str(err))


@router.delete(
    Paths.concept,
    summary="Delete a Concept object",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def concept_delete(
    iri: str,
    service=Depends(GraphService),
):
    try:
        await service.concept_delete(iri=iri)
    except de.ConceptNotFoundError as err:
        raise HTTPException(status_code=404, detail=str(err))


# Concept Scheme


@router.get(
    Paths.concept_scheme,
    summary="Get a ConceptScheme object",
    response_model=response.ConceptScheme,
)
async def concept_scheme_get(
    iri: str,
    service=Depends(GraphService),
) -> response.ConceptScheme:
    try:
        obj = await service.concept_scheme_get(iri=iri)
        return response.ConceptScheme(**obj.to_json_ld())
    except de.ConceptSchemeNotFoundError:
        raise HTTPException(status_code=404, detail=f"Concept Scheme with IRI `{iri}` not found")


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
        raise HTTPException(
            status_code=409, detail=f"Concept Scheme with IRI `{cs.id_}` already exists"
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
        raise HTTPException(status_code=404, detail=f"Concept Scheme with IRI `{cs.id_}` not found")


@router.delete(
    Paths.concept_scheme,
    summary="Delete a Concept Scheme object",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def concept_scheme_delete(
    iri: str,
    service=Depends(GraphService),
):
    try:
        await service.concept_scheme_delete(iri=iri)
    except de.ConceptSchemeNotFoundError as err:
        raise HTTPException(status_code=404, detail=str(err))


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
) -> response.Relationship:
    try:
        incoming = de.Relationship.from_json_ld_list(await request.json())
        lst = await service.relationships_create(incoming)
        return [response.Relationship(**obj.to_json_ld()) for obj in lst]
    except de.DuplicateRelationship as err:
        raise HTTPException(status_code=409, detail=str(err))
    except (
        de.HierarchicRelationshipAcrossConceptScheme,
        de.RelationshipsReferencesConceptScheme,
    ) as err:
        raise HTTPException(status_code=422, detail=str(err))


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
            "detail": "Relationships (possibly) deleted",
            "count": count,
        },
    )


# Correspondence


@router.get(
    Paths.correspondence,
    summary="Get a Correspondence object",
    response_model=response.Correspondence,
)
async def correspondence_get(
    iri: str,
    service=Depends(GraphService),
) -> response.Correspondence:
    try:
        obj = await service.correspondence_get(iri=iri)
        return response.Correspondence(**obj.to_json_ld())
    except de.CorrespondenceNotFoundError:
        raise HTTPException(status_code=404, detail=f"Correspondence with IRI `{iri}` not found")


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
        raise HTTPException(
            status_code=409, detail=f"Correspondence with IRI `{corr.id_}` already exists"
        )


@router.put(
    Paths.correspondence,
    summary="Update a Correspondence object",
    response_model=response.Correspondence,
)
async def correspondence_update(
    request: Request,
    concept_scheme: req.Correspondence,
    service=Depends(GraphService),
) -> response.Correspondence:
    try:
        corr = de.Correspondence.from_json_ld(await request.json())
        result = await service.correspondence_update(corr)
        return response.Correspondence(**result.to_json_ld())
    except de.CorrespondenceNotFoundError:
        raise HTTPException(
            status_code=404, detail=f"Correspondence with IRI `{corr.id_}` not found"
        )


@router.delete(
    Paths.correspondence,
    summary="Delete a Correspondence object",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def correspondence_delete(
    iri: str,
    service=Depends(GraphService),
):
    try:
        await service.correspondence_delete(iri=iri)
    except de.CorrespondenceNotFoundError as err:
        raise HTTPException(status_code=404, detail=str(err))


# Association


@router.get(
    Paths.association,
    summary="Get a Association object",
    response_model=response.Association,
)
async def association_get(
    iri: str,
    service=Depends(GraphService),
) -> response.Association:
    try:
        obj = await service.association_get(iri=iri)
        return response.Association(**obj.to_json_ld())
    except de.AssociationNotFoundError:
        raise HTTPException(status_code=404, detail=f"Association with IRI `{iri}` not found")


@router.post(
    Paths.association,
    summary="Create an Association object",
    response_model=response.Association,
)
async def association_create(
    request: Request,
    relationships: req.Association,
    service=Depends(GraphService),
) -> response.Association:
    try:
        incoming = de.Association.from_json_ld(await request.json())
        obj = await service.association_create(incoming)
        return response.Association(**obj.to_json_ld())
    except de.DuplicateIRI as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.delete(
    Paths.association,
    summary="Delete an Association object",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def association_delete(
    iri: str,
    service=Depends(GraphService),
):
    try:
        await service.association_delete(iri=iri)
    except de.AssociationNotFoundError as err:
        raise HTTPException(status_code=404, detail=str(err))


# TBD: Add in static route before generic catch-all function


@router.get(
    Paths.catchall,
    summary="Get a KOS graph object which shares the same base URL as PyST",
)
async def generic_get_from_iri(
    request: Request, _: str, service=Depends(GraphService)
) -> RedirectResponse:
    try:
        iri = urljoin(str(request.base_url), request.url.path)
        object_type = await service.get_object_type(iri=iri)
        mapping = {
            de.Concept: "concept_get",
            de.ConceptScheme: "concept_scheme_get",
            de.Correspondence: "correspondence_get",
        }
        return RedirectResponse(
            url="{}?iri={}".format(request.url_for(mapping[object_type]), quote_plus(iri))
        )
    except de.NotFoundError:
        raise HTTPException(status_code=404, detail=f"KOS graph object with IRI `{iri}` not found")
