"""Versi yang sudah disetujui tidak boleh ditimpa. SCRUM-136."""

from app.shared.security import Role
from tests.modules.cases.test_cases import _badan, _buat, _setujui, _suite


def test_put_versi_approved_ditolak_dan_isinya_tetap(as_role, db_session):
    client = as_role(Role.AUTHOR)
    suite_id = _suite(client)
    dibuat = _buat(client, suite_id).json()
    _setujui(db_session, dibuat["id"])

    response = client.put(
        f"/cases/{dibuat['id']}",
        json=_badan(
            identity={
                "title": "Judul yang tidak boleh masuk",
                "question": "Apakah PHK tanpa surat sah?",
                "category": "ketenagakerjaan",
            }
        ),
    )

    assert response.status_code == 409
    assert response.json()["code"] == "VERSION_LOCKED"
    tetap = client.get(f"/cases/{dibuat['id']}").json()
    assert tetap["identity"]["title"] == dibuat["identity"]["title"]
    assert tetap["status"] == "approved"
    assert tetap["version"] == 1
