# `py-semantic-taxonomy` Changelog

## [0.5.0] - Unreleased

* Add GitLab-backed admin UI for creating, editing, and deleting concept schemes and concepts
* Add contributor workflows with login, claim creation, claim detail pages, and admin claim review
* Add claim persistence tables and repository helpers
* Add CSV import support for concept data
* Add exports for concept schemes and correspondences
* Add SKOS mapping type support for XKOS associations in admin, contributor, and public UI flows
* Refresh the web UI with concept tree/detail panels, correspondence pages, improved headers, and Tailwind-based styling
* Improve concept scheme and concept views with editable descriptions, association identifiers, mapping details, and delete controls
* Improve search behavior and search result display, including IRI search support
* Add GitLab group/membership configuration and example environment configuration
* Add contributor workflow documentation and update the demo notebook
* Fix packaging for `url_utils` in PyPI distributions
* Fix web UI regressions tracked in issues #66, #69, #71, #72, #77, #78, #79, and #81
* Add integration and unit coverage for web UI, admin OAuth, and contributor claim helpers

## [0.4.4] - 2025-06-07

* Fix packaging to include SQL queries

## [0.4.3] - 2025-06-07

* Fix packaging to include web media

## [0.4.2] - 2025-06-05

* [Fix #63: `typesense` implementation assumes only one running instance of PyST](https://github.com/cauldron/py-semantic-taxonomy/issues/63)

## [0.4.1] - 2025-05-07

* [Fix #60: `Association` serialization is excluding `extra` attributes](https://github.com/cauldron/py-semantic-taxonomy/issues/60)
* [Fix #61: `ConceptScheme` should have copyable IRI in sidebar](https://github.com/cauldron/py-semantic-taxonomy/issues/61)
* [Fix #62: Missing dark mode elements: History notes](https://github.com/cauldron/py-semantic-taxonomy/issues/62)

## [0.4.0] - 2025-05-06

* [#55: Indexed queries within JSONB elements](https://github.com/cauldron/py-semantic-taxonomy/pull/55)
* [#56: Make `pyst` more RESTful](https://github.com/cauldron/py-semantic-taxonomy/pull/56)
* [#57: Fix some missing dynamic background colors](https://github.com/cauldron/py-semantic-taxonomy/pull/57)
* [Fix #58: API Path for a `ConceptScheme` is missing slash](https://github.com/cauldron/py-semantic-taxonomy/issues/58)
* [Fix #59: Add status URL endpoint](https://github.com/cauldron/py-semantic-taxonomy/issues/59)

## [0.3.0] - 2025-04-30

* [#54: Language redo to persist language choice and make globally available](https://github.com/cauldron/py-semantic-taxonomy/pull/54)
* [#53: Hierarchy queries and info display](https://github.com/cauldron/py-semantic-taxonomy/pull/53)

## [0.2.0] - 2025-04-10

First complete release with web frontend

## [0.1.0] - 2025-03-20

Initial release
