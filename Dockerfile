# Single-stage uv build for the demo `app` service in compose.yaml (profile: demo).
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim
WORKDIR /app
COPY . .
RUN uv sync --frozen --no-dev
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "--factory", "py_semantic_taxonomy.app:create_app", "--host", "0.0.0.0", "--port", "8000"]
