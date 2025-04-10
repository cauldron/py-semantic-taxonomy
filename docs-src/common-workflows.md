# Common Workflows

## Importing the Combined Nomenclature codes

This functionality is built into `pyst_client`. `py-semantic-taxonomy` must be deployed and available:

```python
from pyst_client.cn import CombinedNomenclatureLoader
CombinedNomenclatureLoader(
    year=<year>,
    api_key=<pyst-api-key>,
    host=<host>,
    sample=True or False
).write()
```

Where:

* `year` is a integer, like `2024`. If only installing the sample data, this should be 2024 or 2025 (you can also run both one after the other).
* `api_key` is the write-enabled API key (`PyST_auth_token`) for `py-semantic-taxonomy`.
* `host` is the URL that `py-semantic-taxonomy` is running at, e.g. "http://localhost:8000" if running locally
* `sample` is a boolean flag on whether only a sample of the available data should be imported. The full import takes more than an hour.

## Creating a new taxonomy

PyST stores concept schemes, concepts, and relationships between concepts all in different places, so the creation of these objects needs to happen in a defined order:

* First, decide on the URL pattern you will use for concept schemes and concepts. A reasonable pattern is `https://<base_url>/<concept-scheme-notation>/<concept-notation>`. Many of the EU semantic taxonomies use this patter, e.g. `http://data.europa.eu/xsp/cn2025/970300000080`. When following this pattern, the concept scheme notation should be different from version to version or year to year.
* Second, create the concept scheme.
* Third, create the concepts. Although it is possible to provide relationship information among concepts inside the individual concept documents, this is recommended against, as concept creation requests are normally submitted in parallel, and we can't run graph integrity checks against unknown graph nodes.
* Finally, define relationships among concepts. It's best if each request to `relationships` creates one relationship, and these can be chunked to run in parallel (asyncio doesn't seem to like it when thousands of tasks are submitted at once - its better to do 20 or 50 at a time).

## Updating a `Concept` or a `Concept` relationship

Best practice is to always record the who, what, why, and when of changes, which can be done by adding [change, editorial, or history notes](https://docs.pyst.dev/data-model/#tracking-changes) to the `Concept`.

Depending on your institutions review practices, you could also require that change suggestions include changing the `Concept.status` to `draft`, and that changes are only accepted after review, when the status could be changed to `accepted`.

## Creating a new Correspondence

Creating new `Correspondence` and `ConceptAssociation` objects should also follow a set order:

* First, decide on the URL pattern you will use, especially for `ConceptAssociations`, which can be N-to-1. It would be nice if the URLs for `Correspondences` were human readable, but `ConceptAssociations` could use computer-generated ids.
* Second, create the `Correspondence` object. This doesn't have any references to `ConceptAssociation` objects.
* Third, create the `ConceptAssociation` objects. They don't have any information on membership in a `Correspondence`.
* Finally, link the `ConceptAssociation` objects to the `Correspondence` using the `made_of` endpoint. This can be done in one request as this endpoint takes a list of inputs.
