FROM python:3.12
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /code

RUN uv venv .venv
# Use the virtual environment automatically
ENV VIRTUAL_ENV=.venv
# Place entry points in the environment at the front of the path
ENV PATH="/code/.venv/bin:$PATH"

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project

COPY . .

# Sync the project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

RUN uv tool install celery
RUN uv tool install pytest

RUN uv pip install -e .[test]
RUN uv run python manage.py collectstatic --force

# CMD ["uv", "run", "python", "manage.py", "runserver", "0.0.0.0:8000"]
