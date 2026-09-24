# IndoLegalBench Server

Python 3.11, FastAPI, SQLAlchemy, Alembic, PostgreSQL. Tests run with pytest. Lint and format run with ruff. The frontend is a separate repo, `IndoLegalBench-client`.

## Commands

Use Python on the host and Postgres in Docker when changing code.

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
pre-commit install                 # once per clone, scans for secrets
docker compose up -d db
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload      # http://localhost:8000
```

Before opening a pull request:

```bash
pytest
pytest tests/modules/suites
pytest tests/modules/suites/test_suites.py::test_nama_kosong_ditolak
ruff check .
ruff format --check .
python scripts/export_openapi.py
```

CI runs those, plus a secret scan, an image build, and a `/health` smoke test. `pytest` already measures coverage on `app/` through `pyproject.toml`. Do not omit modules to make the number look better. The team bar is coverage above 60 percent.

`python scripts/seed_dev.py` creates local role accounts for trying RBAC. It is development-only and is not a migration.

A new migration:

```bash
alembic revision --autogenerate -m "add cases table"
alembic upgrade head
```

Read the generated file before committing it. Alembic guesses wrong on renames and type changes. Migrations do not run on container start. Leave it that way.

## Layout

One deployment. Each domain is `app/modules/<name>/`. `app/modules/health/` is the reference. Read it before adding a module.

```
app/modules/<name>/   router.py, service.py, repository.py, models.py, schemas.py
app/shared/           config, database, exceptions, security, pagination
app/main.py           router registration and exception handlers
migrations/           Alembic
tests/modules/<name>/ mirrors the module
```

| File | Its job | May touch |
|---|---|---|
| `router.py` | HTTP to service calls | its own service |
| `service.py` | Business rules | its own repository, other modules' services |
| `repository.py` | Queries | its own models |
| `models.py` | SQLAlchemy tables | `Base` from shared |
| `schemas.py` | Request and response shapes, source of `openapi.json` | Pydantic |

A module may call another module's `service.py`. It may not import another module's `repository.py` or `models.py`.

To add a module: create `app/modules/<name>/` with those five files, register the router in `app/main.py`, import the model in `migrations/env.py` if it has a table, and add `tests/modules/<name>/`.

## Code rules

`service.py` does not touch HTTP. No `Request`, `Response`, or `HTTPException`. Raise a subclass from `app/shared/exceptions.py`. `app/main.py` turns it into a response.

```python
suite = repository.get_by_id(db, suite_id)
if suite is None:
    raise NotFoundError("Suite tidak ditemukan")
```

`ConflictError` is the duplicate-name case. `ForbiddenError` is the role case. Ruff line length is 100. Do not hand-edit `openapi.json`. Change `schemas.py`, then run `python scripts/export_openapi.py` and commit the result.

## Testing

Write the failing test first. Three commits on the branch. The type carries the phase, so the subject does not repeat it.

```
test(<scope>): red — <behavior that fails>
feat(<scope>): green — <behavior that passes>
refactor(<scope>): <what was tidied>
```

The red commit has to fail. That is what makes the green commit mean the behavior arrived.

| Tests for | Hold | Leave out |
|---|---|---|
| `service.py` | Business rules | HTTP |
| `router.py` | Status codes and the exception-to-HTTP mapping | Rules already covered in the service |
| `repository.py` | The query | Anything that is not a query |

Mock the repository or an external provider, not the service under test.

For the change you were asked to make, include one positive case, one negative case, and one corner case. Suites already does this in `tests/modules/suites/test_suites.py`:

- Positive: `test_buat_suite_berhasil` creates a suite and expects `201`.
- Negative: `test_nama_kosong_ditolak` sends an empty name and expects `422`.
- Corner: `test_nama_yang_sudah_dihapus_tetap_tidak_boleh_dipakai` deletes a suite, then expects the old name to stay reserved (`409`).

Create, read, update, and delete for one resource are one pull request when that is the change you were asked to make. Do not invent a second feature to have more tests.

## Git

Branch from the latest `staging`. Name it `<type>/<pbi>-<short-description>`, for example `feat/pbi2-suite-crud`. Open the pull request against `staging`. Conventional Commits, English, lowercase subject, no trailing period. One reviewer. Split a diff past roughly 400 lines.

Do not push to `main` or `staging`.

## Boundaries

Always:

- Test first, with the three commits above.
- Run `pytest` and `ruff check .` before the pull request.
- Regenerate `openapi.json` when schemas or routes change.
- Register a new router in `app/main.py`, and its model in `migrations/env.py` when it has a table.

Ask first:

- Adding a dependency.
- A migration that drops or renames a column.
- Editing another module's `models.py` or `repository.py` when this change is not in that module.
- Changing CI, `pyproject.toml`, or pre-commit config.

Never:

- Push to `main` or `staging`.
- Commit `.env`, credentials, API keys, or Zitadel keys. The `providers` module holds other products' credentials. Treat those the same way.
- Import another module's `repository.py` or `models.py`.
- Put HTTP types in `service.py`.
- Delete or skip a failing test to get green.
- Run migrations automatically on container start.
