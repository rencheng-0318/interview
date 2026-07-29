# Clinical Record Semantic Search — submission

## Summary

<!-- What you implemented, and the primary user flow from typing a query to reading a result. -->

## Architecture

<!--
The path from source documents to indexed chunks to patient-level results. A diagram is
welcome but optional.
-->

## Decisions and tradeoffs

### Chunking strategy

<!-- Chunk size, overlap, whether you used section boundaries, how you handled the
     256-token truncation limit, and whether document types are treated differently. -->

### Database representation

<!-- Your chunk/embedding schema, constraints, indexes, and the ON DELETE behaviour. -->

### Vector index

<!-- Did you add one? If so, which type and operator class, and why. If not, why exact
     search is reasonable at this dataset size, and when that stops being true. -->

### Ranking and patient aggregation

<!-- How many chunks you retrieve before grouping, how you collapse to one row per patient,
     how you stop one patient with many documents dominating, and how you pick the snippet. -->

### Practice isolation

<!-- Where the filter is applied, and how you convinced yourself it cannot be bypassed. -->

### Error handling

<!-- Behaviour for invalid queries, an unavailable embedding service, unindexable
     documents, and database failures. -->

### Testing strategy

<!-- What you tested and at which boundary. Which tests use the deterministic stub and
     which need the real embedding service, and why. -->

## Reproduction

```bash
# Exact commands to start the services, migrate, seed, index, test, and use the feature.
```

## Search quality

<!-- Try a few of the example queries. Did the expected patients surface? Anything that
     ranked oddly, and your read on why. -->

## Limitations and next steps

<!-- Be direct. What is incomplete, fragile, or simplified? What would you do next, and
     what would you change before this ran against real records? -->

## Known defects

<!-- Anything you know is broken. Naming it is better than leaving it to be found. -->

## AI-tool disclosure

**Tools used:**

**Where they materially contributed:**

**How you reviewed or tested the generated work:**

**At least one suggestion you rejected, changed, or independently verified:**

<!-- Be specific. This is a question about your judgement, not about tooling. -->

## Checklist

- [ ] The application starts from the documented commands
- [ ] Migrations apply successfully
- [ ] Data can be seeded reproducibly
- [ ] The indexing command completes and reports useful counts
- [ ] Re-running indexing does not duplicate unchanged chunks
- [ ] Changed documents are reindexed
- [ ] Natural-language search returns semantically related records
- [ ] Results are restricted to the current practice
- [ ] Each patient appears at most once in the primary result list
- [ ] Every patient result includes supporting source evidence
- [ ] Loading, empty, validation, and failure states are handled
- [ ] Important backend and frontend behaviour is tested
- [ ] No credentials or real patient data are committed
- [ ] Similarity is never presented as diagnosis, confidence, or clinical certainty
