"""Unit test modul validasi kasus.

PBI-3, SCRUM-106. Tiap aturan diuji di sini, terpisah dari HTTP.
Pola case_code dan rumus kelengkapan masih placeholder.
"""

import pytest

from app.modules.cases.validation import (
    CASE_CODE_INVALID,
    FIELD_REQUIRED,
    PLACEHOLDER_CASE_CODE_PATTERN,
    SPLIT_TAG_REQUIRED,
    hitung_kelengkapan,
    jalur_field,
    periksa_isian,
    respons_dari_pydantic,
)
from app.shared.exceptions import ValidationError

RUJUKAN = {
    "regulation_type": "uu",
    "regulation_number": "13",
    "year": 2003,
    "pasal": "151",
}


def _data(**ubah):
    data = {
        "case_code": "PHK-001",
        "identity": {"title": "PHK sepihak", "question": "Apakah sah?", "category": None},
        "legal_refs": [dict(RUJUKAN)],
        "answer_criteria": {
            "must_contain": ["surat"],
            "must_not_contain": [],
            "expected_conclusion": "tidak sah",
        },
        "traps": [{"description": "Mencampur upah", "expected_model_behavior": "menolak"}],
        "split_tag": "dev",
    }
    data.update(ubah)
    return data


def test_isian_lengkap_lolos():
    periksa_isian(_data())


def test_pola_placeholder_tertulis_di_konstanta():
    assert PLACEHOLDER_CASE_CODE_PATTERN.startswith("^")
    assert "A-Za-z0-9" in PLACEHOLDER_CASE_CODE_PATTERN


@pytest.mark.parametrize("kode", ["", " ", "a", "ada spasi", "kode!"])
def test_case_code_placeholder_ditolak(kode):
    with pytest.raises(ValidationError) as info:
        periksa_isian(_data(case_code=kode))

    assert info.value.field == "case_code"
    if kode.strip():
        assert info.value.code == CASE_CODE_INVALID
    else:
        assert info.value.code == FIELD_REQUIRED


@pytest.mark.parametrize(
    ("identitas", "field"),
    [
        (None, "identity"),
        ({}, "identity.title"),
        ({"title": "  ", "question": "Ada"}, "identity.title"),
        ({"title": "Ada", "question": ""}, "identity.question"),
    ],
)
def test_identitas_wajib(identitas, field):
    with pytest.raises(ValidationError) as info:
        periksa_isian(_data(identity=identitas))

    assert info.value.code == FIELD_REQUIRED
    assert info.value.field == field


@pytest.mark.parametrize("tag", [None, "", "train"])
def test_split_tag_wajib(tag):
    with pytest.raises(ValidationError) as info:
        periksa_isian(_data(split_tag=tag))

    assert info.value.code == SPLIT_TAG_REQUIRED
    assert info.value.field == "split_tag"


def test_tanpa_rujukan_ditolak():
    with pytest.raises(ValidationError) as info:
        periksa_isian(_data(legal_refs=[]))

    assert info.value.code == FIELD_REQUIRED
    assert info.value.field == "legal_refs"


@pytest.mark.parametrize("hilang", ["regulation_type", "regulation_number", "pasal"])
def test_rujukan_wajib_sampai_pasal(hilang):
    rujukan = dict(RUJUKAN)
    rujukan[hilang] = "  "
    with pytest.raises(ValidationError) as info:
        periksa_isian(_data(legal_refs=[rujukan]))

    assert info.value.code == FIELD_REQUIRED
    assert info.value.field == f"legal_refs[0].{hilang}"


def test_kelengkapan_penuh_seratus_persen():
    hasil = hitung_kelengkapan(_data())

    assert hasil["pct"] == 100
    assert hasil["missing"] == []
    assert hasil["contract"] == "placeholder"


def test_kelengkapan_tanpa_jebakan_dan_kriteria_belum_penuh():
    hasil = hitung_kelengkapan(
        _data(answer_criteria={"must_contain": [], "must_not_contain": []}, traps=[])
    )

    assert hasil["pct"] == 71
    assert hasil["missing"] == ["answer_criteria", "traps"]
    assert hasil["contract"] == "placeholder"


def test_jalur_field_rujukan():
    assert jalur_field(("body", "legal_refs", 0, "pasal")) == "legal_refs[0].pasal"


def test_error_pydantic_split_tag_didahulukan():
    body = respons_dari_pydantic(
        [
            {"type": "missing", "loc": ("body", "identity", "title")},
            {"type": "missing", "loc": ("body", "split_tag")},
        ]
    )

    assert body["code"] == SPLIT_TAG_REQUIRED
    assert body["field"] == "split_tag"


def test_error_pydantic_pola_case_code():
    body = respons_dari_pydantic(
        [{"type": "string_pattern_mismatch", "loc": ("body", "case_code")}]
    )

    assert body["code"] == CASE_CODE_INVALID
    assert body["field"] == "case_code"
