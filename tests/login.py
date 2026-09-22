"""Shared fake-OIDC login for pytest. Do not override get_current_user."""

from app.modules.auth.seeds import AUTHOR_SUB, seed_users


def complete_login(client, db_session, sub: str | None = None):
    """Seeds users, follows authorize → callback, leaves `veritask_session` on the client."""
    seed_users(db_session)
    params = {"sub": sub if sub is not None else AUTHOR_SUB}
    login = client.get("/auth/login", params=params, follow_redirects=False)
    assert login.status_code == 302
    authorize = client.get(login.headers["location"], follow_redirects=False)
    assert authorize.status_code == 302
    callback = client.get(authorize.headers["location"], follow_redirects=False)
    return callback
