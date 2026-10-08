"""Suite snapshots. SCRUM-137.

Creating a snapshot is Admin only. A suite with no approved case is rejected.
"""

import uuid

import pytest

from app.modules.auth.models import User
from app.shared.exceptions import ForbiddenError
from app.shared.security import Role
from tests.modules.cases.test_cases import (
    ADMIN_LAIN,
    _badan,
    _buat,
    _ganti,
    _setujui,
    _suite,
)
from tests.modules.conftest import USER_ID_QA


def _seed(db, user_id, name, email, role) -> None:
    db.add(User(id=user_id, name=name, email=email, role=role))
    db.commit()


def _as_admin(client, buat_pengguna):
    _ganti(client, buat_pengguna(Role.ADMIN, user_id=ADMIN_LAIN, name="Admin QA"))


def test_snapshot_hanya_versi_approved_dan_menolak_suite_kosong(as_role, buat_pengguna, db_session):
    client = as_role(Role.AUTHOR)
    _seed(db_session, USER_ID_QA, "Pengguna QA", "qa-snap@veritask.test", Role.AUTHOR)
    _seed(db_session, ADMIN_LAIN, "Admin QA", "admin-snap@veritask.test", Role.ADMIN)
    suite_id = _suite(client)
    _as_admin(client, buat_pengguna)
    empty = client.post(f"/suites/{suite_id}/snapshots")
    assert empty.status_code == 422
    assert empty.json()["code"] == "NOTHING_TO_SNAPSHOT"

    _ganti(client, buat_pengguna(Role.AUTHOR, user_id=USER_ID_QA, name="Pengguna QA"))
    approved = _buat(client, suite_id).json()
    draft_only = _buat(client, suite_id, case_code="PHK-002").json()
    _setujui(db_session, approved["id"])
    assert client.post(f"/cases/{approved['id']}/versions").status_code == 201
    judul_draf = _badan(case_code="PHK-001")
    judul_draf["identity"] = {**judul_draf["identity"], "title": "Judul draf yang tidak ikut"}
    assert client.put(f"/cases/{approved['id']}", json=judul_draf).status_code == 200

    _as_admin(client, buat_pengguna)
    response = client.post(f"/suites/{suite_id}/snapshots")

    assert response.status_code == 201
    body = response.json()
    assert body["author"] == {"id": str(ADMIN_LAIN), "name": "Admin QA"}
    assert len(body["items"]) == 1
    item = body["items"][0]
    assert item["case_id"] == approved["id"]
    assert item["case_id"] != draft_only["id"]
    assert item["body"]["version_no"] == 1
    assert item["body"]["status"] == "approved"
    assert item["body"]["sections"]["identity.title"] == approved["identity"]["title"]
    assert item["body"]["sections"]["case_code"] == "PHK-001"


def test_suite_arsip_yang_punya_kasus_approved_boleh_di_snapshot(
    as_role, buat_pengguna, db_session
):
    client = as_role(Role.AUTHOR)
    suite_id = _suite(client)
    case_id = _buat(client, suite_id).json()["id"]
    _setujui(db_session, case_id)
    assert client.post(f"/suites/{suite_id}/archive").status_code == 200
    _as_admin(client, buat_pengguna)

    response = client.post(f"/suites/{suite_id}/snapshots")

    assert response.status_code == 201
    assert len(response.json()["items"]) == 1


@pytest.mark.parametrize("role", [Role.AUTHOR, Role.REVIEWER, Role.VIEWER])
def test_bukan_admin_tidak_boleh_membuat_snapshot(as_role, buat_pengguna, db_session, role):
    client = as_role(Role.AUTHOR)
    suite_id = _suite(client)
    case_id = _buat(client, suite_id).json()["id"]
    _setujui(db_session, case_id)
    if role != Role.AUTHOR:
        _ganti(client, buat_pengguna(role, user_id=uuid.uuid4()))

    response = client.post(f"/suites/{suite_id}/snapshots")

    assert response.status_code == 403
    assert response.json()["code"] == ForbiddenError.code
