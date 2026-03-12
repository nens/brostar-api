FROM python:3.12
WORKDIR /code

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY pyproject.toml uv.lock ./

# Install to /opt/venv instead of /code/.venv
ENV UV_PROJECT_ENVIRONMENT=/opt/venv
RUN uv sync

# Put venv in PATH
ENV PATH="/opt/venv/bin:$PATH"

COPY . .

RUN uv run python manage.py collectstatic --force
