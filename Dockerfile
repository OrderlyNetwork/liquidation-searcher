FROM python:3.10-bookworm as builder

RUN pip install poetry

# https://medium.com/@albertazzir/blazing-fast-python-docker-builds-with-poetry-a78a66f5aed0
# https://python-poetry.org/docs/configuration/#using-environment-variables
ENV POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# or docker run -e
ENV ORDERLY_KEY=7883GEervpYgu9d7SuZK128PswspqZU6rpYhZirrCbTV \
    ORDERLY_SECRET=9KoCsYwmTwCnVEsG9nhVRokzLSaPYQR5kWbxc8gZ3MgZ

WORKDIR /app
# COPY pyproject.toml poetry.lock ./
# RUN touch README.md
COPY . .

# RUN poetry config installer.modern-installation false
RUN poetry config installer.max-workers 10
RUN poetry install -n --without dev --no-ansi && rm -rf "$POETRY_CACHE_DIR"

FROM python:3.10-slim-bookworm as runtime

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app
COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}
COPY . .
COPY ./conf/staging.yml ./config.yml
EXPOSE 8088
CMD ["python", "src/liquidation_searcher/main.py", "-c", "config.yml"]
