# Embedding service (provided)

Local sentence-embedding service. **Not part of the assignment** — you should not need to
modify it, but its behaviour constrains your chunking decisions, so read this page.

Wraps an ONNX export of `sentence-transformers/all-MiniLM-L6-v2`. The weights are baked
into the image at build time, so no API key, credit, or network access is required at run
time or during tests.

## Interface

```http
POST /v1/embeddings
Content-Type: application/json

{ "texts": ["first text", "second text"] }
```

```json
{
  "model": "interview-embedding-v1",
  "dimensions": 384,
  "embeddings": [[0.012, -0.044, "... 384 floats total"]]
}
```

`GET /health` reports the model name, dimensionality, and the limits below.

## Behaviour

| Property | Value |
|---|---|
| Dimensions | 384 |
| Vectors | L2-normalised |
| Pooling | Attention-weighted mean over tokens |
| Maximum sequence length | 256 tokens; additional tokens are truncated |
| Maximum texts per request | 64 |
| Maximum characters per text | 8,000 |
| Determinism | The same input produces the same output |

These limits are enforced by the service contract. How they influence the searchable
representation is part of the exercise.

## Error responses

| Status | `error` | Cause |
|---|---|---|
| 422 | `blank_text` | A text was empty or whitespace only. |
| 422 | `text_too_long` | A text exceeded the character limit. |
| 422 | `batch_too_large` | More than 64 texts in one request. |
| 503 | `injected_failure` | Deliberate failure injection, see below. |

All errors use `{"error": "...", "detail": "..."}`.

## Simulating an outage

To exercise the "embedding service unavailable" state in the UI without stopping the
container:

```bash
EMBEDDING_FAILURE_RATE=1.0 docker compose up -d embedding
```

Set it back to `0.0` afterwards.

## Configuration

All variables take the `EMBEDDING_` prefix: `MODEL_DIR`, `MAX_SEQUENCE_LENGTH`,
`MAX_BATCH_SIZE`, `MAX_CHARACTERS_PER_TEXT`, `INFERENCE_BATCH_SIZE`, `FAILURE_RATE`,
`LOG_LEVEL`.

## Model provenance

Downloaded at build time by `download_model.py` from `Xenova/all-MiniLM-L6-v2`, pinned by
revision. Only the fp32 `onnx/model.onnx` and tokenizer files are pulled; the quantised
variants are ignored. Changing the pin changes every vector, which invalidates an existing
index — treat it as a reindex.
