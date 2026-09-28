"""SCRUM-75 SCRUM-114: ai_products schema.

SQLite in-memory, same as the other model tests. These lock the columns
and checks the ticket names: unique name, positive limits, lowercase
enum values, and last-test fields that stay empty until SCRUM-116.
"""

from decimal import Decimal

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.modules.auth.models import User
from app.modules.providers.models import AiProduct, LastTestStatus, ProviderType
from app.shared.security import Role


def _admin(db_session) -> User:
    user = User(email="admin@veritask.test", name="Admin", role=Role.ADMIN)
    db_session.add(user)
    db_session.commit()
    return user


def _product(created_by, **override) -> AiProduct:
    values = {
        "name": "AiYU",
        "provider_type": ProviderType.OPENAI_COMPATIBLE,
        "base_url": "https://api.example.test/v1",
        "model_name": "aiyu-1",
        "credential_encrypted": b"ciphertext-not-the-secret",
        "credential_hint": "cret",
        "rate_limit_per_minute": 30,
        "monthly_budget_idr": Decimal("1500000.00"),
        "created_by": created_by,
    }
    values.update(override)
    return AiProduct(**values)


def test_new_product_is_active_and_untested(db_session):
    admin = _admin(db_session)
    product = _product(admin.id)
    db_session.add(product)
    db_session.commit()

    assert product.is_active is True
    assert product.created_at is not None
    assert product.updated_at is not None
    assert product.last_test_at is None
    assert product.last_test_status is None
    assert product.last_test_message is None


def test_provider_type_is_stored_lowercase(db_session):
    admin = _admin(db_session)
    db_session.add(_product(admin.id))
    db_session.commit()

    stored = db_session.execute(text("SELECT provider_type FROM ai_products")).scalar_one()
    assert stored == "openai_compatible"


def test_each_provider_type_can_be_stored(db_session):
    admin = _admin(db_session)
    for index, provider_type in enumerate(ProviderType):
        db_session.add(_product(admin.id, name=f"Product {index}", provider_type=provider_type))
    db_session.commit()

    stored = (
        db_session.execute(text("SELECT provider_type FROM ai_products ORDER BY name"))
        .scalars()
        .all()
    )
    assert stored == ["openai_compatible", "custom_http"]


def test_last_test_status_is_stored_lowercase(db_session):
    admin = _admin(db_session)
    db_session.add(_product(admin.id, last_test_status=LastTestStatus.FAILED))
    db_session.commit()

    stored = db_session.execute(text("SELECT last_test_status FROM ai_products")).scalar_one()
    assert stored == "failed"


def test_duplicate_name_is_rejected(db_session):
    admin = _admin(db_session)
    db_session.add(_product(admin.id))
    db_session.commit()

    db_session.add(_product(admin.id, model_name="aiyu-2"))
    with pytest.raises(IntegrityError):
        db_session.commit()


@pytest.mark.parametrize("rate_limit", [0, -1])
def test_rate_limit_must_be_positive(db_session, rate_limit):
    admin = _admin(db_session)
    db_session.add(_product(admin.id, rate_limit_per_minute=rate_limit))

    with pytest.raises(IntegrityError):
        db_session.commit()


@pytest.mark.parametrize("budget", [Decimal("0"), Decimal("-1")])
def test_monthly_budget_must_be_positive(db_session, budget):
    admin = _admin(db_session)
    db_session.add(_product(admin.id, monthly_budget_idr=budget))

    with pytest.raises(IntegrityError):
        db_session.commit()
