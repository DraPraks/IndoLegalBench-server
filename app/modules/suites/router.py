"""Endpoint HTTP modul suites.

Router hanya menerjemahkan HTTP ke pemanggilan service dan sebaliknya.
Tidak ada logika bisnis di sini, dan tidak ada query database di sini.

TODO(PBI-2): aktifkan kembali dependency require_roles setelah PBI-1 selesai.
"""

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.modules.suites import service
from app.modules.suites.schemas import SuiteCreate, SuiteRead, SuiteUpdate
from app.shared.database import get_db
from app.shared.pagination import Page

router = APIRouter(prefix="/suites", tags=["suites"])


@router.post(
    "",
    response_model=SuiteRead,
    status_code=status.HTTP_201_CREATED,
    summary="Buat suite baru",
)
def create_suite(payload: SuiteCreate, db: Session = Depends(get_db)) -> SuiteRead:
    suite = service.create_suite(db, payload)
    return SuiteRead.model_validate(suite)


@router.get("", response_model=Page[SuiteRead], summary="Daftar suite")
def list_suites(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> Page[SuiteRead]:
    # TODO(PBI-2): pindahkan penyusunan Page ini ke service kalau logikanya
    # sudah lebih dari sekadar offset dan limit.
    from app.modules.suites import repository

    offset = (page - 1) * size
    items = repository.list_all(db, offset=offset, limit=size)
    total = repository.count_all(db)
    return Page[SuiteRead](
        items=[SuiteRead.model_validate(item) for item in items],
        total=total,
        page=page,
        size=size,
    )


@router.get("/{suite_id}", response_model=SuiteRead, summary="Detail satu suite")
def get_suite(suite_id: uuid.UUID, db: Session = Depends(get_db)) -> SuiteRead:
    return SuiteRead.model_validate(service.get_suite(db, suite_id))


@router.patch("/{suite_id}", response_model=SuiteRead, summary="Ubah suite")
def update_suite(
    suite_id: uuid.UUID, payload: SuiteUpdate, db: Session = Depends(get_db)
) -> SuiteRead:
    return SuiteRead.model_validate(service.update_suite(db, suite_id, payload))


@router.delete(
    "/{suite_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Hapus suite, ditolak kalau berisi kasus approved",
)
def delete_suite(suite_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    service.delete_suite(db, suite_id)


@router.post("/{suite_id}/archive", response_model=SuiteRead, summary="Arsipkan suite")
def archive_suite(suite_id: uuid.UUID, db: Session = Depends(get_db)) -> SuiteRead:
    return SuiteRead.model_validate(service.archive_suite(db, suite_id))
