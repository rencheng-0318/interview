# Indexing workflow

The entry point `app/scripts/index_clinical_documents.py` is a starter stub.

```bash
make index
```

Implement a workflow that makes the supplied clinical documents semantically searchable.
It must be repeatable, reflect changed source content, tolerate an individual document
that cannot be indexed, and report a useful completion summary.

The searchable representation, chunking strategy, change-detection mechanism, transaction
boundaries, and failure policy are yours to design. Respect the provided embedding-service
contract and explain your decisions in the pull request.
