"""SQLAlchemy ORM model for financial events."""

from datetime import datetime

from sqlalchemy import JSON, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from bank_ingest.adapters.outbound.persistence.sqlalchemy.base import Base


class FinancialEventModel(Base):
    """ORM model mapping to the financial_events table."""

    __tablename__ = "financial_events"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    message_id: Mapped[str] = mapped_column(String, index=True)
    bank: Mapped[str] = mapped_column(String)
    event_type: Mapped[str] = mapped_column(String)
    merchant: Mapped[str] = mapped_column(String)
    transaction_date: Mapped[datetime] = mapped_column(DateTime)
    card_brand: Mapped[str] = mapped_column(String)
    card_last4: Mapped[str] = mapped_column(String(4))
    authorization_code: Mapped[str] = mapped_column(String)
    transaction_type: Mapped[str] = mapped_column(String)
    amount_cents: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String)
    raw_data: Mapped[dict[str, object]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime)
