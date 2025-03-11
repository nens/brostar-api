FROM python:3.12
WORKDIR /code

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY pyproject.toml uv.lock ./

COPY . .

RUN uv sync

ENV PATH="/code/.venv/bin:$PATH"

RUN python manage.py collectstatic --force
