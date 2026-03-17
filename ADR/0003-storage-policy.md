---
adr: 0003
title: "Local Storage Policy (`data/`)"
status: Accepted
date: 2026-03-16
author: "`bank_ingest` Project"
reviewers: []
tags:
  - storage
  - observability
  - data-retention
  - debugging
decision_scope: system
supersedes: null
superseded_by: null
related_adrs: []
---

## Context

The `bank_ingest` system processes email notifications sent by banks that contain financial transaction information.

During both development and operation, it must be possible to:

- debug parsing failures
- audit extracted financial events
- reprocess messages if parsers change
- investigate changes in email formats sent by banks

A common strategy in data ingestion systems is to store **intermediate pipeline artifacts** to improve observability and reproducibility.

However, indiscriminately storing these artifacts also introduces potential drawbacks:

- increased disk usage
- potential exposure of sensitive financial data
- unnecessary operational complexity in production

For this reason, the system requires an explicit **artifact storage policy** governing what data is stored during processing.

---

## Decision

The system will maintain a structured directory named:

```
data/
```

This directory stores operational artifacts generated during the ingestion pipeline.

The defined structure is:

```
data/
├── db/
├── raw_messages/
├── rendered/
├── parsed/
└── errors/
```

Each subdirectory corresponds to a specific stage of the processing pipeline.

The persistence of each artifact type will be **configurable through runtime configuration flags**.

---

## Directory Description

### `data/db`

Stores the local database used by the system.

The initial implementation uses:

```
SQLite
```

Motivations:

- simple deployment
- self-contained database
- easy backups
- low expected data volume

The main database file will resemble:

```
data/db/bank_ingest.sqlite
```

---

### `data/raw_messages`

Stores copies of the original messages retrieved from Gmail.

Typical formats include:

```
.eml
.json
```

These artifacts may contain:

- full message headers
- HTML body
- plain text body
- Gmail metadata
- message identifiers

This storage enables:

- reprocessing messages if parsers evolve
- analyzing changes in email formats
- auditing the origin of financial events

---

### `data/rendered`

Stores intermediate representations of the message prepared for parsing.

Examples include:

- cleaned text extracted from HTML
- normalized message content
- simplified structures of relevant fields

This intermediate stage helps:

- debug parsing logic
- isolate text extraction issues
- support incremental parser development

---

### `data/parsed`

Stores the structured output produced by the parser, either before or after persistence in the database.

Example:

```json
{
  "bank": "BAC",
  "event_type": "card_transaction",
  "merchant": "AMPM",
  "amount": 12000,
  "currency": "CRC",
  "card_last4": "1234",
  "authorization": "A82F3D",
  "transaction_date": "2026-03-15"
}
```

These artifacts allow developers to:

- quickly inspect parsing results
- validate parser behavior during development
- reproduce reported errors

---

### `data/errors`

Stores diagnostic information about messages that could not be processed successfully.

Each error artifact should include:

- the message identifier
- the error reason
- relevant excerpts from the message
- debugging context

Example:

```json
{
  "message_id": "...",
  "error": "missing_authorization_code",
  "parser": "bac.transaction_notification",
  "excerpt": "...relevant text..."
}
```

These artifacts facilitate diagnosing parsing issues or identifying format changes in bank notifications.

---

## Internal Organization

Within each directory, files should be organized by date to simplify inspection and retention management.

Example:

```
raw_messages/
└── 2026/
    └── 03/
        └── 16/
```

Benefits include:

- easier identification of processing dates
- simplified deletion of old data
- improved support for temporal audits

---

## Configuration Policy

Artifact persistence is controlled through configuration flags.

Examples:

```
STORE_RAW_MESSAGES=true
STORE_RENDERED_MESSAGES=true
STORE_PARSED_OUTPUT=true
STORE_ERROR_ARTIFACTS=true
```

These flags allow the system to adapt behavior depending on the environment.

### Development environment

```
STORE_RAW_MESSAGES=true
STORE_RENDERED_MESSAGES=true
STORE_PARSED_OUTPUT=true
STORE_ERROR_ARTIFACTS=true
```

### Minimal production environment

```
STORE_RAW_MESSAGES=true
STORE_RENDERED_MESSAGES=false
STORE_PARSED_OUTPUT=false
STORE_ERROR_ARTIFACTS=true
```

---

## Security Considerations

The `data/` directory may contain sensitive financial information.

For this reason, the following practices are required:

- the `data/` directory **must not be committed to version control**
- filesystem access should be restricted to authorized users
- restrictive filesystem permissions should be enforced
- backups must be properly protected

---

## Data Retention

The initial retention policy is conservative to facilitate development and debugging.

Suggested defaults:

| Artifact     | Suggested retention |
| ------------ | ------------------- |
| raw_messages | 90 days             |
| rendered     | 30 days             |
| parsed       | 30 days             |
| errors       | 180 days            |

Automated rotation and cleanup policies may be defined in future ADRs.

---

## Relationship to the Hexagonal Architecture

Storage in `data/` is implemented through **storage adapters** located in:

```
src/bank_ingest/adapters/outbound/storage
```

These adapters implement ports defined in the domain layer.

This ensures that the domain remains independent from filesystem details.

---

## Consequences

### Benefits

- improved parser debugging
- traceability of financial events
- ability to reprocess messages
- improved pipeline observability
- support for auditing

---

### Costs

- increased disk usage
- need for retention management
- potential exposure of sensitive data if not properly secured

These costs are considered acceptable given the benefits for development and system observability.

---

## Alternatives Considered

### No artifact storage

One alternative would be to store no intermediate artifacts and rely exclusively on the database.

This option was rejected because it would:

- make parser debugging significantly harder
- prevent message reprocessing
- reduce pipeline observability
- complicate auditing

---

## References

Martin Fowler — _Feature Toggles_
[https://martinfowler.com/articles/feature-toggles.html](https://martinfowler.com/articles/feature-toggles.html)

Alistair Cockburn — _Hexagonal Architecture_
[https://alistair.cockburn.us/hexagonal-architecture](https://alistair.cockburn.us/hexagonal-architecture)

---

## Status

This storage policy is **accepted** for the initial version of the system.
