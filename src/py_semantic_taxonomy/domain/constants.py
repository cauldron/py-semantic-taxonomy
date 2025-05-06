import enum

BIBO = "http://purl.org/ontology/bibo/"
DCTERMS = "http://purl.org/dc/terms/"
OWL = "http://www.w3.org/2002/07/owl#"
SKOS = "http://www.w3.org/2004/02/skos/core#"
XKOS = "http://rdf-vocabulary.ddialliance.org/xkos#"

SKOS_ASSOCIATE_RELATIONSHIP_PREDICATES = {
    f"{SKOS}broadMatch",
    f"{SKOS}closeMatch",
    f"{SKOS}exactMatch",
    f"{SKOS}narrowMatch",
    f"{SKOS}relatedMatch",
}
SKOS_HIERARCHICAL_RELATIONSHIP_PREDICATES = {
    f"{SKOS}narrowerTransitive",
    f"{SKOS}narrower",
    f"{SKOS}broaderTransitive",
    f"{SKOS}broader",
}
SKOS_RELATIONSHIP_PREDICATES = SKOS_ASSOCIATE_RELATIONSHIP_PREDICATES.union(
    SKOS_HIERARCHICAL_RELATIONSHIP_PREDICATES
)


RDF_MAPPING: dict[str, str] = {
    "id_": "@id",
    "types": "@type",
    "alt_labels": f"{SKOS}altLabel",
    "change_notes": f"{SKOS}changeNote",
    "compares": f"{XKOS}compares",
    "created": f"{DCTERMS}created",
    "creators": f"{DCTERMS}creator",
    "definitions": f"{SKOS}definition",
    "editorial_notes": f"{SKOS}editorialNote",
    "hidden_labels": f"{SKOS}hiddenLabel",
    "history_notes": f"{SKOS}historyNote",
    "made_ofs": f"{XKOS}madeOf",
    "notations": f"{SKOS}notation",
    "pref_labels": f"{SKOS}prefLabel",
    "schemes": f"{SKOS}inScheme",
    "source_concepts": f"{XKOS}sourceConcept",
    "status": f"{BIBO}status",
    "target_concepts": f"{XKOS}targetConcept",
    "top_concept_of": f"{SKOS}topConceptOf",
    "version": f"{OWL}versionInfo",
}


class RelationshipVerbs(enum.StrEnum):
    broader = f"{SKOS}broader"
    narrower = f"{SKOS}narrower"
    exact_match = f"{SKOS}exactMatch"
    close_match = f"{SKOS}closeMatch"
    broad_match = f"{SKOS}broadMatch"
    narrow_match = f"{SKOS}narrowMatch"
    related_match = f"{SKOS}relatedMatch"


class AssociationKind(enum.StrEnum):
    simple = "simple"
    conditional = "conditional"


API_VERSION_PREFIX = "/api/v1"


class APIPaths(enum.StrEnum):
    status = "/status/"
    concept = "/concepts/{iri:path}"
    concept_all = "/concepts/"
    concept_scheme = "/concept_schemes/{iri:path}"
    concept_scheme_all = "/concept_schemes/"
    relationship = "/relationships/"
    correspondence = "/correspondences/{iri:path}"
    correspondence_all = "/correspondences/"
    association = "/associations/{iri:path}"
    association_all = "/associations/"
    made_of = "/made_ofs/"
    search = "/concepts/search/"
    suggest = "/concepts/suggest/"
