# syntax=docker/dockerfile:1

FROM python:3.13-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"
RUN python -m venv /opt/venv
WORKDIR /app

FROM base AS poetry
# Poetry lives in the system Python; it installs the app's packages into /opt/venv.
ENV POETRY_NO_INTERACTION=1 POETRY_VIRTUALENVS_CREATE=false
RUN /usr/local/bin/python -m pip install --no-cache-dir --root-user-action=ignore "poetry==2.5.1"
COPY pyproject.toml poetry.lock ./

# Local development: all dependency groups, source mounted from the host, auto-reload.
FROM poetry AS dev
RUN poetry install --no-root
COPY . .
EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"]

FROM poetry AS prod-deps
RUN poetry install --no-root --only main

# Production: runtime packages only, non-root user, migrations on start.
FROM base AS prod
COPY --from=prod-deps /opt/venv /opt/venv
COPY alembic.ini ./
COPY migrations ./migrations
COPY app ./app
RUN useradd --create-home --uid 10001 app
USER app
EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips='*'"]
