"""Shared fake-OIDC login for pytest. Do not override get_current_user."""

from app.modules.auth.seeds import AUTHOR_SUB, seed_users


def complete_login(client, db_session, sub: str | None = None, email: str | None = None):
    """Seeds users, follows authorize → callback, leaves `veritask_session` on the client.

    With neither `sub` nor `email`, logs in as the seeded author.
    """
    seed_users(db_session)
    params = {}
    if sub is not None:
        params["sub"] = sub
    if email is not None:
        params["email"] = email
    if not params:
        params["sub"] = AUTHOR_SUB
    login = client.get("/auth/login", params=params, follow_redirects=False)
    assert login.status_code == 302
    authorize = client.get(login.headers["location"], follow_redirects=False)
    assert authorize.status_code == 302
    callback = client.get(authorize.headers["location"], follow_redirects=False)
    return callback
