# Clinical Record Semantic Search

## Full-stack take-home exercise

Build an end-to-end semantic search feature over the supplied synthetic clinical records.
The exercise evaluates product judgment, data design, backend and frontend implementation,
testing, and the ability to explain technical decisions.

## 1. Product scenario

A user enters a natural-language description of a clinical presentation and receives a
ranked list of patients in their current practice whose existing records are semantically
relevant.

Each result must identify the source record and passage that explains the match. This is a
retrieval feature: it must not generate diagnoses, infer unsupported conditions, or present
similarity as clinical confidence.

## 2. Time and scope

Repository access is provided for 48 consecutive hours. Expected implementation effort is
approximately 8–12 focused hours; spending the full window coding is neither required nor
rewarded.

Prioritize a working, explainable end-to-end feature. State clearly what is incomplete or
intentionally simplified.

## 3. Provided foundation

The repository includes:

- A Next.js application shell and patient-detail route
- A FastAPI service with configuration, database access, session context, and error handling
- PostgreSQL 18 with pgvector
- A deterministic synthetic multi-practice clinical dataset
- A local embedding service and typed client
- Migration, seed, health, smoke, and test infrastructure
- Starter API, indexing, UI, and test placeholders

The root `README.md` contains setup commands and points to the relevant entry points.

## 4. Assignment

### 4.1 Searchable representation

Design and migrate the database representation needed for semantic retrieval. Preserve
enough source metadata to support practice isolation, patient-level results, evidence, and
safe updates when source documents change.

The schema and indexing choices are yours. Explain important constraints, indexes, and
lifecycle decisions in the pull request.

### 4.2 Indexing workflow

Complete the provided indexing command so the supplied documents become searchable.

The workflow must:

- Process the supplied source documents through the provided embedding service
- Be safe to run repeatedly without duplicating unchanged indexed content
- Reflect relevant changes to source documents
- Handle an individual unindexable document without corrupting the overall index
- Report enough completion information to diagnose success and failure

Choose and justify the content segmentation, change detection, persistence, and failure
handling strategies.

### 4.3 Semantic-search API

Implement `POST /api/clinical-search` using the contracts in the starter code.

The endpoint must:

- Validate the request
- Use vector-based semantic retrieval rather than keyword-only matching
- Restrict results to the authenticated user's current practice
- Return a ranked list with each patient appearing at most once
- Include supporting source evidence for every patient result
- Behave predictably when nothing is indexed or no results match
- Return useful client-safe errors when dependencies fail

The client must not select or override a practice identifier. Practice isolation must be
enforced within the trusted backend retrieval boundary, before records are exposed to a
client.

Ranking, aggregation, and evidence-selection behavior are design decisions. Document the
tradeoffs.

### 4.4 Search experience

Complete the provided Next.js search page.

Users must be able to:

- Enter and submit a natural-language query
- Optionally filter by supported document type
- Read a ranked patient-level result list
- Understand which existing record passage supports each result
- Navigate to the existing patient-detail route

Handle idle, loading, results, no-results, invalid-input, and dependency-failure states.
The visual design is flexible and is not graded for polish, but the experience should be
clear and intuitive.

### 4.5 Operational visibility

Provide enough diagnostics to investigate indexing and search failures without logging
document bodies, supporting passages, patient names, or embedding vectors.

## 5. Provided service constraints

The embedding service is part of the supplied platform and is not an assignment component.
Its public contract is documented in `services/embedding/README.md`.

Key compatibility constraints include:

- Embedding dimensionality: 384
- Maximum input sequence: 256 tokens
- Maximum texts per request: 64
- Maximum characters per text: 8,000
- Blank input is rejected

Your implementation must respect the service contract. How those limits influence the
design is for you to decide.

## 6. Required behavior

### Semantic relevance

The primary retrieval mechanism must be vector similarity through PostgreSQL and pgvector.
Exact ranking is not prescribed, but meaningful paraphrases must retrieve relevant source
records within the result limit.

### Source grounding

Every result must be traceable to an existing synthetic clinical document and include a
supporting excerpt. Do not generate unsupported clinical explanations.

### Patient-level results

Multiple matching records may belong to one patient, but the primary list must contain each
patient at most once.

### Practice isolation

Results must never include a patient from another practice. The authenticated session is
the source of practice context; no request field may override it.

### Repeatability

Re-running indexing against unchanged data must not create duplicates. Relevant source
changes must be reflected without requiring a complete manual reset.

### Failure handling

Invalid requests, no-results cases, embedding-service failures, database failures, and
unindexable source documents must produce deliberate behavior rather than silent failure or
partial corruption.

## 7. Security and privacy

Treat the synthetic records as sensitive clinical data:

- Do not send records to an unapproved external service
- Do not commit credentials or local environment files
- Do not expose practice selection through the search request
- Do not return complete documents when an excerpt is sufficient
- Do not log document content, patient names, excerpts, or vectors
- Do not expose stack traces or database-driver details to clients

## 8. Maintainability

Keep the implementation understandable and proportionate to the exercise. Use the existing
project conventions and avoid unrelated frameworks or infrastructure.

The reviewer should be able to understand the data flow, failure behavior, and important
tradeoffs from the code and pull-request description.

## 9. Out of scope

The following are not required:

- Production authentication or authorization infrastructure
- A hosted embedding provider
- Diagnosis generation or clinical decision support
- Perfect handling of negation, historical conditions, or contradictory notes
- A sophisticated reranking model
- Production-scale infrastructure
- Unrelated visual redesign or optional product features

## 10. Submission

Open a pull request against `main` and complete the provided
`PULL_REQUEST_TEMPLATE.md`. Include reproducible commands, architecture and data flow,
important decisions and tradeoffs, limitations, known defects, incomplete requirements,
and AI-tool disclosure.

If time expires, submit the working portion and describe the remaining gaps directly.


## 11. Definition of done

Before submitting, confirm that:

- The application runs from the documented commands
- Natural-language search returns semantically related records
- Results are restricted to the current practice
- Every result includes supporting source evidence
- Required UI and failure states are handled
- Important backend and frontend behavior is tested
- No credentials or real patient data are committed
- Similarity is never presented as diagnosis or clinical certainty
- The pull request explains the implementation and its limitations
