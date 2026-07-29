# Migrations

SQL migrations are applied in filename order by `app.scripts.migrate`. Each file runs in a
transaction, and applied filenames are recorded so rerunning migrations is a no-op.

```bash
make migrate
```

`0001_base_schema.sql` contains the provided source tables. Do not modify it. Add a new
numbered migration for the searchable representation required by your solution.

The schema, constraints, indexes, and deletion behavior are design decisions for you to
make and explain. The resulting model must support the functional and isolation
requirements in `docs/TAKE_HOME_DESIGN.md` and remain safe when existing source data is
present.
