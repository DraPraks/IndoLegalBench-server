"""Logika bisnis modul providers.

PBI-10 Registri produk AI yang akan diukur.

Ini satu-satunya pintu masuk yang boleh dipanggil modul lain. Service
tidak boleh menyentuh HTTP. Kalau aturan bisnis dilanggar, lempar
exception dari app.shared.exceptions.
"""

import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.providers import repository
from app.modules.providers.crypto import CredentialError, credential_hint, encrypt_credential
from app.modules.providers.models import AiProduct
from app.modules.providers.schemas import AiProductCreate, AiProductRead, AiProductUpdate
from app.shared.exceptions import ConflictError, NotFoundError, ValidationError

NAME_TAKEN = "AI_PRODUCT_NAME_TAKEN"


def create_product(
    db: Session, payload: AiProductCreate, *, created_by: uuid.UUID
) -> AiProductRead:
    _pastikan_nama_bebas(db, payload.name)
    product = AiProduct(
        name=payload.name,
        provider_type=payload.provider_type,
        base_url=payload.base_url,
        model_name=payload.model_name,
        credential_encrypted=_enkripsi(payload.credential),
        credential_hint=credential_hint(payload.credential),
        rate_limit_per_minute=payload.rate_limit_per_minute,
        monthly_budget_idr=payload.monthly_budget_idr,
        created_by=created_by,
    )
    try:
        tersimpan = repository.create(db, product)
    except IntegrityError:
        db.rollback()
        raise ConflictError(
            f"Nama produk AI '{payload.name}' sudah dipakai",
            code=NAME_TAKEN,
        ) from None
    return _tampilkan(tersimpan)


def get_product(db: Session, product_id: uuid.UUID) -> AiProductRead:
    return _tampilkan(_wajib_ada(db, product_id))


def list_products(db: Session, *, is_active: bool | None) -> list[AiProductRead]:
    return [_tampilkan(item) for item in repository.list_products(db, is_active=is_active)]


def update_product(db: Session, product_id: uuid.UUID, payload: AiProductUpdate) -> AiProductRead:
    product = _wajib_ada(db, product_id)
    perubahan = payload.model_dump(exclude_unset=True)
    credential = perubahan.pop("credential", None)

    if "name" in perubahan:
        _pastikan_nama_bebas(db, perubahan["name"], kecuali=product.id)
        product.name = perubahan.pop("name")

    for field, value in perubahan.items():
        setattr(product, field, value)

    if credential is not None:
        product.credential_encrypted = _enkripsi(credential)
        product.credential_hint = credential_hint(credential)

    try:
        tersimpan = repository.save(db, product)
    except IntegrityError:
        db.rollback()
        raise ConflictError(
            f"Nama produk AI '{product.name}' sudah dipakai",
            code=NAME_TAKEN,
        ) from None
    return _tampilkan(tersimpan)


def set_active(db: Session, product_id: uuid.UUID, *, is_active: bool) -> AiProductRead:
    product = _wajib_ada(db, product_id)
    product.is_active = is_active
    return _tampilkan(repository.save(db, product))


def _enkripsi(plaintext: str) -> bytes:
    try:
        return encrypt_credential(plaintext)
    except CredentialError as exc:
        raise ValidationError(str(exc), field="credential") from None


def _wajib_ada(db: Session, product_id: uuid.UUID) -> AiProduct:
    product = repository.get_by_id(db, product_id)
    if product is None:
        raise NotFoundError("Produk AI tidak ditemukan")
    return product


def _pastikan_nama_bebas(db: Session, name: str, *, kecuali: uuid.UUID | None = None) -> None:
    ada = repository.get_by_name(db, name)
    if ada is not None and ada.id != kecuali:
        raise ConflictError(f"Nama produk AI '{name}' sudah dipakai", code=NAME_TAKEN)


def _tampilkan(product: AiProduct) -> AiProductRead:
    return AiProductRead(
        id=product.id,
        name=product.name,
        provider_type=product.provider_type,
        base_url=product.base_url,
        model_name=product.model_name,
        credential_hint=product.credential_hint,
        has_credential=True,
        rate_limit_per_minute=product.rate_limit_per_minute,
        monthly_budget_idr=product.monthly_budget_idr,
        is_active=product.is_active,
        last_test_at=product.last_test_at,
        last_test_status=product.last_test_status,
        last_test_message=product.last_test_message,
        created_by=product.created_by,
        created_at=product.created_at,
        updated_at=product.updated_at,
    )
