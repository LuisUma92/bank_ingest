# ADR-0005: Bootstrap and Dependency Injection Strategy

**Status:** Accepted
**Date:** 2026-03-16
**Author:** `bank_ingest` Project

---

## Context

The `bank_ingest` system follows a **hexagonal architecture**, where the domain and application layers define ports, and concrete adapters implement those contracts for external technologies such as the Gmail API, SQLAlchemy, and filesystem storage.

The orchestration of the main processing pipeline occurs in the **application layer**, while infrastructure concerns remain outside the domain.

In the initial version of the system, approximately **15 components** must be wired together, including:

- message source adapters
- persistence adapters
- artifact storage adapters
- message processing state adapters
- parser registries or resolvers
- application use cases

The system therefore requires a clear strategy for **bootstrapping and dependency injection** that remains consistent with the architectural principles of the project.

Three alternatives were considered:

1. **Manual constructor injection** using a `create_app()` function that instantiates and wires all components.
2. A **lightweight DI container**, using a library such as `dependency-injector`.
3. A **global registry pattern**, using dictionaries or shared singletons to resolve dependencies.

Because the project also has a pedagogical objective—learning architecture practices commonly used in industrial software systems—the chosen approach should prioritize **clarity, traceability, and architectural discipline**.

---

## Decision

The system will use **manual constructor injection** within a single **composition root**, located at:

```id="zpq42q"
src/bank_ingest/bootstrap.py
```

This module will expose a function similar to:

```python id="k0io66"
create_app()
```

This function is responsible for:

1. loading configuration
2. constructing technical clients
3. instantiating concrete adapters
4. instantiating services and use cases
5. wiring dependencies between ports and adapters
6. returning the application container or the final composition required by the entrypoint

At this stage:

- **no external DI container will be used**
- **no global dependency registries or service locators are allowed**
- **no hidden singletons accessible via imports**

---

## Rationale

### Explicit visibility of the dependency graph

In small to medium systems, manual wiring makes the dependency graph **fully explicit**.

This is particularly valuable in hexagonal architectures, where maintaining the correct dependency direction is essential:

dependencies must point **toward the domain**, never outward from it.

An explicit `bootstrap.py` provides a single place where it is possible to see:

- which ports exist
- which adapters implement them
- which use cases depend on which ports
- which technical components are shared

---

### Alignment with the pedagogical goals of the project

The project intentionally adopts a formal architecture—even if heavier than strictly necessary for a v1—because one of its goals is to practice **software architecture patterns used in production systems**.

Manual wiring forces the developer to understand the system explicitly:

- where the application layer ends
- where infrastructure begins
- which dependency belongs to which layer
- which adapter satisfies each port

A DI container would obscure part of this understanding behind providers or automatic resolution.

---

### Reduced accidental complexity in the initial version

With approximately **15 components** to wire, introducing a DI container would add an additional conceptual layer without delivering proportional benefits.

At this stage, the main challenge is **maintaining architectural clarity**, not managing a complex dependency graph.

Manual constructor injection solves this problem with minimal additional complexity.

---

### Improved testability without hidden mechanisms

When dependencies are injected through constructors and the composition root is isolated in `bootstrap.py`, tests can instantiate use cases directly with **fakes, stubs, or test adapters**.

This avoids problems such as:

- shared global state
- hidden container dependencies
- implicit runtime resolution
- difficulty isolating unit tests

---

### Avoiding a disguised service locator

The global registry approach was rejected because it introduces **implicit global state** and hides the origin of dependencies.

This weakens architectural discipline and complicates:

- reasoning about the system
- debugging
- testing
- safe refactoring

---

## Implementation Approach

The composition root should remain concentrated in a single module.

Conceptual example:

```python id="5fg3q1"
def create_app(settings: Settings) -> AppContainer:
    gmail_client = GmailClient(...)
    message_source = GmailMessageSourceAdapter(gmail_client)
    processing_state = GmailProcessingStateAdapter(gmail_client)

    engine = build_engine(settings.database_url)
    event_repository = SqlAlchemyEventRepository(engine)

    raw_store = FileSystemRawMessageStore(...)
    rendered_store = FileSystemRenderedStore(...)
    parsed_store = FileSystemParsedStore(...)
    error_store = FileSystemErrorStore(...)

    parser_registry = build_parser_registry()

    process_messages = ProcessMessagesUseCase(
        message_source=message_source,
        processing_state=processing_state,
        event_repository=event_repository,
        parser_registry=parser_registry,
        raw_store=raw_store,
        rendered_store=rendered_store,
        parsed_store=parsed_store,
        error_store=error_store,
    )

    return AppContainer(
        process_messages=process_messages,
    )
```

The exact structure may evolve as the project grows.

---

## Criteria for Migrating to a DI Container

The current decision **does not prohibit** the future adoption of a dependency injection container.

Manual constructor injection is adopted as the **initial strategy**, and the following review criteria are defined.

Migration to a DI container should be reconsidered if **two or more** of the following conditions occur:

1. Multiple entrypoints require different wiring configurations
   (e.g., CLI, scheduler, worker processes, HTTP API, backfill scripts).

2. Significant wiring duplication appears across entrypoints.

3. Environment configuration becomes highly conditional
   (e.g., different adapters for dev, test, and production environments).

4. Explicit lifecycle management becomes necessary
   (e.g., startup/shutdown coordination, connection pools, long-lived clients).

5. Test setup becomes overly verbose due to manual wiring.

6. `bootstrap.py` becomes difficult to read or maintain.

As a rough guideline, this may occur when the system grows to **25–30 wired components**, although this is not a strict threshold.

Until then, the clarity of manual wiring is considered preferable.

---

## Consequences

### Benefits

- explicit and inspectable wiring
- strong alignment with hexagonal architecture
- minimal accidental complexity in v1
- high pedagogical value
- strong testability
- no hidden dependency resolution

---

### Costs

- increased verbosity in `bootstrap.py`
- manual updates required when adding new dependencies
- potential growth of the bootstrap module over time

These costs are acceptable at the current stage of the project.

---

## Alternatives Considered

### Lightweight DI container

Using a dependency injection library was considered.

**Advantages**

- reduces repetitive wiring
- simplifies systems with multiple entrypoints
- supports lifecycle management

**Disadvantages**

- introduces unnecessary conceptual complexity at this stage
- hides parts of the dependency graph
- reduces the educational value of explicit wiring
- encourages premature framework abstractions

For these reasons, this option was **postponed**.

---

### Global registry pattern

Another alternative was registering dependencies in global structures accessible from multiple modules.

**Advantages**

- quick implementation
- minimal initial code

**Disadvantages**

- introduces implicit global state
- complicates testing
- weakens architectural clarity
- promotes hidden coupling
- effectively becomes a service locator

This option was therefore rejected.

---

## References

Alistair Cockburn — _Hexagonal Architecture (Ports and Adapters)_

Robert C. Martin — _Clean Architecture_

Martin Fowler — _Inversion of Control Containers and the Dependency Injection Pattern_

Eric Evans — _Domain-Driven Design_

---

## Status

This decision is **accepted** for the initial version of the system.

Migration to a DI container remains intentionally deferred and should be documented through a new ADR if the defined criteria are met.
