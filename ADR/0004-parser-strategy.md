# ADR-0004: Parser Strategy for Bank Notifications

**Status:** Accepted
**Date:** 2026-03-16
**Author:** `bank_ingest` Project

---

## Context

The `bank_ingest` system processes email notifications sent by multiple banks that describe financial events.

These notifications present several characteristics that influence system design:

1. Each bank uses **different email formats**.
2. A single bank may send **multiple notification types**.
3. Email formats **may change over time**.
4. Messages may contain **both HTML and plain text**.
5. The semantic structure of the data is **not standardized across banks**.

Examples of possible notification types include:

- credit card transaction
- debit card transaction
- credit card payment
- incoming transfer
- outgoing transfer
- automatic debit
- withdrawal alert

The system must extract from these messages a set of **normalized financial events** that can be stored and analyzed.

For the initial version of the system, the scope is limited to:

- **Bank:** BAC Credomatic
- **Notification type:** card transaction notification
- **Gmail label:** `Transacciones`

---

## Decision

The system will use a **modular and extensible parser architecture**, organized by **bank** and **notification type**.

The general structure will be:

```id="pij6q6"
parser/
├── base.py
└── bac/
    ├── classifier.py
    ├── transaction_notification.py
    └── patterns.py
```

Each bank will have its own module.

Each notification type will have its own independent parser.

---

## Design Principles

### Separation between classification and parsing

The system separates two responsibilities:

**Classification**

Determining:

- which bank sent the message
- which type of notification it represents

**Parsing**

Extracting structured data from the message.

This separation improves:

- maintainability
- extensibility
- clarity of individual parsers

---

### Abstract base parser

All parsers must implement a common contract defined in:

```id="y5b1v0"
parser/base.py
```

This contract defines the minimum operations a parser must support.

Conceptual example:

```python id="suhb1e"
class BaseParser(ABC):

    def can_parse(message: SourceMessage) -> bool:
        ...

    def parse(message: SourceMessage) -> FinancialEvent:
        ...
```

Responsibilities:

- determine whether the parser can process the message
- extract the required fields
- produce a normalized financial event

---

### Bank-specific classifiers

Each bank has a dedicated **classifier**.

Location:

```id="1hlivn"
parser/<bank>/classifier.py
```

The classifier analyzes characteristics of the message such as:

- sender address
- sender domain
- email subject
- characteristic phrases
- HTML structure
- text patterns

Example classification logic:

```python id="o9yjz8"
if sender_domain == "baccredomatic.com":
    bank = BAC
```

The classifier also determines the **notification type**.

---

### Notification-specific parsers

Each notification type is implemented as a dedicated parser.

Example:

```id="v2m98a"
transaction_notification.py
```

The parser is responsible for extracting structured fields from the notification.

Fields defined for the initial version:

| Field              | Description                  |
| ------------------ | ---------------------------- |
| merchant           | merchant name                |
| transaction_date   | transaction date             |
| card_brand         | card brand                   |
| card_last4         | last four digits of the card |
| authorization_code | authorization code           |
| transaction_type   | transaction type             |
| amount             | transaction amount           |
| currency           | transaction currency         |

---

### Pattern isolation

Parsing patterns are defined in:

```id="pbo4hs"
patterns.py
```

This includes:

- regular expressions
- identifying phrases
- HTML selectors
- relevant text fragments

Separating patterns from parser logic allows:

- modifying expressions without changing the parser logic
- easier maintenance
- improved readability

---

## Parsing Flow

The complete parsing process follows these steps:

1. obtain a `SourceMessage`
2. run bank classifiers
3. determine the notification type
4. select the appropriate parser
5. execute the parser
6. produce a `FinancialEvent`

If parsing fails:

- an error artifact is generated
- the message is labeled as `error`
- the message remains unread

---

## Output Model

The parser produces a normalized financial event.

Conceptual example:

```json id="8kp9p5"
{
  "bank": "BAC",
  "event_type": "card_transaction",
  "merchant": "AMPM",
  "transaction_date": "2026-03-15",
  "card_brand": "VISA",
  "card_last4": "1234",
  "authorization_code": "A82F3D",
  "transaction_type": "purchase",
  "amount": 12000,
  "currency": "CRC"
}
```

This event is then persisted in the database.

---

## Error Handling

Possible parsing errors include:

- required field not found
- unexpected format
- unsupported notification type
- structural changes in email templates

When an error occurs:

1. an artifact is created in `data/errors`
2. the message receives the label `error`
3. the message remains unread

This enables manual review.

---

## Scalability

The strategy allows new banks to be added easily.

Example:

```id="r3t5yn"
parser/
├── bac/
├── bcr/
├── bncr/
└── scotia/
```

Each bank can contain multiple parsers:

```id="2s5rmo"
parser/bac/
├── classifier.py
├── transaction_notification.py
├── debit_notification.py
└── payment_notification.py
```

---

## Relationship to the Hexagonal Architecture

Parsers are implemented as **outbound adapters**.

Their responsibility is to translate external data (emails) into domain models.

The domain layer must not depend on:

- regular expressions
- HTML structures
- bank-specific formats

Parsers encapsulate these external dependencies.

---

## Consequences

### Benefits

- extensible architecture
- small and specialized parsers
- clear separation of responsibilities
- improved maintainability
- easy addition of new banks

---

### Costs

- increased number of files
- need to maintain classifiers
- greater design discipline required

These costs are acceptable given the heterogeneous nature of bank notifications.

---

## Alternatives Considered

### Single parser

One alternative would be to implement a single parser handling all banks and notification types.

This option was rejected because it would:

- create overly complex files
- complicate maintenance
- make it harder to add new banks
- increase the risk of regressions

---

## References

Eric Evans — _Domain-Driven Design_

Martin Fowler — _Patterns of Enterprise Application Architecture_

Alistair Cockburn — _Hexagonal Architecture_
[https://alistair.cockburn.us/hexagonal-architecture](https://alistair.cockburn.us/hexagonal-architecture)

---

## Status

This parser strategy is **accepted** for the initial version of the system.
