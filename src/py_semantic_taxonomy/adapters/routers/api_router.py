from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic_settings import BaseSettings

import py_semantic_taxonomy.adapters.routers.request_dto as req
import py_semantic_taxonomy.adapters.routers.response_dto as response
from py_semantic_taxonomy.cfg import get_settings
from py_semantic_taxonomy.dependencies import get_graph_service, get_search_service
from py_semantic_taxonomy.domain import entities as de
from py_semantic_taxonomy.domain.constants import API_VERSION_PREFIX, APIPaths
from py_semantic_taxonomy import __version__

api_router = APIRouter(prefix=API_VERSION_PREFIX)


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


async def verify_auth_token(
    x_pyst_auth_token: Annotated[str, Header()] = "", settings: BaseSettings = Depends(get_settings)
):
    if x_pyst_auth_token != settings.auth_token:
        raise HTTPException(status_code=400, detail="X-PyST-Auth-Token header missing or invalid")

# Status


@api_router.get(
    APIPaths.status,
    summary="Get a status report for PyST server",
    response_model=response.ServerStatus,
    tags=["Status"],
)
async def server_status(
    search=Depends(get_search_service),
) -> response.ServerStatus:
    return response.ServerStatus(
        version=__version__,
        search=bool(search.is_configured)
    )


# Search


@api_router.get(
    APIPaths.search,
    summary="Search for `Concept` objects",
    response_model=list[de.SearchResult],
    tags=["Concept"],
    responses={503: {"description": "Search engine not available"}},
)
async def concept_search(
    query: str,
    language: str,
    semantic: bool = True,
    service=Depends(get_search_service),
) -> list[de.SearchResult]:
    try:
        results = await service.search(query=query, language=language, semantic=semantic)
        return results
    except de.SearchNotConfigured:
        raise HTTPException(status_code=503, detail="Search engine not available")
    except de.UnknownLanguage:
        raise HTTPException(
            status_code=422, detail="Search engine not configured for given language"
        )


@api_router.get(
    APIPaths.suggest,
    summary="Suggestion search for `Concept` objects",
    response_model=list[de.SearchResult],
    tags=["Concept"],
    responses={503: {"description": "Search engine not available"}},
)
async def concept_suggest(
    query: str,
    language: str,
    service=Depends(get_search_service),
) -> list[de.SearchResult]:
    try:
        results = await service.suggest(query=query, language=language)
        return results
    except de.SearchNotConfigured:
        raise HTTPException(status_code=503, detail="Search engine not available")
    except de.UnknownLanguage:
        raise HTTPException(
            status_code=422, detail="Search engine not configured for given language"
        )


# Concept


@api_router.get(
    APIPaths.concept_all,
    summary="Get a list of concept objects with optional filters.",
    response_model=list[response.Concept],
    tags=["Concept"],
)
async def concept_all_get(
    concept_scheme_iri: str | None = None,
    top_concepts_only: bool = False,
    service=Depends(get_graph_service),
) -> list[response.Concept]:
    """
    Retrieve a list of `Concept` objects.

    The list can be filtered to a given concept scheme by using the URL parameter
    `concept_scheme_iri=<iri>`.

    The list can be further filtered to only be top concepts of the given concept scheme (if
    `concept_scheme_iri` is specified) with the URL parameter `top_concepts_only=<bool>`. If
    `concept_scheme_iri` is not specified, `top_concepts_only` *has no effect*.
    """
    results = await service.concept_get_all(
        concept_scheme_iri=concept_scheme_iri, top_concepts_only=top_concepts_only
    )
    return [response.Concept(**obj.to_json_ld()) for obj in results]


@api_router.get(
    APIPaths.concept,
    summary="Get a `Concept` object",
    response_model=response.Concept,
    tags=["Concept"],
    responses={404: {"description": "Resource not found"}},
)
async def concept_get(
    iri: str,
    service=Depends(get_graph_service),
) -> response.Concept:
    try:
        obj = await service.concept_get(iri=iri)
        return response.Concept(**obj.to_json_ld())
    except de.ConceptNotFoundError:
        raise HTTPException(status_code=404, detail=f"Concept with IRI `{iri}` not found")


@api_router.post(
    APIPaths.concept,
    summary="Create a `Concept` object",
    response_model=response.Concept,
    dependencies=[Depends(verify_auth_token)],
    tags=["Concept"],
    responses={409: {"description": "Resource already exists"}},
)
async def concept_create(
    request: Request,
    concept: req.ConceptCreate,
    service=Depends(get_graph_service),
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
        de.HierarchyConflict,
    ) as err:
        raise HTTPException(status_code=422, detail=str(err))


@api_router.put(
    APIPaths.concept,
    summary="Update a `Concept` object",
    response_model=response.Concept,
    dependencies=[Depends(verify_auth_token)],
    tags=["Concept"],
    responses={404: {"description": "Resource not found"}},
)
async def concept_update(
    request: Request,
    concept: req.ConceptUpdate,
    service=Depends(get_graph_service),
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
        de.HierarchyConflict,
    ) as err:
        raise HTTPException(status_code=422, detail=str(err))


@api_router.delete(
    APIPaths.concept,
    summary="Delete a `Concept` object",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(verify_auth_token)],
    tags=["Concept"],
    responses={404: {"description": "Resource not found"}},
)
async def concept_delete(
    iri: str,
    service=Depends(get_graph_service),
):
    try:
        await service.concept_delete(iri=iri)
    except de.ConceptNotFoundError as err:
        raise HTTPException(status_code=404, detail=str(err))


# Concept Scheme


@api_router.get(
    APIPaths.concept_scheme_all,
    summary="Get all concept schemes",
    response_model=list[response.ConceptScheme],
    tags=["ConceptScheme"],
)
async def concept_scheme_get_all(
    service=Depends(get_graph_service),
) -> list[response.ConceptScheme]:
    concept_schemes = await service.concept_scheme_get_all()
    return [response.ConceptScheme(**cs.to_json_ld()) for cs in concept_schemes]


@api_router.get(
    APIPaths.concept_scheme,
    summary="Get a `ConceptScheme` object",
    response_model=response.ConceptScheme,
    tags=["ConceptScheme"],
    responses={404: {"description": "Resource not found"}},
)
async def concept_scheme_get(
    iri: str,
    service=Depends(get_graph_service),
) -> response.ConceptScheme:
    try:
        obj = await service.concept_scheme_get(iri=iri)
        return response.ConceptScheme(**obj.to_json_ld())
    except de.ConceptSchemeNotFoundError:
        raise HTTPException(status_code=404, detail=f"Concept Scheme with IRI `{iri}` not found")


@api_router.post(
    APIPaths.concept_scheme,
    summary="Create a `ConceptScheme` object",
    response_model=response.ConceptScheme,
    dependencies=[Depends(verify_auth_token)],
    tags=["ConceptScheme"],
)
async def concept_scheme_create(
    request: Request,
    concept_scheme: req.ConceptScheme,
    service=Depends(get_graph_service),
    responses={409: {"description": "Resource already exists"}},
) -> response.ConceptScheme:
    try:
        cs = de.ConceptScheme.from_json_ld(await request.json())
        result = await service.concept_scheme_create(cs)
        return response.ConceptScheme(**result.to_json_ld())
    except de.DuplicateIRI:
        raise HTTPException(
            status_code=409, detail=f"Concept Scheme with IRI `{cs.id_}` already exists"
        )


@api_router.put(
    APIPaths.concept_scheme,
    summary="Update a `ConceptScheme` object",
    response_model=response.ConceptScheme,
    dependencies=[Depends(verify_auth_token)],
    tags=["ConceptScheme"],
)
async def concept_scheme_update(
    request: Request,
    concept_scheme: req.ConceptScheme,
    service=Depends(get_graph_service),
    responses={404: {"description": "Resource not found"}},
) -> response.ConceptScheme:
    try:
        cs = de.ConceptScheme.from_json_ld(await request.json())
        result = await service.concept_scheme_update(cs)
        return response.ConceptScheme(**result.to_json_ld())
    except de.ConceptSchemeNotFoundError:
        raise HTTPException(status_code=404, detail=f"Concept Scheme with IRI `{cs.id_}` not found")


@api_router.delete(
    APIPaths.concept_scheme,
    summary="Delete a `ConceptScheme` object",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(verify_auth_token)],
    tags=["ConceptScheme"],
    responses={404: {"description": "Resource not found"}},
)
async def concept_scheme_delete(
    iri: str,
    service=Depends(get_graph_service),
):
    try:
        await service.concept_scheme_delete(iri=iri)
    except de.ConceptSchemeNotFoundError as err:
        raise HTTPException(status_code=404, detail=str(err))


# Relationship


@api_router.get(
    APIPaths.relationship,
    summary="Get a list of `Concept` relationships",
    response_model=list[response.Relationship],
    response_model_exclude_unset=True,
    tags=["Concept"],
)
async def relationships_get(
    iri: str,
    source: bool = True,
    target: bool = False,
    service=Depends(get_graph_service),
) -> list[response.Relationship]:
    lst = await service.relationships_get(iri=iri, source=source, target=target)
    return [response.Relationship(**obj.to_json_ld()) for obj in lst]


@api_router.post(
    APIPaths.relationship,
    summary="Create a list of `Concept` relationships",
    response_model=list[response.Relationship],
    response_model_exclude_unset=True,
    dependencies=[Depends(verify_auth_token)],
    tags=["Concept"],
    responses={409: {"description": "Resource already exists"}},
)
async def relationships_create(
    request: Request,
    relationships: list[req.Relationship],
    service=Depends(get_graph_service),
) -> list[response.Relationship]:
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


@api_router.delete(
    APIPaths.relationship,
    summary="Delete a list of `Concept` relationships",
    dependencies=[Depends(verify_auth_token)],
    tags=["Concept"],
)
async def relationship_delete(
    request: Request,
    relationships: list[req.Relationship],
    service=Depends(get_graph_service),
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


@api_router.get(
    APIPaths.correspondence_all,
    summary="Get all `Correspondence` objects",
    response_model=list[response.Correspondence],
    tags=["Correspondence"],
)
async def correspondence_get_all(
    service=Depends(get_graph_service),
) -> list[response.Correspondence]:
    correspondences = await service.correspondence_get_all()
    return [response.Correspondence(**obj.to_json_ld()) for obj in correspondences]


@api_router.get(
    APIPaths.correspondence,
    summary="Get a `Correspondence` object",
    response_model=response.Correspondence,
    tags=["Correspondence"],
    responses={404: {"description": "Resource not found"}},
)
async def correspondence_get(
    iri: str,
    service=Depends(get_graph_service),
) -> response.Correspondence:
    try:
        obj = await service.correspondence_get(iri=iri)
        return response.Correspondence(**obj.to_json_ld())
    except de.CorrespondenceNotFoundError:
        raise HTTPException(status_code=404, detail=f"Correspondence with IRI `{iri}` not found")


@api_router.post(
    APIPaths.correspondence,
    summary="Create a `Correspondence` object",
    response_model=response.Correspondence,
    dependencies=[Depends(verify_auth_token)],
    tags=["Correspondence"],
    responses={409: {"description": "Resource already exists"}},
)
async def correspondence_create(
    request: Request,
    correspondence: req.Correspondence,
    service=Depends(get_graph_service),
) -> response.Correspondence:
    try:
        corr = de.Correspondence.from_json_ld(await request.json())
        result = await service.correspondence_create(corr)
        return response.Correspondence(**result.to_json_ld())
    except de.DuplicateIRI:
        raise HTTPException(
            status_code=409, detail=f"Correspondence with IRI `{corr.id_}` already exists"
        )


@api_router.put(
    APIPaths.correspondence,
    summary="Update a `Correspondence` object",
    response_model=response.Correspondence,
    dependencies=[Depends(verify_auth_token)],
    tags=["Correspondence"],
    responses={404: {"description": "Resource not found"}},
)
async def correspondence_update(
    request: Request,
    concept_scheme: req.Correspondence,
    service=Depends(get_graph_service),
) -> response.Correspondence:
    try:
        corr = de.Correspondence.from_json_ld(await request.json())
        result = await service.correspondence_update(corr)
        return response.Correspondence(**result.to_json_ld())
    except de.CorrespondenceNotFoundError:
        raise HTTPException(
            status_code=404, detail=f"Correspondence with IRI `{corr.id_}` not found"
        )


@api_router.delete(
    APIPaths.correspondence,
    summary="Delete a `Correspondence` object",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(verify_auth_token)],
    tags=["Correspondence"],
    responses={404: {"description": "Resource not found"}},
)
async def correspondence_delete(
    iri: str,
    service=Depends(get_graph_service),
):
    try:
        await service.correspondence_delete(iri=iri)
    except de.CorrespondenceNotFoundError as err:
        raise HTTPException(status_code=404, detail=str(err))


# Association


@api_router.get(
    APIPaths.association_all,
    summary="Get an `Association` object",
    response_model=list[response.Association],
    tags=["ConceptAssociation"],
    responses={404: {"description": "Resource not found"}},
)
async def association_get_all(
    correspondence_iri: str | None = None,
    source_concept_iri: str | None = None,
    target_concept_iri: str | None = None,
    kind: de.AssociationKind | None = None,
    service=Depends(get_graph_service),
) -> list[response.Association]:
    results = await service.association_get_all(
        correspondence_iri=correspondence_iri,
        source_concept_iri=source_concept_iri,
        target_concept_iri=target_concept_iri,
        kind=kind,
    )
    return [response.Association(**obj.to_json_ld()) for obj in results]


@api_router.get(
    APIPaths.association,
    summary="Get an `Association` object",
    response_model=response.Association,
    tags=["ConceptAssociation"],
    responses={404: {"description": "Resource not found"}},
)
async def association_get(
    iri: str,
    service=Depends(get_graph_service),
) -> response.Association:
    try:
        obj = await service.association_get(iri=iri)
        return response.Association(**obj.to_json_ld())
    except de.AssociationNotFoundError:
        raise HTTPException(status_code=404, detail=f"Association with IRI `{iri}` not found")


@api_router.post(
    APIPaths.association,
    summary="Create an `Association` object",
    response_model=response.Association,
    dependencies=[Depends(verify_auth_token)],
    tags=["ConceptAssociation"],
    responses={409: {"description": "Resource already exists"}},
)
async def association_create(
    request: Request,
    relationships: req.Association,
    service=Depends(get_graph_service),
) -> response.Association:
    try:
        incoming = de.Association.from_json_ld(await request.json())
        obj = await service.association_create(incoming)
        return response.Association(**obj.to_json_ld())
    except de.DuplicateIRI as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@api_router.delete(
    APIPaths.association,
    summary="Delete an `Association` object",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(verify_auth_token)],
    tags=["ConceptAssociation"],
    responses={404: {"description": "Resource not found"}},
)
async def association_delete(
    iri: str,
    service=Depends(get_graph_service),
):
    try:
        await service.association_delete(iri=iri)
    except de.AssociationNotFoundError as err:
        raise HTTPException(status_code=404, detail=str(err))


@api_router.post(
    APIPaths.made_of,
    summary="Add some `Correspondence` `madeOf` links",
    response_model=response.Correspondence,
    dependencies=[Depends(verify_auth_token)],
    tags=["Correspondence"],
    responses={404: {"description": "Resource not found"}},
)
async def made_of_add(
    request: Request,
    made_of: req.MadeOf,
    service=Depends(get_graph_service),
) -> response.Correspondence:
    try:
        made_of = de.MadeOf.from_json_ld(await request.json())
        corr = await service.made_of_add(made_of)
        return response.Correspondence(**corr.to_json_ld())
    except de.CorrespondenceNotFoundError:
        raise HTTPException(
            status_code=404, detail=f"Correspondence with IRI `{made_of.id_}` not found"
        )


@api_router.delete(
    APIPaths.made_of,
    summary="Remove some `Correspondence` `madeOf` links",
    response_model=response.Correspondence,
    dependencies=[Depends(verify_auth_token)],
    tags=["Correspondence"],
    responses={404: {"description": "Resource not found"}},
)
async def made_of_remove(
    request: Request,
    made_of: req.MadeOf,
    service=Depends(get_graph_service),
) -> response.Correspondence:
    try:
        made_of = de.MadeOf.from_json_ld(await request.json())
        corr = await service.made_of_remove(made_of)
        return response.Correspondence(**corr.to_json_ld())
    except de.CorrespondenceNotFoundError:
        raise HTTPException(
            status_code=404, detail=f"Correspondence with IRI `{made_of.id_}` not found"
        )
