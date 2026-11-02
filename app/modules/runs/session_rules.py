"""Aturan murni sesi pengukuran, tanpa database. PBI-11 SCRUM-210.

Status percobaan ditulis sebagai string yang sama dengan enum attempts di D2
(pending, running, succeeded, technical_failure), supaya aturan ini bisa diuji
sebelum tabel attempts ada di staging.
"""

from collections.abc import Mapping
from dataclasses import dataclass

# Percobaan yang sudah punya hasil akhir. Gagal teknis tetap selesai: coba ulang
# menambah call_logs, bukan attempts (D2).
_FINAL = frozenset({"succeeded", "technical_failure"})
_NOT_FINAL = frozenset({"pending", "running"})


@dataclass(frozen=True)
class SessionProgress:
    """Progres "X dari N" di daftar sesi (AC10)."""

    completed: int
    total: int


def progress(status_counts: Mapping[str, int]) -> SessionProgress:
    """X = percobaan selesai, N = semua percobaan sesi.

    Status di luar enum D2 ditolak supaya status baru (PBI-12) diputuskan
    dulu, bukan diam-diam terhitung belum selesai.
    """
    unknown = set(status_counts) - _FINAL - _NOT_FINAL
    if unknown:
        raise ValueError(f"Unknown attempt status: {', '.join(sorted(unknown))}")
    completed = sum(count for status, count in status_counts.items() if status in _FINAL)
    return SessionProgress(completed=completed, total=sum(status_counts.values()))
