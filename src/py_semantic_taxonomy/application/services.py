from fastapi.params import Depends

from py_semantic_taxonomy.adapters.routers.dependencies import get_kos_graph
from py_semantic_taxonomy.domain.constants import SKOS_HIERARCHICAL_RELATIONSHIP_PREDICATES
from py_semantic_taxonomy.domain.entities import (
    Association,
    AssociationNotFoundError,
    Concept,
    ConceptNotFoundError,
    ConceptScheme,
    ConceptSchemeNotFoundError,
    ConceptSchemesNotInDatabase,
    Correspondence,
    CorrespondenceNotFoundError,
    DuplicateRelationship,
    GraphObject,
    HierarchicRelationshipAcrossConceptScheme,
    MadeOf,
    Relationship,
    RelationshipsInCurrentConceptScheme,
    RelationshipsReferencesConceptScheme,
)
from py_semantic_taxonomy.domain.ports import KOSGraph


class GraphService:
    def __init__(self, graph: KOSGraph = Depends(get_kos_graph)):
        self.graph = graph

    async def get_object_type(self, iri: str) -> GraphObject:
        return await self.graph.get_object_type(iri=iri)

    # Concept

    async def concept_get(self, iri: str) -> Concept:
        return await self.graph.concept_get(iri=iri)

    async def _concept_refers_to_concept_scheme_in_database(self, concept: Concept) -> None:
        concept_schemes = set(await self.concept_scheme_get_all_iris())
        given_cs = {cs["@id"] for cs in concept.schemes}
        if not given_cs.intersection(concept_schemes):
            raise ConceptSchemesNotInDatabase(
                f"At least one of the specified concept schemes must be in the database: {given_cs}"
            )

    async def concept_create(
        self, concept: Concept, relationships: list[Relationship] = []
    ) -> Concept:
        await self._concept_refers_to_concept_scheme_in_database(concept)

        await self.graph.concept_create(concept=concept)
        if relationships:
            try:
                await self.relationships_create(relationships)
            except (HierarchicRelationshipAcrossConceptScheme, DuplicateRelationship) as err:
                await self.concept_delete(concept.id_)
                raise err
        return concept

    async def concept_update(self, concept: Concept) -> Concept:
        await self._concept_refers_to_concept_scheme_in_database(concept)

        current = await self.graph.concept_get(concept.id_)
        current_schemes = {cs["@id"] for cs in current.schemes}
        new_schemes = {cs["@id"] for cs in concept.schemes}
        if current_schemes.difference(new_schemes):
            # Can remove a ConceptScheme only if it doesn't create cross-scheme hierarchical
            # relationships
            rel_schemes = (
                await self.graph.known_concept_schemes_for_concept_hierarchical_relationships(
                    concept.id_
                )
            )
            if missing := set(rel_schemes).difference(new_schemes):
                raise RelationshipsInCurrentConceptScheme(
                    f"Update asked to change concept schemes, but existing concept scheme {missing} had hierarchical relationships."
                )
        return await self.graph.concept_update(concept=concept)

    async def concept_delete(self, iri: str) -> None:
        rowcount = await self.graph.concept_delete(iri=iri)
        if not rowcount:
            raise ConceptNotFoundError(f"Concept with IRI `{iri}` not found")
        return

    # Concept Scheme

    async def concept_scheme_get(self, iri: str) -> ConceptScheme:
        return await self.graph.concept_scheme_get(iri=iri)

    async def concept_scheme_get_all_iris(self) -> list[str]:
        return await self.graph.concept_scheme_get_all_iris()

    async def concept_scheme_create(self, concept_scheme: ConceptScheme) -> ConceptScheme:
        return await self.graph.concept_scheme_create(concept_scheme=concept_scheme)

    async def concept_scheme_update(self, concept_scheme: ConceptScheme) -> ConceptScheme:
        return await self.graph.concept_scheme_update(concept_scheme=concept_scheme)

    async def concept_scheme_delete(self, iri: str) -> None:
        rowcount = await self.graph.concept_scheme_delete(iri=iri)
        if not rowcount:
            raise ConceptSchemeNotFoundError(f"Concept Scheme with IRI `{iri}` not found")
        return

    # Relationships

    async def relationships_get(
        self, iri: str, source: bool = True, target: bool = False
    ) -> list[Relationship]:
        return await self.graph.relationships_get(iri=iri, source=source, target=target)

    async def _relationships_check_source_target_share_known_concept_scheme(
        self, relationships: list[Relationship]
    ) -> None:
        for rel in relationships:
            if rel.predicate in SKOS_HIERARCHICAL_RELATIONSHIP_PREDICATES and not (
                await self.graph.relationship_source_target_share_known_concept_scheme(rel)
            ):
                raise HierarchicRelationshipAcrossConceptScheme(
                    f"Hierarchical relationship between `{rel.source}` and `{rel.target}` crosses Concept Schemes. Use an associative relationship like `skos:broadMatch` instead."
                )

    async def relationships_create(self, relationships: list[Relationship]) -> list[Relationship]:
        concept_schemes = await self.concept_scheme_get_all_iris()
        for rel in relationships:
            if rel.source in concept_schemes:
                raise RelationshipsReferencesConceptScheme(
                    f"Relationship `{rel}` source refers to concept scheme `{rel.source}`"
                )
            if rel.target in concept_schemes:
                raise RelationshipsReferencesConceptScheme(
                    f"Relationship `{rel}` target refers to concept scheme `{rel.target}`"
                )

        await self._relationships_check_source_target_share_known_concept_scheme(relationships)
        return await self.graph.relationships_create(relationships)

    async def relationships_delete(self, relationships: list[Relationship]) -> int:
        return await self.graph.relationships_delete(relationships)

    # Correspondence

    async def correspondence_get(self, iri: str) -> Correspondence:
        return await self.graph.correspondence_get(iri=iri)

    async def correspondence_create(self, correspondence: Correspondence) -> Correspondence:
        return await self.graph.correspondence_create(correspondence=correspondence)

    async def correspondence_update(self, correspondence: Correspondence) -> Correspondence:
        return await self.graph.correspondence_update(correspondence=correspondence)

    async def correspondence_delete(self, iri: str) -> None:
        rowcount = await self.graph.correspondence_delete(iri=iri)
        if not rowcount:
            raise CorrespondenceNotFoundError(f"Correspondence with IRI `{iri}` not found")
        return

    async def made_of_add(self, made_of: MadeOf) -> Correspondence:
        return await self.graph.made_of_add(made_of)

    async def made_of_remove(self, made_of: MadeOf) -> Correspondence:
        return await self.graph.made_of_remove(made_of)

    # Association

    async def association_get(self, iri: str) -> Association:
        return await self.graph.association_get(iri=iri)

    async def association_create(self, association: Association) -> Association:
        return await self.graph.association_create(association=association)

    async def association_delete(self, iri: str) -> None:
        rowcount = await self.graph.association_delete(iri=iri)
        if not rowcount:
            raise AssociationNotFoundError(f"Association with IRI `{iri}` not found")
        return
