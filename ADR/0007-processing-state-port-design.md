---
adr: 0007
title: Design of the ProcessingStatePort
status: Accepted
date: 2026-03-16
author:
  - "`bank_ingest` Project"
reviewers: []
tags:
  - outbound-port
  - message-processing
  - state-management
  - infrastructure-abstraction
decision_scope: component
supersedes: null
superseded_by: null
related_adrs: []
---

## Context

The `bank_ingest` system processes bank notification emails retrieved from Gmail.

Once a message has been processed, the system must update its **processing state** in order to:

- prevent duplicate processing
- provide observability of the processing pipeline

In Gmail, this state is represented through **labels** applied to the message, for example:

- `parsed`
- `error`

These labels allow the system to distinguish between messages that have already been processed and those that are still pending or that failed during processing.

However, within a **hexagonal architecture**, the domain and application layers must not depend on infrastructure-specific concepts such as Gmail labels.

Therefore, the system requires an **outbound port** that allows expressing the processing state without coupling the system to Gmail’s labeling semantics.

This port is called:

```id="p0lmb7"
ProcessingStatePort
```

---

## Decision

The `ProcessingStatePort` will expose **operations oriented around processing outcomes**, rather than generic label manipulation operations.

The minimal contract of the port will be:

```python id="nfdh1u"
class ProcessingStatePort(Protocol):

    def mark_processed(self, message_id: MessageId) -> None:
        ...

    def mark_failed(self, message_id: MessageId, reason: str | None = None) -> None:
        ...

    def mark_skipped(self, message_id: MessageId, reason: str | None = None) -> None:
        ...
```

This interface expresses **state transitions in the processing pipeline**, rather than low-level label operations.

The Gmail adapter will translate these operations into label updates in Gmail.

---

## Rationale

### Separation between domain logic and infrastructure

The domain and application layers should express **business intent**, not the mechanics of an external API.

Exposing operations such as:

```id="odv1jq"
add_label
remove_label
set_labels
```

would introduce Gmail-specific semantics into the port interface.

This would violate the architectural boundary between application and infrastructure.

Instead, operations such as:

```id="y2j7pl"
mark_processed
mark_failed
```

express the natural language of the processing pipeline.

---

### Clear semantic representation of pipeline states

The system recognizes three primary outcomes for a message:

1. **Processed**
   The message was successfully parsed and produced a valid financial event.

2. **Failed**
   An error occurred during parsing or processing.

3. **Skipped**
   The message does not correspond to a supported notification type or should not be processed.

These categories clearly represent the logical states of the pipeline.

---

### Handling partial failures

A possible scenario is:

```id="i8igw3"
message parsed successfully
↓
event persisted
↓
failure while updating Gmail labels
```

This situation represents an **external synchronization failure**, not a failure of the business process.

Therefore:

- the persisted event **must not be rolled back**
- the incident should be logged
- the error should be observable through logs or diagnostic artifacts

This prevents the system’s internal consistency from depending on the availability of Gmail.

Updating the processing state should therefore be treated as a **post-processing operation**.

Conceptual example:

```python id="j6g5dz"
event_repository.save(event)

try:
    processing_state.mark_processed(message.id)
except Exception:
    logger.error("Failed to update processing state")
```

This approach ensures the system remains internally consistent even if Gmail temporarily fails.

---

## Consequences

### Benefits

- strong decoupling between the domain and Gmail
- a port interface aligned with the language of the processing pipeline
- improved semantic clarity in the application layer
- easier testing through fake adapters
- full encapsulation of infrastructure details

---

### Costs

- reduced flexibility if more complex label operations are required
- potential need to extend the port if new processing states appear in the future

These costs are considered acceptable for the current version of the system.

---

## Alternatives Considered

### Label-based port

One alternative would expose generic operations such as:

```id="3f3rmt"
add_label(label)
remove_label(label)
```

#### Advantages

- maximum flexibility
- direct alignment with Gmail functionality

#### Disadvantages

- introduces Gmail-specific semantics into the port interface
- couples the application layer to infrastructure
- weakens the domain language

This option was rejected.

---

### Generic tag abstraction

Another alternative was exposing a generic tag interface:

```id="g5sikc"
add_tag("processed")
add_tag("error")
```

#### Advantages

- decouples from Gmail-specific terminology

#### Disadvantages

- introduces an unnecessarily generic abstraction
- does not clearly express the pipeline states
- complicates the conceptual model without meaningful benefit

This option was rejected.

---

## References

Alistair Cockburn — _Hexagonal Architecture (Ports and Adapters)_

Eric Evans — _Domain-Driven Design_

Robert C. Martin — _Clean Architecture_

---

## Status

This decision is **accepted** for the current version of the system.

If the system later requires more complex synchronization with external providers or additional processing states, the port interface may be extended through a new ADR.
