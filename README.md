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

## Installation

You can install _py_semantic_taxonomy_ via [pip] from [PyPI]:

```console
$ pip install py_semantic_taxonomy
```

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