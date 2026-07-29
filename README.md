# Clinical Record Semantic Search — take-home exercise

Make a corpus of synthetic clinical records semantically searchable, end to end.

A user types a natural-language description:

> recurring headaches preceded by flashing lights, nausea, and sensitivity to light

and gets a ranked list of patients **in their own practice** whose existing notes and
reports are relevant, each with the specific document and passage that explains the match.

This is retrieval. It must not generate a diagnosis, infer a condition that is not already
in the records, or present a similarity score as clinical confidence.

**Read [`docs/TAKE_HOME_DESIGN.md`](docs/TAKE_HOME_DESIGN.md) first.** It is the
specification; this file is the operating manual.

---

## Quick start

Requirements: Docker with Compose v2. Nothing else — Python, Node, pnpm, and the embedding
model all live inside the images.

```bash
cp .env.example .env
make setup     # build images, start services, apply migrations
make seed      # load the synthetic dataset
make dev       # web on http://localhost:3000, API on http://localhost:8000
```

In another shell:

```bash
make test      # backend and frontend suites
make smoke     # confirm database, seed data, and a real embedding call
```

`make index` is wired up but exits with a message: building the index is your task.

<details>
<summary>Without <code>make</code> (Windows PowerShell, or a bare shell)</summary>

Every target is one or two Compose commands.

```powershell
Copy-Item .env.example .env
docker compose build
docker compose up -d db embedding api
docker compose run --rm api python -m app.scripts.wait_for_dependencies
docker compose exec -T api python -m app.scripts.migrate
docker compose exec -T api python -m app.scripts.migrate --database test
docker compose exec -T api python -m app.scripts.seed
docker compose up                                              # make dev
docker compose exec -T api pytest -q                           # make test-api
docker compose run --rm --no-deps web pnpm test                 # make test-web
```

`make help` lists every target with its description.
</details>

The first build downloads the embedding model (~90 MB) into the image. Later builds are
cached, and nothing reaches the network at run time.

---

## What you are given

| Area | State |
|---|---|
| Next.js 16 app shell, layout, navigation, design-system primitives | Provided |
| Mock session with a practice switcher | Provided |
| Patient detail route `/patients/[patientId]` | Provided and working |
| `/search` route | **Shell only — yours to build** |
| FastAPI service, config, connection pool, error envelope, request logging | Provided |
| Migration runner, seed loader, health endpoint | Provided |
| Embedding service (ONNX MiniLM, 384-dim) | Provided, not part of the assignment |
| Embedding client with batching and error translation | Provided |
| Synthetic dataset: 3 practices, 715 patients, 2,400 documents | Provided |
| Test harness, fixtures, deterministic embedding stub | Provided |
| Base tables `practices`, `users`, `patients`, `clinical_documents` | Provided |
| Chunk and embedding storage | **Yours to design** |
| Indexing workflow | **Yours to build** |
| `POST /api/clinical-search` | **Returns 501 — yours to build** |
| Acceptance tests | **Yours to write** |

### Where your work goes

| Task | Start here |
|---|---|
| Chunk and embedding schema | [`database/migrations/README.md`](database/migrations/README.md) |
| Indexing workflow | [`services/api/app/features/indexing/README.md`](services/api/app/features/indexing/README.md) |
| Search endpoint | [`services/api/app/features/search/README.md`](services/api/app/features/search/README.md) |
| Search UI | [`apps/web/features/search/README.md`](apps/web/features/search/README.md) |
| Tests | [`services/api/tests/acceptance/README.md`](services/api/tests/acceptance/README.md) |
| Synthetic dataset | [`docs/DATASET.md`](docs/DATASET.md) |

---

## Session and practice context

The provided mock session associates each demo user with one practice. The search request
must not accept a client-selected practice identifier, and results must remain isolated to
the authenticated user's current practice.

Use the dropdown in the header to switch between the supplied demo identities while
testing. The implementation of the search boundary is part of the exercise.

---

## Layout

```text
├── apps/web/                     Next.js 16, App Router, Tailwind v4
│   ├── app/                      routes: /, /search, /patients/[id], /api/demo-session
│   ├── components/ui/            design-system primitives
│   ├── features/                 feature-local code — search goes here
│   └── lib/                      server-only API client, types, formatting
├── services/
│   ├── api/                      FastAPI
│   │   ├── app/features/         health, session, patients, search*, indexing*
│   │   ├── app/clients/          embedding client
│   │   ├── app/scripts/          migrate, seed, index*, smoke, wait_for_dependencies
│   │   └── tests/                harness, worked examples, acceptance skeletons*
│   └── embedding/                provided embedding service
├── database/
│   ├── init/                     first-boot extension and test database
│   ├── migrations/               0001 base schema; add 0002 for your chunks*
│   └── seed/                     generator plus committed CSVs
└── docs/                         design document and dataset notes

* your work
```

---

## Configuration

Copy `.env.example` to `.env`. It holds no credentials worth protecting and is safe to
commit as an example; `.env` itself is git-ignored.

| Variable | Default | Notes |
|---|---|---|
| `DATABASE_URL` | `postgresql://clinical:local_dev_only@db:5432/clinical_search` | |
| `TEST_DATABASE_URL` | …`/clinical_search_test` | Created on first boot |
| `EMBEDDING_SERVICE_URL` | `http://embedding:8080` | |
| `EMBEDDING_MAX_BATCH_SIZE` | `64` | Service rejects larger batches |
| `SEARCH_DEFAULT_LIMIT` | `10` | |
| `SEARCH_MAX_LIMIT` | `25` | |
| `SEARCH_MAX_QUERY_LENGTH` | `500` | |
| `EMBEDDING_FAILURE_RATE` | `0.0` | Set to `1.0` to exercise the failure UI |
| `API_BASE_URL` | `http://api:8000` | Server-side only |

---

## Provided service contracts

Review [`services/embedding/README.md`](services/embedding/README.md) for the embedding API,
input limits, and failure responses. Respecting that contract is required; how it shapes
your implementation is a design decision.

---

## Testing

```bash
make test              # backend + frontend, no containers beyond the database
make test-api
make test-web
make test-integration  # needs the real embedding container
make lint              # ruff, eslint
make typecheck
```

A fresh clone is green. Candidate-owned acceptance placeholders remain marked `xfail` until
their behavior is implemented and tested.

---

## Submitting

Open a pull request against `main` and complete the
[`PULL_REQUEST_TEMPLATE.md`](PULL_REQUEST_TEMPLATE.md) provided beside this README. It asks
for architecture, tradeoffs, chunking and ranking decisions, limitations, and AI-tool
disclosure.

If you run out of time, submit what works and be explicit about what is incomplete. That is
read as good judgement. Polish does not substitute for practice isolation, source evidence,
idempotent indexing, or a working end-to-end flow.

---

## Troubleshooting

**`make setup` cannot reach the Docker daemon** — start Docker Desktop and retry.

**Database container exits immediately** — the volume was created by an older Postgres.
`make destroy` then `make setup`.

**`pgvector types are not available`** — migrations have not run. `make migrate`.

**Search returns 501** — expected. That endpoint is your task.

**Integration tests skip** — the embedding container is not up.
`docker compose up -d embedding`, then wait for its health check.

**Web shows "The API is not reachable"** — check `docker compose logs api`. The API needs a
migrated database to answer `/api/session`.

**`pnpm install` warns about ignored build scripts** — already handled via
`onlyBuiltDependencies` in `apps/web/package.json`; run `pnpm install` once more.
