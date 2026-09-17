"""Test endpoint kesehatan.

Test ini sengaja dibuat lengkap sebagai CONTOH POLA. Perhatikan bahwa
test memakai fixture client dari conftest.py, tidak membuat TestClient
sendiri.
"""


def test_health_selalu_menjawab_200(client):
    """Health harus menjawab 200 walaupun database sedang mati.

    Di CI tidak ada PostgreSQL yang menyala, jadi database akan
    berstatus unreachable, dan itu memang perilaku yang diharapkan.
    """
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] in {"ok", "unreachable"}


def test_openapi_schema_tersedia(client):
    """Kontrak OpenAPI harus selalu bisa dihasilkan.

    Kalau test ini gagal, biasanya ada schema Pydantic yang rusak, dan
    frontend tidak akan bisa generate tipe dari kontrak.
    """
    response = client.get("/openapi.json")

    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"]
    assert "/health" in schema["paths"]
    assert "/suites" in schema["paths"]
