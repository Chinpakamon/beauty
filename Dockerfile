FROM node:22-slim AS frontend-builder

WORKDIR /frontend

COPY frontend/package.json /frontend/package.json
COPY frontend/scripts /frontend/scripts
COPY frontend/src /frontend/src

RUN npm run build

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry

COPY pyproject.toml poetry.lock* /app/

RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

COPY . /app
COPY --from=frontend-builder /frontend/dist /app/frontend/dist

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
