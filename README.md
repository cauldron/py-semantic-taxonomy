# py-semantic-taxonomy

[![PyPI](https://img.shields.io/pypi/v/py-semantic-taxonomy.svg)][pypi status]
[![Status](https://img.shields.io/pypi/status/py-semantic-taxonomy.svg)][pypi status]
[![Python Version](https://img.shields.io/pypi/pyversions/py-semantic-taxonomy)][pypi status]
[![License](https://img.shields.io/pypi/l/py-semantic-taxonomy)][license]
[![Tests](https://github.com/cauldron/py-semantic-taxonomy/actions/workflows/python-test.yml/badge.svg)][tests]

[pypi status]: https://pypi.org/project/py-semantic-taxonomy/
[tests]: https://github.com/cauldron/py-semantic-taxonomy/actions?workflow=Tests

## A Knowledge Organization System for Sustainability Assessment

PyST is opinionated server software for creating, maintaining, and publishing [SKOS](https://www.w3.org/TR/skos-reference/)/[XKOS](https://rdf-vocabulary.ddialliance.org/xkos.html) taxonomies.

* [General documentation](https://docs.pyst.dev)
* [API documentation](https://docs.pytest.dev/api/)
* [Example notebook]()

### Background and Design Goals

This project has been based on our experiences using [SKOSMOS](https://skosmos.org/) for the [Sentier.dev taxonomic vocabulary](https://vocab.sentier.dev/en/). The RDF graph data structure and the SKOSMOS software itself work well for a certain set of use cases, but for our specific needs and user community, the choice of PHP, [Jena](https://jena.apache.org/), [SPARQL](https://en.wikipedia.org/wiki/SPARQL), and built-in search indexer all posed barriers to productive software and vocabulary maintenance.




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
      {"@id": "http://data.europa.eu/xsp/cn2023/010239100080"}
  ],
  "http://rdf-vocabulary.ddialliance.org/xkos#targetConcept": [
      {"@id": "http://data.europa.eu/xsp/cn2024/010239100080"}
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

Contributions are very welcome. Please be nice.

## License

Distributed under the terms of the [MIT license][License],
_py_semantic_taxonomy_ is free and open source software.

## Issues

If you encounter any problems,
please [file an issue][Issue Tracker] along with a detailed description.


<!-- github-only -->

[License]: https://github.com/cauldron/py-semantic-taxonomy/blob/main/LICENSE
[Issue Tracker]: https://github.com/cauldron/py-semantic-taxonomy/issues
