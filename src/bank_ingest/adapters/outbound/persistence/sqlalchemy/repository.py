"""SQLAlchemy implementation of EventRepositoryPort."""

from sqlalchemy import exists as sa_exists
from sqlalchemy import select
from sqlalchemy.orm import Session

from bank_ingest.adapters.outbound.persistence.sqlalchemy.models import (
    FinancialEventModel,
)
from bank_ingest.domain.entities import FinancialEvent
from bank_ingest.domain.enums import (
    Bank,
    Currency,
    NotificationType,
    TransactionType,
)
from bank_ingest.domain.ports.event_repository import EventRepositoryPort
from bank_ingest.domain.value_objects import CardInfo, EventId, MessageId, Money


class SqlAlchemyEventRepository(EventRepositoryPort):
    """Concrete repository backed by SQLAlchemy sessions.

    Uses session.merge() for idempotent upsert semantics on save.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, event: FinancialEvent) -> None:
        model = _to_model(event)
        self._session.merge(model)

    def find_by_id(self, event_id: EventId) -> FinancialEvent | None:
        model = self._session.get(FinancialEventModel, event_id.value)
        if model is None:
            return None
        return _to_domain(model)

    def find_by_message_id(self, message_id: MessageId) -> list[FinancialEvent]:
        stmt = select(FinancialEventModel).where(
            FinancialEventModel.message_id == message_id.value
        )
        models = self._session.scalars(stmt).all()
        return [_to_domain(m) for m in models]

    def exists(self, event_id: EventId) -> bool:
        stmt = select(sa_exists().where(FinancialEventModel.id == event_id.value))
        return bool(self._session.scalar(stmt))


def _to_model(event: FinancialEvent) -> FinancialEventModel:
    """Map a domain FinancialEvent to an ORM model."""
    return FinancialEventModel(
        id=event.id.value,
        message_id=event.message_id.value,
        bank=event.bank.value,
        event_type=event.event_type.value,
        merchant=event.merchant,
        transaction_date=event.transaction_date,
        card_brand=event.card.brand,
        card_last4=event.card.last4,
        authorization_code=event.authorization_code,
        transaction_type=event.transaction_type.value,
        amount_cents=event.amount.amount,
        currency=event.amount.currency.value,
        raw_data=event.raw_data,
        created_at=event.created_at,
    )


def _to_domain(model: FinancialEventModel) -> FinancialEvent:
    """Map an ORM model back to a domain FinancialEvent."""
    return FinancialEvent(
        id=EventId(value=model.id),
        message_id=MessageId(value=model.message_id),
        bank=Bank(model.bank),
        event_type=NotificationType(model.event_type),
        merchant=model.merchant,
        transaction_date=model.transaction_date,
        card=CardInfo(brand=model.card_brand, last4=model.card_last4),
        authorization_code=model.authorization_code,
        transaction_type=TransactionType(model.transaction_type),
        amount=Money(amount=model.amount_cents, currency=Currency(model.currency)),
        raw_data=model.raw_data,
        created_at=model.created_at,
    )
