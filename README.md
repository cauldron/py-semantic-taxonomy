# py-semantic-taxonomy

[![PyPI](https://img.shields.io/pypi/v/py-semantic-taxonomy.svg)][pypi status]
[![Status](https://img.shields.io/pypi/status/py-semantic-taxonomy.svg)][pypi status]
[![Python Version](https://img.shields.io/pypi/pyversions/py-semantic-taxonomy)][pypi status]
[![License](https://img.shields.io/pypi/l/py-semantic-taxonomy)][license]

[![Read the documentation at https://py-semantic-taxonomy.readthedocs.io/](https://img.shields.io/readthedocs/py-semantic-taxonomy/latest.svg?label=Read%20the%20Docs)][read the docs]
[![Tests](https://github.com/cauldron/py-semantic-taxonomy/actions/workflows/python-test.yml/badge.svg)][tests]
[![Codecov](https://codecov.io/gh/cauldron/py-semantic-taxonomy/branch/main/graph/badge.svg)][codecov]

[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)][pre-commit]
[![Black](https://img.shields.io/badge/code%20style-black-000000.svg)][black]

[pypi status]: https://pypi.org/project/py-semantic-taxonomy/
[read the docs]: https://py-semantic-taxonomy.readthedocs.io/
[tests]: https://github.com/cauldron/py-semantic-taxonomy/actions?workflow=Tests
[codecov]: https://app.codecov.io/gh/cauldron/py-semantic-taxonomy
[pre-commit]: https://github.com/pre-commit/pre-commit
[black]: https://github.com/psf/black

## A Knowledge Organization System for Sustainability Assessment

### Background and Design Goals

This project has been based on our experiences using [SKOSMOS](https://skosmos.org/) for the [Sentier.dev taxonomic vocabulary](https://vocab.sentier.dev/en/). The RDF graph data structure and the SKOSMOS software itself work well for a certain set of use cases, but for our specific needs and user community, the choice of PHP, [Jena](https://jena.apache.org/), [SPARQL](https://en.wikipedia.org/wiki/SPARQL), and built-in search indexer all posed barriers to productive software and vocabulary maintenance.

In `py_semantic_taxonomy` we have the following goals:

* Native support for [XKOS](https://rdf-vocabulary.ddialliance.org/xkos.html) [`Correspondence` and `ConceptAssociation` classes](https://rdf-vocabulary.ddialliance.org/xkos.html#correspondences)
* A predictable, consistent, and validated set of properties and property uses for SKOS and XKOS terms
* Web interface to allow for browsing, and some basic data entry and editing
* API to allow for the complete set of [CRUD](https://en.wikipedia.org/wiki/Create,_read,_update_and_delete) operations
* API provides common graph queries without needing to learn SPARQL
* IRIs should resolve to HTML or RDF serialized resources, depending on requested media type
* Web interface supports high quality multilingual search without configuration pain
* Python client library which provides convenience wrappers around the API

This means that we want the following technical capabilities which are missing or more difficult than they need to be in SKOSMOS:

* A set of validation classes and functions for input data to ensure consistency in how objects are described.
* Better query performance by optimizing database structure and indices for a small set of needed edges
* Easy customization of the UI
* Pluggable search index

To put it another way, SKOSMOS is amazing software which can handle knowledge organization systems which are based on SKOS and already exist in a graph database, but which include a lot of inconsistency and variability - PyST has a reduced feature set, but allows for easier data editing, and is much pickier about incoming data.

### Concepts and Concept Schemes

The core objects in SKOS are [Concepts](https://www.w3.org/TR/skos-primer/#secconcept) and [Concept Schemes](https://www.w3.org/TR/skos-primer/#secscheme).

In `py_semantic_taxonomy`, we impose some <a name="additional-requirements">additional requirements</a> on top of those already present in the the SKOS and XKOS ontologies:

* All string literals **must specify** an `@language` code, and can specify an `@direction`.
* At least one preferred label (`http://www.w3.org/2004/02/skos/core#prefLabel`) is **required**.
* One only definition per language code is allowed.

For `ConceptScheme`, we also require the following:

* Exactly one `http://purl.org/dc/terms/created` value is specified
* Exactly one `http://www.w3.org/2002/07/owl#versionInfo` value is specified
* At least one definition (`http://www.w3.org/2004/02/skos/core#definition`) is given

In addition to the above requirements, we assume that concepts within a concept scheme have a strictly **transitive hierarchy** - e.g. if `A` is broader than `B`, and `B` is broader than `C`, then `A` is always broader than `C`. There is therefore no need to specify `broaderTransitive` or `narrowerTransitive`, these are implicit in the taxonomy graph. Similarly, as `broader` and `narrower` are reciprocal, API inputs should only specify `broader` relationships - giving both `broader` and `narrower` relationships will raise a `DuplicateRelationship` error.

For `Concept`, we enforce or expect the following SKOS ontology best practices:

* Each `Concept` must be in at least one `ConceptScheme`.
* `skos:related` is for *associative* relationships, not *hierarchical* ones. You shouldn't specify associative relationships for two concepts which are related through a transitive chain of either `skos:broader` or `skos:narrower` relationships, but this is not enforced.
* We do enforce that concepts with hierarchical relationships must share a concept scheme. Concepts also can't have relationships with themselves.
* The use of `skos:note` is discouraged (but not prohibited) in favor of the specific `skos:note` subclasses: `skos:scopeNote`, `skos:definition`, `skos:example`, `skos:historyNote`, `skos:editorialNote`, and `skos:changeNote`. Their use should follow the intended use as documented in the [SKOS Primer](https://www.w3.org/TR/skos-primer/#secdocumentation).
* Hierarchical relationships (`skos:narrower` and `skos:broader`) are reserved for concepts in the same concept scheme. Use `skos:narrowMatch` and `skos:broadMatch` for describing mappings to concepts outside the source concept scheme.
* `skos:notation` must be a [typed literal](https://www.w3.org/TR/2004/REC-rdf-concepts-20040210/#dfn-typed-literal) - not a string literal - and not include a `@language` tag. The default datatype should be `http://www.w3.org/1999/02/22-rdf-syntax-ns#PlainLiteral`.

Additionally, we **break from** [SKOS guidance](https://www.w3.org/TR/skos-reference/#L2613) to prohibit `skos:notation` having the same value as `skos:prefLabel`. A notation is ['a string of characters such as "T58.5" or "303.4833" used to uniquely identify a concept within the scope of a given concept scheme'](https://www.w3.org/TR/skos-reference/#L2064); this definition is inconsistent with [lexical labels](https://www.w3.org/TR/skos-reference/#L2831) like `skos:prefLabel`, which are human-readable and in a natural language. In our system, `skos:prefLabel` is required but `skos:notation` is optional.

### Tracking changes

We follow the SKOS Primer guidance on [documentary notes](https://www.w3.org/TR/skos-primer/#secdocumentation) for the fields `skos:changeNote`, `skos:editorialNote`, and `skos:historyNote`:

* `skos:changeNote` documents fine-grained changes to a concept, for the purposes of administration and maintenance, e.g. "Moved from under 'fruits' to under 'vegetables' by Horace Gray"
* `skos:editorialNote` supplies information that is an aid to administrative housekeeping, such as reminders of editorial work still to be done, e.g. "Check spelling with John Doe"
* `skos:historyNote` describes significant changes to the meaning or the form of a concept, e.g. "estab. 1975; heading was: Cruelty to children [1952-1975]"

All three of these notes are required to be RDF resources instead of string literals, and in addition to their values (`rdf:value`), they **must** also include a creator (`dcterms:creator`) and an issuance timestamp (`dcterms:issued`).

SKOS and XKOS don't provide constructs for tracking status. We have [chosen to use](https://github.com/cauldron/py-semantic-taxonomy/issues/16) a subset of the [BIBO](https://en.wikipedia.org/wiki/Bibliographic_Ontology) ontology, and support three different status options:

* draft (`http://purl.org/ontology/bibo/status/draft`)
* accepted (`http://purl.org/ontology/bibo/status/accepted`)
* rejected (`http://purl.org/ontology/bibo/status/rejected`)

The predicate verb is `http://purl.org/ontology/bibo/status`.

### Examples

Here is an example of a valid `ConceptScheme` in JSON-LD:

```json
{
  "@id": "http://data.europa.eu/xsp/cn2024/cn2024",
  "@type": ["http://www.w3.org/2004/02/skos/core#ConceptScheme"],
  "http://purl.org/dc/terms/created": [
    {
      "@type": "http://www.w3.org/2001/XMLSchema#dateTime",
      "@value": "2023-10-11T13:59:56"
    }
  ],
  "http://purl.org/dc/terms/creator": [
    {"@id": "http://publications.europa.eu/resource/authority/corporate-body/ESTAT"},
    {"@id": "http://publications.europa.eu/resource/authority/corporate-body/TAXUD"}
  ],
  "http://purl.org/ontology/bibo/status": [
    {"@id": "http://purl.org/ontology/bibo/status/accepted"}
  ],
  "http://www.w3.org/2002/07/owl#versionInfo": [{"@value": "2024"}],
  "http://www.w3.org/2004/02/skos/core#prefLabel": [
    {"@value": "Combined Nomenclature, 2024 (CN 2024)", "@language": "en"},
    {"@value": "Nomenclatura Combinada, 2024 (NC 2024)", "@language": "pt"}
  ],
  "http://www.w3.org/2004/02/skos/core#definition": [
    {
      "@value": "The main classification for the European ITGS (International trade in goods statistics)  is the Combined Nomenclature (CN). This is the primary nomenclature as it is the one used by the EU Member States to collect detailed data on their trading of goods since 1988. Before the introduction of the CN, ITGS were based on a product classification called NIMEXE.  The CN is based on the Harmonised Commodity Description and Coding System (managed by the World Customs Organisation (WCO). The Harmonised System (HS) is an international classification at two, four and six-digit level which classifies goods according to their nature. It was introduced in 1988 and, since then, was revised six times: in 1996, 2002, 2007, 2012, 2017 and 2022. The CN corresponds to the HS plus a further breakdown at eight-digit level defined to meet EU needs. The CN is revised annually and, as a Council Regulation, is binding on the Member States.",
      "@language": "en"
    }
  ],
  "http://rdf-vocabulary.ddialliance.org/xkos#follows": [
    {"@id": "http://data.europa.eu/xsp/cn2023/cn2023"}
  ],
  "http://www.w3.org/2004/02/skos/core#notation": [
    {
      "@value": "CN 2024",
      "@type": "http://www.w3.org/1999/02/22-rdf-syntax-ns#PlainLiteral"
    }
  ]
}
```

Here is an example of a valid `Concept` in JSON-LD:

```json
{
  "@id": "http://data.europa.eu/xsp/cn2024/010011000090",
  "@type": ["http://www.w3.org/2004/02/skos/core#Concept"],
  "http://www.w3.org/2004/02/skos/core#inScheme": [
    {"@id": "http://data.europa.eu/xsp/cn2024/cn2024"}
  ],
  "http://purl.org/ontology/bibo/status": [
    {"@id": "http://purl.org/ontology/bibo/status/accepted"}
  ],
  "http://www.w3.org/2004/02/skos/core#prefLabel": [
    {
      "@value": "SECTION I - LIVE ANIMALS; ANIMAL PRODUCTS",
      "@language": "en"
    },
    {
      "@value": "SEC\u00c7\u00c3O I - ANIMAIS VIVOS E PRODUTOS DO REINO ANIMAL",
      "@language": "pt"
    }
  ],
  "http://www.w3.org/2004/02/skos/core#notation": [
    {
      "@value": "I",
      "@type": "http://www.w3.org/1999/02/22-rdf-syntax-ns#PlainLiteral"
    }
  ],
  "http://www.w3.org/2004/02/skos/core#definition": [
    {
      "@language": "en",
      "@value": "LIVE ANIMALS; ANIMAL PRODUCTS"
    }
  ],
  "http://www.w3.org/2004/02/skos/core#topConceptOf": [
    {"@id": "http://data.europa.eu/xsp/cn2024/cn2024"}
  ]
}
```

### Correspondence

The [XKOS](https://rdf-vocabulary.ddialliance.org/xkos.html) ontology provides the [Correspondence](https://rdf-vocabulary.ddialliance.org/xkos.html#correspondences) class definition, which we use follow the [XKOS best practice guide](http://linked-statistics.github.io/xkos/xkos-best-practices.html). A `Correspondence` instance is very similar to a `ConceptScheme` - it provides metadata for a collection of child nodes.

In addition to our [generic addition restrictions](#additional-requirements), `Correspondence` must have:

* Exactly one `http://purl.org/dc/terms/issued` value.

Here is an example of a valid `Correspondence` in JSON-LD:

```json
{
  "@id": "http://data.europa.eu/xsp/cn2024/CN2024_CN2023",
  "@type": ["http://rdf-vocabulary.ddialliance.org/xkos#Correspondence"],
  "http://rdf-vocabulary.ddialliance.org/xkos#compares": [
      {"@id": "http://data.europa.eu/xsp/cn2024"}
      {"@id": "http://data.europa.eu/xsp/cn2023"}
  ],
  "http://www.w3.org/2004/02/skos/core#definition": [
    {
      "@value": "This table is indicative and has no legal value.",
      "@language": "en"
    }
  ],
  "http://www.w3.org/2004/02/skos/core#prefLabel": [
    {
      "@value": "Transposition between CN 2024 and CN 2023",
      "@language": "en"
    }
  ],
  "http://purl.org/dc/terms/issued": [
    {
      "@type": "http://www.w3.org/2001/XMLSchema#dateTime",
      "@value": "2024-07-02T08:41:55"
    }
  ]
}
```

### 1-to-N Concept Association

The class [ConceptAssociation](https://rdf-vocabulary.ddialliance.org/xkos.html#correspondences) links concepts from different concept schemes. While the XKOS standard does allow M-to-N (i.e. multiple concepts in one concept scheme mapping to multiple concepts in another concept scheme), we require that each concept in the source concept scheme be mapped separately to the appropriate target concepts.

One frustration of the current XKOS standard is that no additional properties for describing the kinds or qualities of `ConceptAssociation` are defined: "In this version, XKOS does not define any properties or sub-classes for `xkos:Correspondence` and `xkos:ConceptAssociation` in order to model these different types of correspondences. This may be added in a future version.". This means that we don't have proscribed ways to indicate the quality of the correspondence like we do in mapping relations within SKOS, such as close, related, or exact matches. To add this additional information, you should therefore specify these properties directly on the `Concept` instances themselves. Note that this means that these mapping properties will not be linked directly to the `Correspondence` instance. It is our hope that client libraries will provide a more convenient way of working with correspondence association properties.

We don't impose any restrictions outside of the XKOS specification on `ConceptAssociation`, aside from every string literal specifying their `@language`.

Here is an example of a valid 1-to-N `ConceptAssociation` in JSON-LD; in this case it is 1-to-1:

```json
{
  "@id": "http://data.europa.eu/xsp/cn2024/CN2024_CN2023_010239100080",
  "@type": ["http://rdf-vocabulary.ddialliance.org/xkos#ConceptAssociation"],
  "http://rdf-vocabulary.ddialliance.org/xkos#sourceConcept": [
      {"@id": "http://data.europa.eu/xsp/cn2024/010239100080"}
  ],
  "http://rdf-vocabulary.ddialliance.org/xkos#sourceConcept": [
      {"@id": "http://data.europa.eu/xsp/cn2023/010239100080"}
  ]
}
```

### Conditional Concept Association

In certain cases a concept in scheme `A` can correspond to a concept in scheme `B`, but only when it is paired with another concept from scheme `C`. For example, `A:electricity` is equivalent to `B:renewable_electricity` when it is produced by `C:wind_turbine`.

We will (slightly) abuse the `Correspondence` class to meet this modelling need by allowing `Correspondence` to link *three* concept schemes. In this case, each concept association should have *two* source `Concepts` and *one* target `Concept`.

Here is an example of this pattern in JSON-LD:

```json
{
  "@id": "http://example.com/conditional",
  "@type": ["http://rdf-vocabulary.ddialliance.org/xkos#ConceptAssociation"],
  "http://rdf-vocabulary.ddialliance.org/xkos#sourceConcept": [
      {"@id": "http://example.com/A/electricity"},
      {"@id": "http://example.com/C/wind_turbine"}
  ],
  "http://rdf-vocabulary.ddialliance.org/xkos#targetConcept": [
      {"@id": "http://example.com/B/renewable_electricity"}
  ]
}
```

An alternative to this approach would be to create new graph nodes (possibly instances of `Concept` in a custom `ConceptScheme`) which represented the combination of two `Concepts`. This could be done using, for example, `http://www.w3.org/2002/07/owl#intersectionOf`. We didn't choose this approach because it adds complexity creating and maintaining these composite nodes, and because none of the OWL predicates we found were a good fit for conditional concept association.

## Contributing

Contributions are very welcome.
To learn more, see the [Contributor Guide][Contributor Guide].

## License

Distributed under the terms of the [MIT license][License],
_py_semantic_taxonomy_ is free and open source software.

## Issues

If you encounter any problems,
please [file an issue][Issue Tracker] along with a detailed description.


<!-- github-only -->

[command-line reference]: https://py-semantic-taxonomy.readthedocs.io/en/latest/usage.html
[License]: https://github.com/cauldron/py-semantic-taxonomy/blob/main/LICENSE
[Contributor Guide]: https://github.com/cauldron/py-semantic-taxonomy/blob/main/CONTRIBUTING.md
[Issue Tracker]: https://github.com/cauldron/py-semantic-taxonomy/issues


## Building the Documentation

You can build the documentation locally by installing the documentation Conda environment:

```bash
conda env create -f docs/environment.yml
```

activating the environment

```bash
conda activate sphinx_py-semantic-taxonomy
```

and [running the build command](https://www.sphinx-doc.org/en/master/man/sphinx-build.html#sphinx-build):

```bash
sphinx-build docs _build/html --builder=html --jobs=auto --write-all; open _build/html/index.html
```
