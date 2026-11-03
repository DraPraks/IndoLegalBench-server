"""Akses database modul runs.

ATURAN: hanya runs/service.py yang boleh memanggil file ini. Modul lain
tidak boleh mengimpor repository milik modul lain.

Isi file ini murni query, tanpa logika bisnis.

TODO(PBI-11, PBI-12, PBI-13): query lain menyusul sesuai kebutuhan service.
"""

import uuid
from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal

from sqlalchemy import exists, func, select
from sqlalchemy.orm import Session

from app.modules.runs.models import CallLog, MeasurementSession


def product_has_sessions(db: Session, product_id: uuid.UUID) -> bool:
    """Sesi yang diarsipkan tetap terhitung: datanya tidak pernah dihapus (AC10)."""
    return bool(db.scalar(select(exists().where(MeasurementSession.product_id == product_id))))


def count_sessions_by_product(
    db: Session, product_ids: Sequence[uuid.UUID]
) -> dict[uuid.UUID, int]:
    """Satu query untuk banyak produk, sesi arsip ikut terhitung. Produk tanpa sesi tidak ada."""
    if not product_ids:
        return {}
    rows = db.execute(
        select(MeasurementSession.product_id, func.count())
        .where(MeasurementSession.product_id.in_(product_ids))
        .group_by(MeasurementSession.product_id)
    )
    return dict(rows.tuples().all())


class CallLogRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def add(self, row: CallLog) -> None:
        self._db.add(row)
        self._db.flush()

    def sum_cost_since(self, product_id: uuid.UUID, start: datetime) -> Decimal:
        total = self._db.scalar(
            select(func.coalesce(func.sum(CallLog.cost_idr), 0)).where(
                CallLog.product_id == product_id,
                CallLog.started_at >= start,
                CallLog.cost_idr.is_not(None),
            )
        )
        return Decimal(total)

    def sum_cost_since_by_product(
        self, product_ids: Sequence[uuid.UUID], start: datetime
    ) -> dict[uuid.UUID, Decimal]:
        """Satu query untuk banyak produk. Produk tanpa biaya tidak ada di hasil."""
        if not product_ids:
            return {}
        rows = self._db.execute(
            select(CallLog.product_id, func.sum(CallLog.cost_idr))
            .where(
                CallLog.product_id.in_(product_ids),
                CallLog.started_at >= start,
                CallLog.cost_idr.is_not(None),
            )
            .group_by(CallLog.product_id)
        )
        return {product_id: Decimal(total) for product_id, total in rows}

    def output_token_average(self, product_id: uuid.UUID) -> Decimal | None:
        average = self._db.scalar(
            select(func.avg(CallLog.output_tokens)).where(
                CallLog.product_id == product_id,
                CallLog.output_tokens.is_not(None),
            )
        )
        if average is None:
            return None
        return Decimal(average)

    def attempt_counts(self, product_id: uuid.UUID) -> tuple[int, int]:
        total = self._db.scalar(
            select(func.count()).select_from(CallLog).where(CallLog.product_id == product_id)
        )
        failed = self._db.scalar(
            select(func.count())
            .select_from(CallLog)
            .where(CallLog.product_id == product_id, CallLog.failure_kind.is_not(None))
        )
        return int(total or 0), int(failed or 0)
