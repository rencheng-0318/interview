# Semantic search API

`router.py` currently returns `501`. The request and response contracts are defined in
`schemas.py`.

Implement semantic retrieval that returns a ranked, practice-isolated list of unique
patients with supporting evidence from the indexed source documents. Requests must be
validated, dependency failures must produce appropriate API errors, and internal details
must not leak to clients.

The query shape, ranking strategy, patient aggregation, evidence selection, and database
access design are yours to implement and justify. Follow the contracts and observable
requirements in `docs/TAKE_HOME_DESIGN.md`.
