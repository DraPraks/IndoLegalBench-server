# Testing

Test first, then implement. Commit the failing test before the code that makes it pass, using the subjects in [AGENTS.md](../AGENTS.md):

```
test(<scope>): red — <behavior that fails>
feat(<scope>): green — <behavior that passes>
refactor(<scope>): <what was tidied>
```

The red commit is the point. It proves the test can fail, so a later green commit means the behavior arrived, not that the test was empty.

## Where each test goes

| Layer | Holds | Leave out |
|---|---|---|
| `service.py` tests | Business rules | HTTP. No `HTTPException`. Raise `app/shared/exceptions.py` and let `app/main.py` map them. |
| `router.py` tests | Status codes and that mapping | Business rules already covered in the service |
| `repository.py` tests | The query itself | Everything that is not a query |

Mock the repository or an external provider, not the service under test. Tests should be fast and deterministic so people actually run them.

## Positive, negative, corner

Every slice needs all three. Suites already does this in `tests/modules/suites/test_suites.py`:

- Positive: `test_buat_suite_berhasil` creates a suite and expects `201`.
- Negative: `test_nama_kosong_ditolak` sends an empty name and expects `422`.
- Corner: `test_nama_yang_sudah_dihapus_tetap_tidak_boleh_dipakai` deletes a suite, then expects the old name to stay reserved (`409`).

Match that shape for the subtask you are on. Do not invent a second feature to have more tests.

## How to run

```bash
pytest                          # whole suite
pytest tests/modules/suites     # one module
```

`pytest` already applies coverage on `app/` via `pyproject.toml`. That is the run. No extra report format.
