# ADR-0006: Parser Selection Strategy

**Status:** Accepted
**Date:** 2026-03-16
**Author:** `bank_ingest` Project

---

## Context

The `bank_ingest` system processes bank notification emails in order to extract structured financial events.

The overall processing pipeline is:

1. Retrieve the message from the source (Gmail)
2. Classify the message
3. Select the appropriate parser
4. Parse the message content
5. Persist the resulting event
6. Update the processing state of the message

Message classification occurs along two dimensions:

- **Issuing bank** (`Bank`)
- **Notification type** (`NotificationType`)

Example:

```
Bank.BAC
NotificationType.TRANSACTION_NOTIFICATION
```

Once the message has been classified, the system must automatically determine which parser should be used.

The system is expected to grow to approximately:

- ~5 banks
- ~3 notification types per bank

This implies around **15 possible parser combinations**.

Three main strategies were evaluated:

1. **Explicit parser registry**
2. **Parser auto-discovery**
3. **Chain of Responsibility**

---

## Decision

The system will use an **explicit parser registry**, indexed by the pair:

```
(Bank, NotificationType)
```

The registry will be responsible for resolving the correct parser for a given classification.

Conceptual representation:

```python
registry: dict[tuple[Bank, NotificationType], BaseParser]
```

Parser selection follows this flow:

```
Message
  ↓
Classifier
  ↓
ClassificationResult(bank, notification_type)
  ↓
ParserRegistry.resolve(...)
  ↓
Parser
```

Each `(Bank, NotificationType)` combination must map to **exactly one parser**.

---

## Rationale

### Deterministic parser resolution

The registry guarantees deterministic behavior.

Given a classification `(Bank, NotificationType)`, the system will always resolve the same parser.

This avoids ambiguity or reliance on evaluation order.

---

### Separation between classification and parsing

The system intentionally separates two responsibilities:

**Classification**

Determining which bank and notification type correspond to a message.

**Parsing**

Extracting structured information from the message.

This separation keeps parsers focused on extraction logic and avoids duplicating classification logic inside parser implementations.

---

### Parser identity via metadata

Each parser declares its identity using class attributes:

```python
class BacTransactionNotificationParser(BaseParser):

    bank = Bank.BAC
    notification_type = NotificationType.TRANSACTION_NOTIFICATION
```

The registry can register parsers using this metadata:

```python
registry.register_parser(BacTransactionNotificationParser())
```

Internally, the registry builds the key:

```
(parser.bank, parser.notification_type)
```

This prevents duplication of configuration between the parser implementation and the registry.

---

### Explicit initialization of available parsers

Available parsers are declared explicitly in the composition root or in a dedicated registry module.

Example:

```python
def build_parser_registry() -> ParserRegistry:
    registry = ParserRegistry()

    registry.register_parser(BacTransactionNotificationParser())
    registry.register_parser(BacDebitNotificationParser())

    return registry
```

This ensures that all active parsers remain visible in system configuration.

---

### Defensive validation through `can_parse()`

The base parser may expose a method such as:

```python
def can_parse(message: RawMessage) -> bool
```

This method **is not used for parser selection**.

Instead, it serves as:

- a defensive validation
- an internal parser check
- a useful testing tool
- protection against classification errors

Parser selection remains the responsibility of the `ParserRegistry`.

---

## Consequences

### Benefits

- simple and deterministic parser selection
- clear separation between classification and parsing
- small and maintainable registry
- explicit visibility of available parsers
- predictable system behavior

---

### Costs

- the registry must be updated when adding new parsers
- developers must maintain consistency between parsers and registry entries

Given the expected system size (~15 parsers), these costs are considered minimal.

---

## Alternatives Considered

### Parser auto-discovery

An alternative would be scanning parser modules and automatically registering parser classes using decorators, metaclasses, or module introspection.

Conceptual workflow:

```
scan parsers/*
↓
import modules
↓
auto-register parsers
```

#### Advantages

- less manual work when adding new parsers
- automatic extensibility

#### Disadvantages

- dependence on import side effects
- harder debugging
- active parsers may depend on import order
- reduced visibility of system components
- unnecessary complexity

Given the relatively small expected number of parsers (~15), the benefit does not justify the additional complexity.

This option was rejected.

---

### Chain of Responsibility

Another possibility would be allowing each parser to implement:

```python
can_parse(message)
```

and sequentially evaluating parsers until one accepts the message.

Conceptual flow:

```
for parser in parsers:
    if parser.can_parse(message):
        return parser
```

#### Advantages

- parsers encapsulate their own recognition logic
- flexible in ambiguous cases

#### Disadvantages

- duplicates classification logic inside parsers
- evaluation order becomes significant
- system behavior becomes less predictable
- weaker architectural separation

Because the system already includes an explicit **classification stage**, this approach would introduce unnecessary redundancy.

This option was rejected.

---

## References

Alistair Cockburn — _Hexagonal Architecture_

Martin Fowler — _Patterns of Enterprise Application Architecture_

Eric Evans — _Domain-Driven Design_

---

## Status

This decision is **accepted** for the current version of the system.

If the number of parsers grows significantly in the future or if a plugin-based architecture becomes necessary, an automatic discovery mechanism may be reconsidered in a new ADR.
