# ADR-0002: Gmail as the Message Ingestion Source

**Status:** Accepted
**Date:** 2026-03-16
**Author:** `bank_ingest` Project

---

## Context

The `bank_ingest` system requires a reliable source from which to retrieve bank notification emails. Currently, these notifications are delivered to a **Gmail** account, and the user already organizes them using Gmail filters and labels.

The current manual workflow is:

1. Banks send transaction notification emails.
2. Gmail automatically applies filters.
3. Relevant messages receive the label **`Transacciones`**.
4. The user manually reviews these messages and extracts the relevant information.

The system should automate the ingestion of these messages in order to:

- identify relevant banking notifications
- extract structured financial information
- record financial events in a database
- maintain traceability of message processing

Two main alternatives were considered for retrieving messages from Gmail:

1. **IMAP**
2. **Gmail API**

---

## Decision

The system will use the **Gmail API** as the official mechanism for retrieving messages.

Only messages that have the label:

```
Transacciones
```

will be processed.

The system will update the processing state of each message using additional labels depending on the outcome of processing.

| Result  | Action             |
| ------- | ------------------ |
| success | add label `parsed` |
| error   | add label `error`  |

Messages that result in an error will remain **unread**, making them easier to identify and review manually in the Gmail interface.

---

## Rationale

### Native integration with Gmail’s labeling model

Unlike traditional email systems that rely on folders, Gmail uses a **label-based model**, where a single message can have multiple labels simultaneously.

The Gmail API allows the system to interact directly with this model by enabling:

- querying messages by label
- adding or removing labels
- updating read/unread status
- retrieving message metadata and full content

IMAP exposes Gmail labels as folders, which introduces ambiguity and can lead to duplicated messages.

---

### Clear and observable processing state

The system uses labels to represent the processing status of each message.

Defined states:

| State     | Label           |
| --------- | --------------- |
| pending   | `Transacciones` |
| processed | `parsed`        |
| error     | `error`         |

This approach allows the processing state to be observed directly in Gmail without relying on the internal database.

---

### Reduced risk of duplicate processing

Each Gmail message contains unique identifiers:

```
message_id
thread_id
```

These identifiers allow the system to:

- prevent duplicate processing
- maintain traceability of message origins
- associate financial events with their source message

IMAP may produce duplicates when a message has multiple labels.

---

### Secure authentication via OAuth2

Access to Gmail is implemented through **OAuth2**, which provides several security benefits:

- the system does not store user passwords
- the user explicitly authorizes access
- tokens can be revoked at any time

The system uses two credential files:

```
credentials.json
token.json
```

These files contain:

- `client_id`
- `client_secret`
- `access_token`
- `refresh_token`

User passwords are never stored.

---

### Compatibility with the hexagonal architecture

The Gmail integration is implemented as an **outbound adapter** that satisfies the port:

```
MessageSourcePort
```

This ensures that the domain and application layers remain independent from Gmail.

If a different message source were required in the future (for example IMAP, Exchange, or local files), it would only require implementing another adapter for the same port.

---

## Ingestion Model

The system periodically queries Gmail for messages labeled:

```
Transacciones
```

The query excludes messages that have already been processed.

Conceptual query:

```
label:Transacciones -label:parsed
```

For each message, the system retrieves:

- message metadata
- plain text body
- HTML body
- relevant headers
- snippet

These elements are converted into an internal domain representation called:

```
SourceMessage
```

---

## Processing Flow

The ingestion pipeline follows these steps:

1. query Gmail for messages labeled `Transacciones`
2. exclude messages already labeled `parsed`
3. download message contents
4. convert the message into a `SourceMessage`
5. store artifacts in `data/raw_messages`
6. classify the message
7. run the corresponding parser
8. persist the financial event
9. update message labels in Gmail

### Success

```
+ parsed
```

### Error

```
+ error
```

Messages with errors remain **unread**.

---

## Gmail Adapter Location

Within the project, the Gmail adapter is located at:

```
src/bank_ingest/adapters/outbound/gmail
```

Key modules include:

```
auth.py
client.py
mapper.py
labels.py
```

Responsibilities:

| File        | Responsibility                           |
| ----------- | ---------------------------------------- |
| `auth.py`   | OAuth authentication                     |
| `client.py` | communication with Gmail API             |
| `mapper.py` | mapping Gmail messages → `SourceMessage` |
| `labels.py` | operations related to labels             |

---

## Observability

The system provides observability at two levels.

### Gmail interface

Users can directly observe:

- pending messages
- processed messages
- messages with errors

from the Gmail UI.

---

### Local system artifacts

The system stores ingestion artifacts in:

```
data/raw_messages
data/rendered
data/parsed
data/errors
```

These artifacts allow developers to debug the system if the format of bank emails changes.

---

## Consequences

### Benefits

- natural integration with Gmail
- processing state visible from the email client
- fine-grained control over labels
- reduced risk of duplicates
- OAuth2-based security
- alignment with the hexagonal architecture

---

### Costs

- dependency on Gmail API
- initial OAuth2 configuration required
- slightly more complexity compared to simple IMAP access

---

## Alternatives Considered

### IMAP

IMAP was considered as an alternative.

**Advantages**

- standard protocol
- compatible with many providers

**Disadvantages**

- ambiguous handling of Gmail labels
- potential message duplication
- limited metadata support
- difficulty managing labels

For these reasons, the Gmail API was selected.

---

## References

Google Gmail API Documentation
[https://developers.google.com/gmail/api](https://developers.google.com/gmail/api)

Alistair Cockburn — _Hexagonal Architecture_
[https://alistair.cockburn.us/hexagonal-architecture](https://alistair.cockburn.us/hexagonal-architecture)

OAuth2 Authorization Framework
RFC 6749

---

## Status

This decision is **accepted** for the initial version of the system.
