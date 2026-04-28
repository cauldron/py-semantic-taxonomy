# Contributor And Admin Workflows

## Goal

PyST currently gives administrators a more guided editing experience than contributors. This document proposes a clearer split of responsibilities and a more structured contributor workflow, especially for bulk changes based on CSV files.

The main design principle is:

* Contributors propose changes
* Admins review and publish changes

This keeps publication rights with administrators while still allowing contributors to work efficiently.

## Proposed Role Split

### Contributors

Contributors should be able to:

* Propose new concepts
* Propose edits to existing concepts
* Propose new relationships
* Propose concept deprecations
* Propose correspondence changes
* Upload CSV files for bulk proposals
* Track the status of their own submissions
* Receive review comments from administrators

Contributors should normally **not** write directly to published taxonomy data.

### Administrators

Administrators should be able to:

* Do everything contributors can do
* Edit taxonomy data directly in the UI
* Review contributor submissions
* Approve or reject submissions
* Run bulk imports that publish data
* Manage concept schemes and correspondence structures

## UI Direction

The contributor interface should focus on guided forms and reviewable submissions, not raw JSON entry for common tasks.

Recommended contributor flows:

* `Add concept`: guided form
* `Edit concept`: guided form preloaded with the current values
* `Add relationship`: guided form with concept lookup
* `Deprecate concept`: guided form with reason and replacement concept
* `Bulk upload`: CSV upload with validation and preview

The existing raw JSON claim payload can remain available as an advanced option, but it should not be the primary workflow for normal users.

## CSV Support

CSV uploads should first be implemented as **claims for review**, not direct writes to the taxonomy.

Recommended workflow:

1. Contributor uploads a CSV file
2. PyST validates and parses the file
3. PyST shows a preview and any validation errors
4. PyST stores the parsed result as a contributor claim
5. An administrator reviews the claim
6. If approved, PyST publishes the changes

This approach is safer than allowing contributors to write taxonomy data directly from CSV.

## BONSAI Compatibility

For CSV design, PyST should follow the BONSAI classifications conventions used in:

* `tree_` tables
* `conc_` tables

Reference project:

* <https://gitlab.com/bonsamurais/bonsai/util/classifications>

Reference documentation:

* <https://lookup-bonsamurais-bonsai-clean-330eb13cc839181a6ad54b293ca2729.gitlab.io/>
* <https://pypi.org/project/bonsai-classifications/>

PyST should preserve compatibility with the minimal BONSAI column structure, and allow PyST-specific optional columns later.

## `tree_` CSV Proposal

`tree_` files describe hierarchical classifications and are the best match for concept scheme and concept imports.

### Minimal BONSAI-compatible columns

* `code`
* `parent_code`
* `name`
* `level`

### Proposed PyST interpretation

* Each `tree_` file represents one concept scheme, unless future work explicitly adds subtree imports
* Each row becomes one `Concept`
* `parent_code` becomes the basis for `broader` and `narrower` relationships
* `name` becomes the default `prefLabel`
* `level` is validated against the hierarchy and used as an integrity check

### Open design questions

* How the concept scheme is identified: filename, upload form field, or explicit column
* How `code` becomes a concept IRI
* Which language is assumed for `name`
* Whether a future extended format should support multiple label columns such as `prefLabel_en` and `prefLabel_da`

### Recommended optional PyST columns

These columns should be optional extensions, not BONSAI requirements:

* `iri`
* `notation`
* `definition_en`
* `status`
* `valid_from`
* `valid_to`
* `prefLabel_<lang>`

## `conc_` CSV Proposal

`conc_` files describe correspondences between classifications and are the best match for SKOS mapping relations and PyST correspondence workflows.

### Minimal BONSAI-compatible columns

* `<category>_from`
* `<category>_to`
* `classification_from`
* `classification_to`
* `comment`
* `skos_uri`

### Proposed PyST interpretation

* Each row expresses one mapping proposal between two concepts
* `skos_uri` maps directly to a SKOS mapping predicate such as `exactMatch`, `broadMatch`, `narrowMatch`, or `relatedMatch`
* The upload should create or update a reviewable mapping claim

### Open design questions

* Whether `conc_` uploads should create plain SKOS mappings only
* Whether `conc_` uploads should also create XKOS `Correspondence` and `ConceptAssociation` structures
* How ambiguity comments should be preserved in PyST review and publication flows

### Recommended optional PyST columns

* `source_iri`
* `target_iri`
* `correspondence_iri`
* `mapping_status`
* `review_note`

## First Implementation Scope

To keep the first milestone manageable, PyST should implement:

1. Guided contributor forms for common single-item changes
2. `tree_` CSV upload as a contributor claim
3. `conc_` CSV upload as a contributor claim
4. Validation preview for uploads
5. Admin approval or rejection of parsed submissions

The raw JSON claim form can stay in place during this transition as an advanced fallback.

## Validation Expectations

For `tree_` uploads, PyST should validate:

* Required columns are present
* `code` values are unique
* Parent codes exist, except for top-level rows
* `level` values are consistent with the tree structure

For `conc_` uploads, PyST should validate:

* Required columns are present
* `skos_uri` is one of the supported mapping predicates
* Source and target codes can be resolved
* The referenced classifications or schemes are known

## Summary

The recommended product direction is:

* contributors submit structured proposals
* administrators review and publish
* bulk uploads follow BONSAI `tree_` and `conc_` conventions
* PyST keeps BONSAI compatibility at the minimal schema level, while allowing optional PyST-specific extensions
