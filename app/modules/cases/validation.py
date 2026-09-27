"""Modul validasi terpusat untuk kasus hukum.

PBI-3, SCRUM-106. Satu modul dipakai untuk tiga hal:
1. Validator Pydantic saat kasus dibuat atau diubah
2. Kode error HTTP untuk field yang gagal
3. Indikator kelengkapan yang disimpan bersama draft

Pola `case_code` dan rumus kelengkapan masih placeholder. Klarifikasi
#7 dan kontrak SCRUM-103 belum final, jadi keduanya ditandai di sini
dan boleh diganti tanpa memindahkan aturan ke tempat lain.
"""

import re
from typing import Any

from app.shared.exceptions import ValidationError

# Placeholder Klarifikasi #7: huruf atau angka di depan, lalu huruf,
# angka, titik, garis bawah, atau tanda hubung. Bukan pola final.
PLACEHOLDER_CASE_CODE_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9._-]{1,63}$"
_POLA_KODE = re.compile(PLACEHOLDER_CASE_CODE_PATTERN)

SPLIT_TAG_REQUIRED = "SPLIT_TAG_REQUIRED"
CASE_CODE_INVALID = "CASE_CODE_INVALID"
FIELD_REQUIRED = "FIELD_REQUIRED"
VALIDATION_ERROR = "VALIDATION_ERROR"

_TAG_SAH = frozenset({"dev", "test"})
_FIELD_RUJUKAN = ("regulation_type", "regulation_number", "pasal")
# Placeholder sampai SCRUM-107 mengunci definisi "lengkap".
_BAGIAN_KELENGKAPAN = (
    "identity.title",
    "identity.question",
    "case_code",
    "split_tag",
    "legal_refs",
    "answer_criteria",
    "traps",
)


def periksa_isian(data: dict[str, Any]) -> None:
    """Tolak isian yang melanggar aturan simpan. Lolos berarti boleh disimpan."""
    _periksa_kode(data.get("case_code"))
    _periksa_identitas(data.get("identity"))
    _periksa_tag(data.get("split_tag"))
    _periksa_rujukan(data.get("legal_refs"))


def hitung_kelengkapan(data: dict[str, Any]) -> dict[str, Any]:
    """Persen bagian yang sudah terisi. Rumusnya placeholder, bukan SCRUM-107."""
    identitas = data.get("identity") if isinstance(data.get("identity"), dict) else {}
    terisi = {
        "identity.title": bool(_teks(identitas.get("title"))),
        "identity.question": bool(_teks(identitas.get("question"))),
        "case_code": _POLA_KODE.fullmatch(_teks(data.get("case_code"))) is not None,
        "split_tag": data.get("split_tag") in _TAG_SAH,
        "legal_refs": _rujukan_lengkap(data.get("legal_refs")),
        "answer_criteria": _kriteria_ada(data.get("answer_criteria")),
        "traps": _jebakan_ada(data.get("traps")),
    }
    belum = [nama for nama in _BAGIAN_KELENGKAPAN if not terisi[nama]]
    jumlah = len(_BAGIAN_KELENGKAPAN)
    return {
        "pct": round((jumlah - len(belum)) * 100 / jumlah),
        "missing": belum,
        "contract": "placeholder",
    }


def respons_dari_pydantic(errors: list[dict[str, Any]]) -> dict[str, str]:
    """Ubah error bawaan FastAPI jadi kode yang sama dengan modul ini.

    Field yang tidak dikirim atau string kosong menjadi FIELD_REQUIRED.
    Batasan lain (panjang, rentang, tipe JSON) memakai VALIDATION_ERROR
    dan pesan Pydantic, bukan "wajib diisi".
    """
    if not errors:
        return {"code": VALIDATION_ERROR, "message": "Isian kasus tidak valid"}
    dipetakan = [_petakan(error) for error in errors]
    for kode in (SPLIT_TAG_REQUIRED, CASE_CODE_INVALID):
        for item in dipetakan:
            if item["code"] == kode:
                return item
    return dipetakan[0]


def jalur_field(loc: Any) -> str:
    """`('body', 'legal_refs', 0, 'pasal')` menjadi `legal_refs[0].pasal`."""
    bagian: list[str] = []
    for item in loc or ():
        if item == "body":
            continue
        if isinstance(item, int):
            if bagian:
                bagian[-1] = f"{bagian[-1]}[{item}]"
            else:
                bagian.append(f"[{item}]")
            continue
        bagian.append(str(item))
    return ".".join(bagian)


def _periksa_kode(nilai: Any) -> None:
    kode = _teks(nilai)
    if not kode:
        raise ValidationError("Field case_code wajib diisi", code=FIELD_REQUIRED, field="case_code")
    if _POLA_KODE.fullmatch(kode) is None:
        raise ValidationError(
            "Format case_code belum final. Pola yang dipakai sekarang adalah "
            "placeholder Klarifikasi #7.",
            code=CASE_CODE_INVALID,
            field="case_code",
        )


def _periksa_identitas(nilai: Any) -> None:
    if not isinstance(nilai, dict):
        raise ValidationError("Field identity wajib diisi", code=FIELD_REQUIRED, field="identity")
    for nama in ("title", "question"):
        if not _teks(nilai.get(nama)):
            field = f"identity.{nama}"
            raise ValidationError(f"Field {field} wajib diisi", code=FIELD_REQUIRED, field=field)


def _periksa_tag(nilai: Any) -> None:
    if nilai not in _TAG_SAH:
        raise ValidationError(
            "Tag dev/test wajib diisi",
            code=SPLIT_TAG_REQUIRED,
            field="split_tag",
        )


def _periksa_rujukan(nilai: Any) -> None:
    if not isinstance(nilai, list) or len(nilai) < 1:
        raise ValidationError(
            "Minimal satu rujukan hukum sampai level pasal",
            code=FIELD_REQUIRED,
            field="legal_refs",
        )
    for indeks, rujukan in enumerate(nilai):
        if not isinstance(rujukan, dict):
            field = f"legal_refs[{indeks}]"
            raise ValidationError(f"Field {field} wajib diisi", code=FIELD_REQUIRED, field=field)
        for nama in _FIELD_RUJUKAN:
            if not _teks(rujukan.get(nama)):
                field = f"legal_refs[{indeks}].{nama}"
                raise ValidationError(
                    f"Field {field} wajib diisi",
                    code=FIELD_REQUIRED,
                    field=field,
                )


def _rujukan_lengkap(nilai: Any) -> bool:
    if not isinstance(nilai, list) or not nilai:
        return False
    return all(
        isinstance(rujukan, dict) and all(_teks(rujukan.get(nama)) for nama in _FIELD_RUJUKAN)
        for rujukan in nilai
    )


def _kriteria_ada(nilai: Any) -> bool:
    if not isinstance(nilai, dict):
        return False
    for kunci in ("must_contain", "must_not_contain"):
        butir = nilai.get(kunci) or []
        if isinstance(butir, list) and any(_teks(item) for item in butir):
            return True
    return bool(_teks(nilai.get("expected_conclusion")))


def _jebakan_ada(nilai: Any) -> bool:
    if not isinstance(nilai, list):
        return False
    return any(isinstance(item, dict) and _teks(item.get("description")) for item in nilai)


def _teks(nilai: Any) -> str:
    if nilai is None:
        return ""
    return str(nilai).strip()


def _petakan(error: dict[str, Any]) -> dict[str, str]:
    field = jalur_field(error.get("loc", ()))
    tipe = str(error.get("type", ""))
    if field == "split_tag" or field.endswith(".split_tag"):
        return {
            "code": SPLIT_TAG_REQUIRED,
            "message": "Tag dev/test wajib diisi",
            "field": "split_tag",
        }
    if field == "case_code" and "pattern" in tipe:
        return {
            "code": CASE_CODE_INVALID,
            "message": (
                "Format case_code belum final. Pola yang dipakai sekarang adalah "
                "placeholder Klarifikasi #7."
            ),
            "field": "case_code",
        }
    if not field:
        return {"code": VALIDATION_ERROR, "message": "Isian kasus tidak valid"}
    if _kosong_atau_hilang(error):
        return {
            "code": FIELD_REQUIRED,
            "message": f"Field {field} wajib diisi",
            "field": field,
        }
    return {
        "code": VALIDATION_ERROR,
        "message": _pesan_pydantic(error),
        "field": field,
    }


def _kosong_atau_hilang(error: dict[str, Any]) -> bool:
    """Field tidak dikirim, atau isiannya string kosong setelah strip."""
    if str(error.get("type", "")) == "missing":
        return True
    nilai = error.get("input")
    return isinstance(nilai, str) and not nilai.strip()


def _pesan_pydantic(error: dict[str, Any]) -> str:
    pesan = error.get("msg")
    if isinstance(pesan, str) and pesan.strip():
        return pesan
    return "Isian kasus tidak valid"
