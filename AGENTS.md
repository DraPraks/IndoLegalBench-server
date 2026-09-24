# Agent guide

Follow this file, then [README.md](README.md) for the layout and [CONTRIBUTING.md](CONTRIBUTING.md) for git flow.

## Read this first

The server is a modular monolith. Each domain lives in `app/modules/<name>/` with `router.py`, `service.py`, `repository.py`, `models.py`, and `schemas.py`. `app/modules/health/` is the reference module. Read it before adding a new one.

Two boundary rules, same as the README:

1. A module may call another module's `service.py`. A module may not import another module's `repository.py` or `models.py`.
2. `service.py` must not touch HTTP. No `Request`, `Response`, or `HTTPException`. Raise exceptions from `app/shared/exceptions.py` and let `app/main.py` translate them.

## Scope

Implement the subtask you were given. When that subtask is one resource, create, read, update, and delete are one slice, not four pull requests. Do not widen into a neighboring module unless the subtask needs it.

## Test first

Commit in three steps on the branch. Use Conventional Commits, as in CONTRIBUTING. The type carries the phase, so the subject does not repeat it.

```
test(<scope>): red — <behavior that fails>
feat(<scope>): green — <behavior that passes>
refactor(<scope>): <what was tidied>
```

Each slice needs one positive case, one negative case, and one corner case. How to place those tests is in [docs/testing.md](docs/testing.md).

Run `pytest` before opening the pull request. Coverage is already configured in `pyproject.toml`. Do not omit `app/` modules to make the number look better. The team bar stays the one in CONTRIBUTING: coverage above 60 percent.

## Hard stops

- Do not push to `main` or `staging`. Open a pull request against `staging`.
- Do not commit `.env`, credentials, API keys, or Zitadel keys.
- Do not import another module's `repository.py` or `models.py`. Editing those files is normal when the subtask is in that module, or when the subtask genuinely needs a schema change there. Say why in the pull request.
- When `schemas.py` changes, regenerate `openapi.json` in the same pull request. CI fails the pull request if the contract is stale.
