"""Test modul suites.

PBI-2, sub task "[QA] Suite testing".

Dua test di bawah sudah jalan dan memakai pola yang benar. Sisanya
masih TODO, ditulis sebagai daftar acceptance criteria yang harus
dibuktikan. Hapus tanda skip satu per satu sambil fitur dikerjakan.
"""

import pytest


def test_buat_suite_berhasil(client):
    response = client.post(
        "/suites",
        json={"name": "Ketenagakerjaan 2026", "description": "Kasus seputar hubungan kerja"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Ketenagakerjaan 2026"
    assert body["status"] == "active"


def test_nama_suite_duplikat_ditolak(client):
    """AC PBI-2: nama suite yang sudah dipakai tidak bisa dipakai ulang."""
    payload = {"name": "Ketenagakerjaan 2026", "description": None}

    first = client.post("/suites", json=payload)
    assert first.status_code == 201

    second = client.post("/suites", json=payload)
    assert second.status_code == 409
    assert second.json()["code"] == "conflict"


@pytest.mark.skip(reason="TODO(PBI-2): butuh modul cases")
def test_suite_berisi_kasus_approved_tidak_bisa_dihapus(client):
    """AC PBI-2: suite berisi kasus approved hanya bisa diarsipkan."""


@pytest.mark.skip(reason="TODO(PBI-2): butuh modul cases")
def test_suite_kosong_tidak_bisa_diekspor(client):
    """AC PBI-2: suite kosong ditandai jelas dan tidak bisa ikut ekspor."""


@pytest.mark.skip(reason="TODO(PBI-2): butuh modul cases")
def test_daftar_suite_menampilkan_jumlah_kasus(client):
    """AC PBI-2: daftar suite menampilkan jumlah kasus per suite."""
