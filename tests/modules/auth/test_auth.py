"""Fake-OIDC login flow tests (SCRUM-90).

- Covers authorize → callback → session cookie → /me → logout
- Error codes: `USER_NOT_REGISTERED`, `USER_DEACTIVATED`, `UNAUTHENTICATED`
- No Zitadel Cloud or PostgreSQL
"""

import json
from datetime import UTC, datetime

from app.modules.auth.models import User, UserSession
from app.modules.auth.seeds import (
    AUTHOR_ID,
    AUTHOR_SUB,
    DEACTIVATED_SUB,
    UNKNOWN_SUB,
    seed_users,
)
from app.shared.config import get_settings
from app.shared.security import Role


def _complete_login(client, db_session, sub: str | None = None, email: str | None = None):
    # TODO: assumes AUTH_OIDC_MODE=fake; does not exercise Zitadel
    seed_users(db_session)
    params = {}
    if sub is not None:
        params["sub"] = sub
    if email is not None:
        params["email"] = email
    login = client.get("/auth/login", params=params, follow_redirects=False)
    assert login.status_code == 302
    authorize = client.get(login.headers["location"], follow_redirects=False)
    assert authorize.status_code == 302
    callback = client.get(authorize.headers["location"], follow_redirects=False)
    return callback


def test_unregistered_sub_returns_user_not_registered(client, db_session):
    """Test untuk pengguna yang tidak terdaftar. Logs in with a sub that's not in users table."""
    callback = _complete_login(client, db_session, UNKNOWN_SUB)
    assert callback.status_code == 403
    body = callback.json()
    assert body["code"] == "USER_NOT_REGISTERED"
    assert "message" in body


def test_deactivated_user_returns_user_deactivated(client, db_session):
    """Test untuk pengguna yang dinonaktifkan. Logs in with a sub that is in users table but is not active."""
    callback = _complete_login(client, db_session, DEACTIVATED_SUB)
    assert callback.status_code == 403
    assert callback.json()["code"] == "USER_DEACTIVATED"


def test_null_sub_binds_on_matching_email(client, db_session):
    seed_users(db_session)
    pending = User(
        email="pending@veritask.test",
        name="Pending Author",
        role=Role.AUTHOR,
        zitadel_sub=None,
        is_active=True,
    )
    db_session.add(pending)
    db_session.commit()
    new_sub = "888888888888888888"
    callback = _complete_login(client, db_session, new_sub, email="pending@veritask.test")
    assert callback.status_code == 302
    db_session.refresh(pending)
    assert pending.zitadel_sub == new_sub


def test_email_with_different_sub_is_not_rebound(client, db_session):
    callback = _complete_login(client, db_session, UNKNOWN_SUB, email="author@veritask.test")
    assert callback.status_code == 403
    assert callback.json()["code"] == "USER_NOT_REGISTERED"


def test_deactivated_email_with_null_sub_stays_unbound(client, db_session):
    seed_users(db_session)
    pending = User(
        email="inactive-pending@veritask.test",
        name="Inactive Pending",
        role=Role.VIEWER,
        zitadel_sub=None,
        is_active=False,
    )
    db_session.add(pending)
    db_session.commit()
    callback = _complete_login(
        client, db_session, "777777777777777777", email="inactive-pending@veritask.test"
    )
    assert callback.status_code == 403
    assert callback.json()["code"] == "USER_DEACTIVATED"
    db_session.refresh(pending)
    assert pending.zitadel_sub is None


def test_login_sets_absolute_expires_at(client, db_session):
    callback = _complete_login(client, db_session, AUTHOR_SUB)
    assert callback.status_code == 302
    session = db_session.query(UserSession).one()
    created = session.last_activity_at
    expires = session.expires_at
    if created.tzinfo is None:
        created = created.replace(tzinfo=UTC)
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=UTC)
    delta_minutes = (expires - created).total_seconds() / 60
    assert abs(delta_minutes - get_settings().absolute_session_lifetime_minutes) < 1
    assert datetime.now(UTC) < expires


def test_happy_path_sets_httponly_samesite_cookie_and_me(client, db_session):
    """Test untuk pengguna yang terdaftar dan aktif. Logs in with a sub that is in users table and is active."""
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
    """Test untuk pengguna yang tidak memiliki sesi. Logs in without a session cookie."""
    me = client.get("/me")
    assert me.status_code == 401
    assert me.json()["code"] == "UNAUTHENTICATED"


def test_logout_clears_session_and_redirects_to_end_session(client, db_session):
    """Test untuk logout. Logs out and clears the session cookie."""
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
    """Test untuk OpenAPI spec. Checks that the spec does not contain password fields."""
    spec = client.get("/openapi.json")
    assert spec.status_code == 200
    dumped = json.dumps(spec.json()).lower()
    # TODO: substring check is weak (false positives/negatives vs schema fields)
    assert "password" not in dumped
