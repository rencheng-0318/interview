FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/srv

WORKDIR /srv

RUN pip install --no-cache-dir \
        "fastapi==0.140.7" \
        "uvicorn[standard]==0.51.0" \
        "pydantic==2.13.4" \
        "pydantic-settings==2.14.2" \
        "asyncpg==0.31.0" \
        "pgvector==0.5.0" \
        "httpx==0.28.1" \
        "numpy==2.5.1" \
        "pytest==9.1.1" \
        "pytest-asyncio==1.4.0" \
        "ruff==0.16.0"

COPY pyproject.toml .
COPY app ./app
COPY tests ./tests

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
