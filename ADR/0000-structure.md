---
adr: 0000
title: "Project structure"
status: Accepted
date: 2026-03-16
authors:
  - "Luis Fernando Umaña Castro"
reviewers: []
tags:
  - project-structure
  - repository-design
  - architecture
  - conventions
decision_scope: system
supersedes: null
superseded_by: null
related_adrs: []
---

## Project structure

```
bank_ingest/
├── .gitignore
├── ADR/
│   ├── 0000-structure.md
│   ├── 0001-architecture.md
│   ├── 0002-gmail-as-source.md
│   ├── 0003-storage-policy.md
│   ├── 0004-parser-strategy.md
│   ├── 0005-bootstrap.md
│   ├── 0006-parser-registry.md
│   └── 0007-processing-state-port-design.md
├── CLAUDE.md
├── data/
│   ├── db/
│   ├── errors/
│   ├── parsed/
│   ├── raw_messages/
│   └── rendered/
├── logs/
├── pyproject.toml
├── README.md
├── src/
│   └── bank_ingest/
│       ├── __init__.py
│       ├── bootstrap.py
│       ├── cli.py
│       ├── config.py
│       ├── adapters/
│       │   ├── __init__.py
│       │   ├── inbound/
│       │   │   ├── __init__.py
│       │   │   └── cli/
│       │   │       ├── __init__.py
│       │   │       └── commands.py
│       │   └── outbound/
│       │       ├── __init__.py
│       │       ├── gmail/
│       │       │   ├── __init__.py
│       │       │   ├── auth.py
│       │       │   ├── client.py
│       │       │   ├── labels.py
│       │       │   └── mapper.py
│       │       ├── observability/
│       │       │   ├── __init__.py
│       │       │   └── logger_adapter.py
│       │       ├── parser/
│       │       │   ├── __init__.py
│       │       │   ├── base.py
│       │       │   ├── registry.py
│       │       │   └── bac/
│       │       │       ├── __init__.py
│       │       │       ├── classifier.py
│       │       │       ├── patterns.py
│       │       │       └── transaction_notification.py
│       │       ├── persistence/
│       │       │   ├── __init__.py
│       │       │   ├── sqlalchemy/
│       │       │   │   ├── __init__.py
│       │       │   │   ├── base.py
│       │       │   │   ├── models.py
│       │       │   │   ├── repository.py
│       │       │   │   └── uow.py
│       │       │   └── sqlite/
│       │       │       ├── __init__.py
│       │       │       └── engine.py
│       │       └── storage/
│       │           ├── __init__.py
│       │           ├── filesystem_error_store.py
│       │           ├── filesystem_parsed_store.py
│       │           ├── filesystem_raw_store.py
│       │           └── filesystem_rendered_store.py
│       ├── application/
│       │   ├── __init__.py
│       │   ├── commands.py
│       │   ├── dtos.py
│       │   ├── policies/
│       │   │   ├── __init__.py
│       │   │   ├── error_policy.py
│       │   │   └── storage_policy.py
│       │   └── use_cases/
│       │       ├── __init__.py
│       │       ├── classify_message.py
│       │       ├── fetch_labeled_messages.py
│       │       ├── parse_message.py
│       │       ├── persist_event.py
│       │       └── process_inbox_batch.py
│       ├── domain/
│       │   ├── __init__.py
│       │   ├── entities.py
│       │   ├── enums.py
│       │   ├── exceptions.py
│       │   ├── services.py
│       │   ├── value_objects.py
│       │   └── ports/
│       │       ├── __init__.py
│       │       ├── event_repository.py
│       │       ├── logger.py
│       │       ├── message_source.py
│       │       ├── message_store.py
│       │       └── processing_state.py
│       └── shared/
│           ├── __init__.py
│           ├── datetime.py
│           ├── hashing.py
│           ├── money.py
│           └── text.py
└── tests/
    ├── conftest.py
    ├── fixtures/
    ├── integration/
    │   ├── gmail/
    │   ├── persistence/
    │   └── storage/
    └── unit/
        ├── adapters/
        ├── application/
        └── domain/
```
