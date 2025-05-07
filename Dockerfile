FROM python:3.12
WORKDIR /code

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY pyproject.toml uv.lock ./

RUN uv sync
# Place entry points in the environment at the front of the path
ENV PATH="/code/.venv/bin:$PATH"

COPY . .

RUN uv run python manage.py collectstatic --force
