#!/bin/bash
echo "Building main docs"
mkdocs build
echo "Building API docs"
mkdir docs/api
python scripts/export_openapi_spec.py
npx --yes @redocly/cli build-docs docs/api/openapi.yaml --output docs/api/index.html # --config docs/redocly.yaml
