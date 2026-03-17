# ADR-0001: System Architecture for `bank_ingest`

**Status:** Accepted
**Date:** 2026-03-16
**Author:** `bank_ingest` Project

---

## Context

The `bank_ingest` project aims to automate the ingestion, classification, and processing of banking notification emails in order to extract structured financial events that can later be analyzed.

Currently, this process is performed manually. The automated system must:

1. Read Gmail messages labeled **"Transacciones"**.
2. Classify and parse bank notifications.
3. Extract structured information about financial events.
4. Persist the events in a local database.
5. Update Gmail labels according to the processing result.

This project also has an explicit pedagogical objective: **to practice software architecture approaches used in industrial environments**, specifically domain-oriented and hexagonal architectures.

For this reason, a formal architecture has been adopted from the beginning, even though for a minimal v1 it might be considered overengineering.

---

## Decision

The system will be implemented using a **Hexagonal Architecture (Ports and Adapters)** combined with principles from **Domain-Driven Design (DDD)** and **Clean Architecture**.

The main architectural decisions are the following.

---

## 1. Strict separation between domain and infrastructure

The system is organized into the following layers:

- **Domain**
- **Application**
- **Adapters**
- **Shared**

The domain must never depend on:

- Gmail API
- SQLAlchemy
- filesystem
- CLI
- Google Sheets
- external frameworks

Dependencies must always point **toward the domain**, never from the domain outward.

---

## 2. Use of ports and adapters

The domain and application layers define **ports** (abstract interfaces).

Adapters implement those ports for specific technologies.

Examples of ports:

- `MessageSourcePort`
- `EventRepositoryPort`
- `MessageStorePort`
- `ProcessingStatePort`

Examples of adapters:

- Gmail API adapter
- SQLAlchemy repository
- Filesystem storage
- Google Sheets exporter

This pattern allows infrastructure to be replaced without modifying the domain.

---

## 3. Code organization

The project structure is:

```
src/bank_ingest/
├── domain
├── application
├── adapters
└── shared
```

### Domain

Defines the problem model.

Contains:

- entities
- value objects
- enums
- domain services
- domain exceptions
- ports

The domain describes **what the system is**, not **how it technically works**.

---

### Application

Defines the **use cases**.

It orchestrates the processing pipeline:

1. retrieve messages
2. classify them
3. parse them
4. persist events
5. update message state

The application layer depends on the domain and on the ports defined within it.

It does not depend directly on Gmail or SQL.

---

### Adapters

Contains concrete implementations of ports.

It is divided into:

**Inbound adapters**

- CLI
- scheduled tasks

**Outbound adapters**

- Gmail API
- bank-specific parsers
- SQLAlchemy persistence
- filesystem storage
- external exporters

Adapters translate between:

- external models
- domain models

---

### Shared

Reusable technical utilities that do not belong to the domain.

Examples:

- date parsing
- monetary operations
- hashing
- text cleaning

This module must remain small to avoid becoming a “miscellaneous utilities” dumping ground.

---

## 4. Extensible parser system

The system must support multiple banks and multiple notification types.

The strategy is:

```
parser/
 ├── base.py
 └── bac/
     ├── classifier.py
     └── transaction_notification.py
```

Each bank has its own module.

Each notification type has its own parser.

This avoids monolithic files as the system grows.

---

## 5. Data source: Gmail

Messages are retrieved through the **Gmail API**.

Only emails with the label:

```
Transacciones
```

are processed.

The system updates labels according to the processing result:

| Result  | Action             |
| ------- | ------------------ |
| success | add label `parsed` |
| error   | add label `error`  |

Messages that fail processing remain **unread** so they can be easily reviewed manually.

---

## 6. Persistence

Initial persistence will be implemented using:

**SQLite + SQLAlchemy**

Motivations:

- simple deployment
- local database
- sufficient for expected volume
- easy backups

The system could later migrate to PostgreSQL without modifying the domain.

---

## 7. Local artifact storage (`data/`)

The system maintains a `data/` directory for processing artifacts.

This serves purposes such as:

- debugging
- auditing
- reproducibility
- parser development

Structure:

```
data/
├── db
├── raw_messages
├── rendered
├── parsed
└── errors
```

### raw_messages

Original downloaded emails.

Allows messages to be reprocessed if parsers change.

---

### rendered

Intermediate representation of the message.

Example:

- cleaned text extracted from HTML

---

### parsed

Structured parser output.

---

### errors

Artifacts associated with parsing failures.

They include:

- the original message
- the error reason
- relevant message fragments

---

## 8. Configurable storage policy

Artifact storage will be controlled through **configuration flags**.

Examples:

```
STORE_RAW_MESSAGES=true
STORE_RENDERED_MESSAGES=true
STORE_PARSED_OUTPUT=true
STORE_ERROR_ARTIFACTS=true
```

This allows behavior changes without modifying code.

The strategy is inspired by **feature toggles**.

---

## 9. Credential security

Access to Gmail uses **OAuth2**.

The system never stores passwords.

Two files are used:

```
credentials.json
token.json
```

These files:

- are not versioned
- have restrictive permissions
- can be revoked from the Google account

---

## 10. Observability

The system provides two forms of observability.

### Logs

Directory:

```
logs/
```

Contains system execution events.

---

### Operational artifacts

Directory:

```
data/
```

Contains processing data useful for auditing.

---

## Consequences

### Benefits

- scalable architecture
- domain independence
- easy addition of new banks
- easy persistence replacement
- easier parser debugging
- processing traceability

Additionally, this architecture allows practicing principles used in real enterprise systems.

---

### Costs

- higher initial complexity
- more files and layers
- stronger discipline required to maintain proper separation

For a small project this could be considered overengineering, but it is accepted as a deliberate decision for educational and architectural quality purposes.

---

## Alternatives considered

### Simple monolithic architecture

A simpler structure could have been:

```
src/
 parser/
 gmail/
 db/
 main.py
```

This option was rejected because it:

- mixes domain logic with infrastructure
- makes scaling to multiple banks harder
- complicates testing
- reduces the educational value of the project

---

## References

Alistair Cockburn — _Hexagonal Architecture (Ports and Adapters)_
[https://alistair.cockburn.us/hexagonal-architecture](https://alistair.cockburn.us/hexagonal-architecture)

Eric Evans — _Domain-Driven Design_

Martin Fowler — _Patterns of Enterprise Application Architecture_

Robert C. Martin — _Clean Architecture_

Martin Fowler — _Feature Toggles_
[https://martinfowler.com/articles/feature-toggles.html](https://martinfowler.com/articles/feature-toggles.html)

---

## Status

This architecture is considered **accepted** for the initial version of the system.

Future changes must be recorded through new ADRs.
