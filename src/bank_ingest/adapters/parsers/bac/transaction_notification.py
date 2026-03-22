"""BAC transaction notification parser."""

import re
from datetime import UTC, datetime

from bank_ingest.domain.entities import FinancialEvent, SourceMessage
from bank_ingest.domain.enums import Bank, Currency, NotificationType, TransactionType
from bank_ingest.domain.exceptions import ParsingError
from bank_ingest.domain.ports.parser import ParserPort
from bank_ingest.domain.value_objects import CardInfo, EventId, Money
from bank_ingest.shared.money import parse_amount_string
from bank_ingest.shared.text import extract_table_rows

_KNOWN_CARD_BRANDS = frozenset({"VISA", "AMEX", "MASTERCARD", "MASTER"})

_TRANSACTION_TYPE_MAP: dict[str, TransactionType] = {
    "COMPRA": TransactionType.PURCHASE,
    "RETIRO": TransactionType.WITHDRAWAL,
    "DEVOLUCION": TransactionType.REFUND,
    "DEVOLUCIÓN": TransactionType.REFUND,
    "PAGO": TransactionType.PAYMENT,
}

_MASKED_PAN_PATTERN = re.compile(r"\d{4}$")


class BACTransactionNotificationParser(ParserPort):
    """Parses BAC transaction notification emails into FinancialEvent."""

    @property
    def bank(self) -> Bank:
        return Bank.BAC

    @property
    def notification_type(self) -> NotificationType:
        return NotificationType.TRANSACTION_NOTIFICATION

    def parse(self, message: SourceMessage) -> FinancialEvent:
        rows = extract_table_rows(message.body_html)
        if not rows:
            raise ParsingError(message.id.value, "No table rows found in message body")

        fields = dict(rows)
        raw_data: dict[str, object] = dict(fields)

        merchant = self._require(fields, "Comercio:", message.id.value)
        date_str = self._require(fields, "Fecha:", message.id.value)
        auth_code = self._require(fields, "Autorización:", message.id.value)
        tx_type_str = self._require(fields, "Tipo de Transacción:", message.id.value)
        amount_str = self._require(fields, "Monto:", message.id.value)

        card = self._extract_card(fields, message.id.value)
        transaction_date = self._parse_date(date_str, message.id.value)
        transaction_type = self._map_transaction_type(tx_type_str, message.id.value)
        amount, currency_code = self._parse_amount(amount_str, message.id.value)

        return FinancialEvent(
            id=EventId(),
            message_id=message.id,
            bank=Bank.BAC,
            event_type=NotificationType.TRANSACTION_NOTIFICATION,
            merchant=merchant,
            transaction_date=transaction_date,
            card=card,
            authorization_code=auth_code,
            transaction_type=transaction_type,
            amount=Money(amount=amount, currency=Currency(currency_code)),
            raw_data=raw_data,
            created_at=datetime.now(tz=UTC),
        )

    def _require(self, fields: dict[str, str], key: str, message_id: str) -> str:
        value = fields.get(key)
        if not value:
            raise ParsingError(message_id, f"Missing required field: {key}")
        return value.strip()

    def _extract_card(self, fields: dict[str, str], message_id: str) -> CardInfo:
        for label, value in fields.items():
            if label.upper() in _KNOWN_CARD_BRANDS:
                last4_match = _MASKED_PAN_PATTERN.search(value)
                if not last4_match:
                    raise ParsingError(
                        message_id,
                        f"Cannot extract last4 from card value: {value!r}",
                    )
                return CardInfo(brand=label.upper(), last4=last4_match.group())

        raise ParsingError(message_id, "No card information found")

    def _parse_date(self, date_str: str, message_id: str) -> datetime:
        # BAC format: "Mar 16, 2026, 08:27"
        try:
            return datetime.strptime(date_str.strip(), "%b %d, %Y, %H:%M")
        except ValueError as exc:
            raise ParsingError(message_id, f"Cannot parse date: {date_str!r}") from exc

    def _map_transaction_type(self, raw: str, message_id: str) -> TransactionType:
        normalized = raw.strip().upper()
        tx_type = _TRANSACTION_TYPE_MAP.get(normalized)
        if tx_type is None:
            raise ParsingError(
                message_id,
                f"Unknown transaction type: {raw!r}",
            )
        return tx_type

    def _parse_amount(self, raw: str, message_id: str) -> tuple[int, str]:
        try:
            return parse_amount_string(raw)
        except ValueError as exc:
            raise ParsingError(message_id, f"Cannot parse amount: {raw!r}") from exc
