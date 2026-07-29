# Synthetic dataset

All practices, patients, clinicians, and documents in this repository are fabricated. No
production data, customer data, or protected health information is included.

## Shape

| | |
|---|---|
| Practices | 3 |
| Patients | 715 |
| Documents | 2,400 |
| Document types | `diagnostic_note`, `specialist_note`, `radiology_report`, `lab_report` |

The committed CSV files under `database/seed/data/` are the source of truth. `make seed`
loads them deterministically and can be run repeatedly.

The corpus spans multiple practices and includes realistic variation in document length,
formatting, and content quality. Do not assume that every document is suitable for
indexing or that the strongest semantic match belongs to the current practice.

Your implementation should satisfy the observable requirements in
`docs/TAKE_HOME_DESIGN.md` without depending on hard-coded record identifiers or dataset
ordering.
