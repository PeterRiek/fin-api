FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# Install dependencies first so this layer is cached across source changes.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src ./src
RUN uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH"
RUN mkdir -p /app/data

EXPOSE 8000

CMD ["uvicorn", "app.api:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8000"]
