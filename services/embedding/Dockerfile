FROM python:3.13-slim AS model
WORKDIR /build
RUN pip install --no-cache-dir huggingface-hub==1.25.1
COPY download_model.py .
RUN python download_model.py --out /opt/model

FROM python:3.13-slim AS runtime
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HF_HUB_OFFLINE=1

WORKDIR /srv
COPY pyproject.toml .
RUN pip install --no-cache-dir \
        "fastapi==0.140.7" \
        "uvicorn[standard]==0.51.0" \
        "pydantic==2.13.4" \
        "pydantic-settings==2.14.2" \
        "onnxruntime==1.28.0" \
        "tokenizers==0.23.1" \
        "numpy==2.5.1"

COPY --from=model /opt/model /opt/model
COPY app ./app

RUN useradd --create-home --uid 10001 service && chown -R service /srv
USER service

EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
