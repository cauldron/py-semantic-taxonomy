# PyST (py-semantic-taxonomy)

PyST is opinionated server software for creating, maintaining, and publishing [SKOS](https://www.w3.org/TR/skos-reference/)/[XKOS](https://rdf-vocabulary.ddialliance.org/xkos.html) taxonomies.

* [API docs](https://docs.pyst.dev/api/), [OpenAPI 3.1 JSON](https://docs.pyst.dev/api/openapi.json), [OpenAPI 3.1 YAML](https://docs.pyst.dev/api/openapi.yaml)
* [GitHub repo](https://github.com/cauldron/py-semantic-taxonomy/)
* [Client library](https://github.com/cauldron/pyst-client/)
* [Client library usage guide](https://github.com/cauldron/pyst-client/blob/main/pyst_client/example/Simple%20client%20library%20guide.ipynb)
* [Example notebook](https://github.com/cauldron/py-semantic-taxonomy/blob/main/examples/PyST%20basic%20demo.ipynb)

PyST was built and is maintained by [Cauldron Solutions](https://www.cauldron.ch/).

## Quickstart

1\. Install required software

* Install and configure Postgres
* Install and configure [Typesense](https://typesense.org/)
* `pip install py-semantic-taxonomy`

If you just want to try our the software, and have Docker installed on your machine, you can run Postgres and Typesense in containers using the scripts in the `scripts` directory, i.e.:

* `python scripts/start_postgres_container.py`
* `python scripts/start_typesense_container.py`

These scripts will give you the values of the environment variables needed for step 2. Note that you will still need to make up your own `PyST_auth_token` setting and make sure it is set correctly, i.e.:

```console
export PyST_auth_token="supersecret"
```

2\. Configure required software

The following parameters must be either specified as environment variables, or given in the file `pyst-config.env`.

!!! Note

    We use `pydantic-settings` for settings management, please note [their instructions on dependencies, precedence, and env file location](https://docs.pydantic.dev/1.10/usage/settings/#dotenv-env-support).

* `PyST_db_user` : Postgres user. Must have table and index creation rights.
* `PyST_db_pass` : Postgres password for given user
* `PyST_db_host` : Postgres host URL
* `PyST_db_port` : Postgres port
* `PyST_db_name` : Postgres database name; default is "PyST"
* `PyST_auth_token` : Authorization header token to allow users to change data
* `PyST_typesense_url` : Typesense host URL
* `PyST_typesense_api_key` : Typesense API key. Must have collection creation rights.
* `PyST_typesense_embedding_model` : [Typesense embedding model](https://typesense.org/docs/28.0/api/vector-search.html#using-built-in-models) for semantic search. Default is "ts/all-MiniLM-L12-v2"
* `PyST_languages` : List of language codes used in the search engine and web UI. Should be a JSON _string_, e.g. `'["en", "de"]'`. Default is `'["en", "de", "es", "fr", "pt", "it", "da"]'`

3\. Run the server

PyST is a [FastAPI app](https://fastapi.tiangolo.com/); it can be run [as any python ASGI app](https://fastapi.tiangolo.com/deployment/manually/), e.g. with `uvicorn`:

```python
import uvicorn

uvicorn.run(
    "py_semantic_taxonomy.app:create_app",
    host="0.0.0.0",
    port=8000,
    log_level="warning",
)
```

If you are using the default ASGI app runner and configuration options, you can also do:

```console
python <pyst-source-directory>/src/py_semantic_taxonomy/app.py
```

4\. Add data

See [common workflows](common-workflows.md) for a guide on adding example data.

## Why New Software?

There are a number of great projects for browsing SKOS taxonomies already, including:

* [showvoc](https://showvoc.uniroma2.it/)
* [skosmos](https://skosmos.org/)

[JSKOS](https://gbv.github.io/jskos/) translate SKOS to JSON, and provides validation and publication capabilities. It's an amazing project with a long history, but we started with a strict requirement that data transfer would be valid JSON-LD follow SKOS and other RDF specifications.

Our user community is comfortable with Python and relational databases, and our experiments to customize skosmos and write complicated queries in SPARQL proved to be serious barriers to barriers to productive software and vocabulary maintenance. We also wanted more flexibility on the choice of search engine.

In `py_semantic_taxonomy` we have the following goals:

* Native and rich support for [XKOS](https://rdf-vocabulary.ddialliance.org/xkos.html) [`Correspondence` and `ConceptAssociation` classes](https://rdf-vocabulary.ddialliance.org/xkos.html#correspondences)
* A predictable, consistent, and validated set of properties and property uses for SKOS and XKOS terms
* Web interface to allow for browsing
* API to allow for the complete set of [CRUD](https://en.wikipedia.org/wiki/Create,_read,_update_and_delete) operations
* API provides common graph queries without needing to learn SPARQL
* IRIs should resolve to HTML or RDF serialized resources, depending on requested media type
* Web interface supports high quality multilingual search without configuration pain

This means that we want the following technical capabilities which are missing or more difficult than they need to be in SKOSMOS:

* A set of validation classes and functions for input data to ensure consistency in how objects are described.
* Better query performance by optimizing database structure and indices for a small set of needed edges
* Easy customization of the UI
* Pluggable search index

To put it another way, SKOSMOS is amazing software which can handle knowledge organization systems which are based on SKOS and already exist in a graph database, but which include a lot of inconsistency and variability - PyST has a reduced feature set, but allows for easier data editing, and is much pickier about incoming data.
