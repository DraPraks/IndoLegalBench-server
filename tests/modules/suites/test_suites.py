"""Test modul suites.

PBI-2, sub task "[QA] Suite testing" plus PBI-1 RBAC on live /suites routes.
"""

import pytest

from app.modules.auth.seeds import ADMIN_SUB, AUTHOR_SUB, REVIEWER_SUB, VIEWER_SUB
from tests.login import complete_login

_SUITE_PAYLOAD = {"name": "Ketenagakerjaan 2026", "description": "Kasus seputar hubungan kerja"}


def test_buat_suite_berhasil(client, db_session):
    complete_login(client, db_session, AUTHOR_SUB)
    response = client.post("/suites", json=_SUITE_PAYLOAD)

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Ketenagakerjaan 2026"
    assert body["status"] == "active"


def test_nama_suite_duplikat_ditolak(client, db_session):
    """AC PBI-2: nama suite yang sudah dipakai tidak bisa dipakai ulang."""
    complete_login(client, db_session, AUTHOR_SUB)
    payload = {"name": "Ketenagakerjaan 2026", "description": None}

    first = client.post("/suites", json=payload)
    assert first.status_code == 201

    second = client.post("/suites", json=payload)
    assert second.status_code == 409
    assert second.json()["code"] == "conflict"


def test_unauthenticated_suites_is_unauthenticated(client):
    listed = client.get("/suites")
    assert listed.status_code == 401
    assert listed.json()["code"] == "UNAUTHENTICATED"

    created = client.post("/suites", json=_SUITE_PAYLOAD)
    assert created.status_code == 401
    assert created.json()["code"] == "UNAUTHENTICATED"


def test_viewer_suites_are_forbidden(client, db_session):
    complete_login(client, db_session, VIEWER_SUB)
    listed = client.get("/suites")
    assert listed.status_code == 403
    assert listed.json()["code"] == "FORBIDDEN"

    created = client.post("/suites", json=_SUITE_PAYLOAD)
    assert created.status_code == 403
    assert created.json()["code"] == "FORBIDDEN"


def test_reviewer_can_list_but_not_create(client, db_session):
    complete_login(client, db_session, REVIEWER_SUB)
    listed = client.get("/suites")
    assert listed.status_code == 200

    created = client.post("/suites", json=_SUITE_PAYLOAD)
    assert created.status_code == 403
    assert created.json()["code"] == "FORBIDDEN"


def test_admin_can_create_suite(client, db_session):
    complete_login(client, db_session, ADMIN_SUB)
    response = client.post(
        "/suites",
        json={"name": "Admin Suite", "description": None},
    )
    assert response.status_code == 201


@pytest.mark.skip(reason="TODO(PBI-2): butuh modul cases")
def test_suite_berisi_kasus_approved_tidak_bisa_dihapus(client):
    """AC PBI-2: suite berisi kasus approved hanya bisa diarsipkan."""


@pytest.mark.skip(reason="TODO(PBI-2): butuh modul cases")
def test_suite_kosong_tidak_bisa_diekspor(client):
    """AC PBI-2: suite kosong ditandai jelas dan tidak bisa ikut ekspor."""


@pytest.mark.skip(reason="TODO(PBI-2): butuh modul cases")
def test_daftar_suite_menampilkan_jumlah_kasus(client):
    """AC PBI-2: daftar suite menampilkan jumlah kasus per suite."""
