FROM docker.io/library/python:3.10-alpine3.22
RUN python3 -m venv .poetry-venv && .poetry-venv/bin/pip install poetry
RUN .poetry-venv/bin/poetry self add poetry-plugin-export
COPY pyproject.toml ./
RUN .poetry-venv/bin/poetry add poetry
RUN .poetry-venv/bin/poetry export -f requirements.txt --output poetry-requirements.txt
