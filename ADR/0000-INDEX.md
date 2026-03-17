---
adr: 0000
title: "ADR Index"
status: Accepted
date: 2026-03-16
authors:
  - bank_ingest Project
reviewers: []
tags:
  - adr-governance
  - documentation
  - architecture
decision_scope: system
supersedes: null
superseded_by: null
related_adrs: []
---

## Context

The `bank_ingest` project uses **Architectural Decision Records (ADR)** to document
important architectural and design decisions.

As the number of ADRs grows, it becomes necessary to provide a **single index
document** that allows developers and AI coding agents to quickly locate and
navigate the architectural decisions that define the system.

This document serves as the **entry point to the ADR collection**.

---

## Decision

All architectural decisions for this project are stored in the directory:

```

ADR/

```

Each ADR follows the numbering convention:

```

XXXX-topic-name.md

```

Where:

- `XXXX` is a **zero-padded sequential identifier**
- `topic-name` is a short descriptive slug

Example:

```

0004-parser-strategy.md

```

The ADR index provides a **centralized list of all decisions**, grouped in a
logical order that roughly follows the system architecture.

---

## ADR List

### Foundational Decisions

| ADR  | Title                                 | Scope  | Status   |
| ---- | ------------------------------------- | ------ | -------- |
| 0000 | Project Structure                     | system | Accepted |
| 0001 | System Architecture for `bank_ingest` | system | Accepted |

These ADRs define the **overall architectural structure** of the project.

---

### Infrastructure & Integration

| ADR  | Title                                 | Scope     | Status   |
| ---- | ------------------------------------- | --------- | -------- |
| 0002 | Gmail as the Message Ingestion Source | component | Accepted |
| 0003 | Local Storage Policy (`data/`)        | system    | Accepted |

These ADRs define how the system interacts with **external services and local storage**.

---

### Message Processing Pipeline

| ADR  | Title                                  | Scope     | Status   |
| ---- | -------------------------------------- | --------- | -------- |
| 0004 | Parser Strategy for Bank Notifications | module    | Accepted |
| 0006 | Parser Selection Strategy              | module    | Accepted |
| 0007 | Design of the ProcessingStatePort      | component | Accepted |

These ADRs define the **core message processing architecture**.

---

### Application Wiring

| ADR  | Title                                       | Scope  | Status   |
| ---- | ------------------------------------------- | ------ | -------- |
| 0005 | Bootstrap and Dependency Injection Strategy | system | Accepted |

This ADR defines how the system components are wired together at runtime.

---

## Reading Order

For developers new to the project, the recommended reading order is:

```

0000  Project Structure
0001  System Architecture
0003  Storage Policy
0002  Gmail Ingestion Source
0004  Parser Strategy
0006  Parser Registry
0007  Processing State Port
0005  Bootstrap / Dependency Injection

```

This order follows the conceptual layering of the system:

```

Repository structure
↓
System architecture
↓
Infrastructure decisions
↓
Processing pipeline
↓
Runtime wiring

```

---

## ADR Lifecycle

Each ADR progresses through the following lifecycle states:

| Status     | Meaning                     |
| ---------- | --------------------------- |
| Proposed   | Decision under discussion   |
| Accepted   | Decision currently in force |
| Superseded | Replaced by another ADR     |
| Deprecated | No longer relevant          |

When an ADR is replaced, the following fields must be updated:

```

superseded_by
supersedes

```

This ensures traceability of architectural evolution.

---

## Guidelines for New ADRs

When creating a new ADR:

1. Copy the template:

```

ADR/0000-TEMPLATE.md

```

1. Assign the next sequential identifier.

Example:

```

0008-new-decision.md

```

1. Fill all metadata fields.

2. Update this **ADR index**.

---

## Purpose of ADRs in This Project

ADR documentation is used to:

- maintain architectural clarity
- document design rationale
- support onboarding of developers
- guide AI coding agents working in the repository
- preserve the historical evolution of system architecture

The ADR collection represents the **authoritative description of the system architecture**.

---

## References

Michael Nygard — _Architectural Decision Records_

<https://adr.github.io/>

Martin Fowler — _Documenting Architecture Decisions_

<https://martinfowler.com/articles/architecture-decision-records.html>

---

## Status

This ADR index is **accepted** as the navigation entry point for the ADR collection.

---

## Change Log

| Date       | Change            |
| ---------- | ----------------- |
| 2026-03-16 | Initial ADR index |
