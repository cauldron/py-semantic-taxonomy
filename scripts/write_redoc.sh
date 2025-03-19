#!/bin/bash
python scripts/export_openapi_spec.py
npx --yes @redocly/cli build-docs docs/api/openapi.yaml --output docs/api/index.html # --config docs/redocly.yaml
