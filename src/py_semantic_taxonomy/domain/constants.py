SKOS = "http://www.w3.org/2004/02/skos/core#"
DCTERMS = "http://purl.org/dc/terms/"
OWL = "http://www.w3.org/2002/07/owl#"


SKOS_RELATIONSHIP_PREDICATES = {
    f"{SKOS}narrowerTransitive",
    f"{SKOS}narrower",
    f"{SKOS}broaderTransitive",
    f"{SKOS}broader",
    f"{SKOS}topConceptOf",
    f"{SKOS}hasTopConcept",
}

RDF_MAPPING = {
    "id_": "@id",
    "types": "@type",
    "schemes": f"{SKOS}inScheme",
    "pref_labels": f"{SKOS}prefLabel",
    "definitions": f"{SKOS}definition",
    "notations": f"{SKOS}notation",
    "alt_labels": f"{SKOS}altLabel",
    "hidden_labels": f"{SKOS}hiddenLabel",
    "change_notes": f"{SKOS}changeNote",
    "history_notes": f"{SKOS}historyNote",
    "editorial_notes": f"{SKOS}editorialNote",
    "created": f"{DCTERMS}created",
    "creators": f"{DCTERMS}creator",
    "version": f"{OWL}versionInfo",
}
