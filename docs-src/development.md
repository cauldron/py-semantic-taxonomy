# Development and testing

## Asynchronous code

All three layers of PyST are asynchronous; most functions and methods user `async` and must be called with `await`. Developing in this style can be challenging at first; see the tests for patterns which you can follow if you need help.

## Prerequisites

Use [uv](https://docs.astral.sh/uv/) for development. Run `uv sync --extra dev` to create a virtual environment and install all dependencies.

## Containers for Postgres and Typesense

Development and testing require Docker via [testcontainers](https://testcontainers.com/). On MacOS you will need a recent version of Docker Desktop - the alternatives don't seem to work.

The `scripts` directory has two scripts for running Postgres and Typesense containers:

* [start_typesense_container.py](https://github.com/cauldron/py-semantic-taxonomy/blob/main/scripts/start_typesense_container.py)
* [start-postgres-container.py](https://github.com/cauldron/py-semantic-taxonomy/blob/main/scripts/start_postgres_container.py)

If you run those scripts, you will get instructions on how to set the environment variable values needed to run the development server:

```console
python src/py_semantic_taxonomy/app.py
```

Alternatively, a `compose.yaml` file in the repo root starts both containers on fixed ports with persistent volumes. Copy `.env.example` to `.env`, which both Compose and the app read automatically:

```console
cp .env.example .env
docker compose up -d
```

`.env` is the single source of truth: the app reads it and Compose interpolates the port mapping from it, so changing `PyST_db_port` moves both. Use `docker compose down` to stop the containers.

To run the app itself in a container too — no host Python needed — use the `demo` profile, which builds from the `Dockerfile` and serves on port 8000:

```console
docker compose --profile demo up --build
```

Values from `.env` flow into the demo containers too, falling back to built-in defaults if it is absent. Tear it down with `docker compose --profile demo down` (the `--profile` flag is required on the way down as well).

## Testing

When adding new functionality, it's important to write unit tests for each layer effected, as well as integration tests. Unit tests should *mock* the other layers - see the [conftest.py](https://github.com/cauldron/py-semantic-taxonomy/blob/main/tests/conftest.py) file for test mocks and fixture data.

![Integration and unit tests](img/testing.png)

## Linting

```console
isort --profile=black tests/ && black tests/ && \
isort --profile=black src/ && black src/
```
