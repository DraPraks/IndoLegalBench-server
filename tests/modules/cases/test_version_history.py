"""Version history. SCRUM-137.

Reads stay Author and Admin. Viewer and Reviewer are not granted, even
though SCRUM-73 and SCRUM-138 name Viewer.
"""

import uuid

import pytest
from sqlalchemy.orm import Session

from app.modules.auth.models import User
from app.shared.exceptions import ForbiddenError
from app.shared.security import Role
from tests.modules.cases.test_cases import _badan, _buat, _ganti, _setujui, _suite
from tests.modules.conftest import USER_ID_QA


def _seed_author(db: Session) -> None:
    db.add(
        User(
            id=USER_ID_QA,
            name="Pengguna QA",
            email="qa-history@veritask.test",
            role=Role.AUTHOR,
        )
    )
    db.commit()


def _approved_case(client, db_session) -> tuple[str, str]:
    _seed_author(db_session)
    suite_id = _suite(client)
    dibuat = _buat(client, suite_id).json()
    _setujui(db_session, dibuat["id"])
    return suite_id, dibuat["id"]


def test_riwayat_versi_pertama_kosong_dan_menyebut_pembuat(as_role, db_session):
    client = as_role(Role.AUTHOR)
    _, case_id = _approved_case(client, db_session)

    response = client.get(f"/cases/{case_id}/versions")

    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 1
    assert rows[0]["version_no"] == 1
    assert rows[0]["status"] == "approved"
    assert rows[0]["changed"] == []
    assert rows[0]["author"] == {"id": str(USER_ID_QA), "name": "Pengguna QA"}


def test_perubahan_kategori_tercatat_sendiri(as_role, db_session):
    client = as_role(Role.AUTHOR)
    _, case_id = _approved_case(client, db_session)
    assert client.post(f"/cases/{case_id}/versions").status_code == 201
    kategori = _badan()
    kategori["identity"] = {**kategori["identity"], "category": "pidana"}
    assert client.put(f"/cases/{case_id}", json=kategori).status_code == 200

    history = client.get(f"/cases/{case_id}/versions").json()

    assert history[1]["version_no"] == 2
    assert history[1]["changed"] == ["category"]


def test_kasus_yang_tidak_ada_404(as_role):
    client = as_role(Role.AUTHOR)

    response = client.get(f"/cases/{uuid.uuid4()}/versions")

    assert response.status_code == 404


@pytest.mark.parametrize("role", [Role.VIEWER, Role.REVIEWER])
def test_viewer_dan_reviewer_tidak_boleh_membaca_riwayat(as_role, buat_pengguna, db_session, role):
    client = as_role(Role.AUTHOR)
    _, case_id = _approved_case(client, db_session)
    _ganti(client, buat_pengguna(role, user_id=uuid.uuid4()))

    history = client.get(f"/cases/{case_id}/versions")

    assert history.status_code == 403
    assert history.json()["code"] == ForbiddenError.code
