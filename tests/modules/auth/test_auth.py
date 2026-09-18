"""Fake-OIDC login flow tests (SCRUM-90).

- Covers authorize → callback → session cookie → /me → logout
- Error codes: `USER_NOT_REGISTERED`, `USER_DEACTIVATED`, `UNAUTHENTICATED`
- No Zitadel Cloud or PostgreSQL
"""

import json

from app.modules.auth.seeds import AUTHOR_ID, AUTHOR_SUB, DEACTIVATED_SUB, UNKNOWN_SUB, seed_users


def _complete_login(client, db_session, sub: str | None = None):
    seed_users(db_session)
    params = {"sub": sub} if sub is not None else {}
    login = client.get("/auth/login", params=params, follow_redirects=False)
    assert login.status_code == 302
    authorize = client.get(login.headers["location"], follow_redirects=False)
    assert authorize.status_code == 302
    callback = client.get(authorize.headers["location"], follow_redirects=False)
    return callback


def test_unregistered_sub_returns_user_not_registered(client, db_session):
    callback = _complete_login(client, db_session, UNKNOWN_SUB)
    assert callback.status_code == 403
    body = callback.json()
    assert body["code"] == "USER_NOT_REGISTERED"
    assert "message" in body


def test_deactivated_user_returns_user_deactivated(client, db_session):
    callback = _complete_login(client, db_session, DEACTIVATED_SUB)
    assert callback.status_code == 403
    assert callback.json()["code"] == "USER_DEACTIVATED"


def test_happy_path_sets_httponly_samesite_cookie_and_me(client, db_session):
    callback = _complete_login(client, db_session, AUTHOR_SUB)
    assert callback.status_code == 302
    assert callback.headers["location"] == "http://localhost:3000/auth/done"

    set_cookie = callback.headers["set-cookie"].lower()
    assert "veritask_session=" in set_cookie
    assert "httponly" in set_cookie
    assert "samesite=lax" in set_cookie

    me = client.get("/me")
    assert me.status_code == 200
    body = me.json()
    assert body == {
        "id": str(AUTHOR_ID),
        "name": "Author One",
        "email": "author@veritask.test",
        "role": "author",
    }


def test_me_without_cookie_is_unauthenticated(client):
    me = client.get("/me")
    assert me.status_code == 401
    assert me.json()["code"] == "UNAUTHENTICATED"


def test_logout_clears_session_and_redirects_to_end_session(client, db_session):
    callback = _complete_login(client, db_session, AUTHOR_SUB)
    assert callback.status_code == 302
    assert client.get("/me").status_code == 200

    logout = client.post("/auth/logout", follow_redirects=False)
    assert logout.status_code == 302
    location = logout.headers["location"]
    assert "/_fake/oidc/end_session" in location
    assert "post_logout_redirect_uri=" in location

    me = client.get("/me")
    assert me.status_code == 401
    assert me.json()["code"] == "UNAUTHENTICATED"


def test_openapi_has_no_password_fields(client):
    spec = client.get("/openapi.json")
    assert spec.status_code == 200
    dumped = json.dumps(spec.json()).lower()
    assert "password" not in dumped
