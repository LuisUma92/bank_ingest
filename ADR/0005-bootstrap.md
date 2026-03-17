# ADR-0005: Bootstrap y estrategia de Dependency Injection

**Estado:** Aceptado
**Fecha:** 2026-03-16
**Autor:** Proyecto `bank_ingest`

---

## Contexto

El sistema `bank_ingest` utiliza una arquitectura hexagonal en la que el dominio y la capa application definen puertos, y los adaptadores concretos implementan esos contratos para tecnologías como Gmail API, SQLAlchemy y filesystem. La orquestación del flujo principal ocurre en application, mientras que la infraestructura debe permanecer fuera del dominio.

En la versión inicial del sistema existen aproximadamente 15 componentes que deben conectarse entre sí, incluyendo:

- adaptadores de fuente de mensajes
- adaptadores de persistencia
- adaptadores de almacenamiento de artefactos
- adaptadores de actualización de estado en Gmail
- registries o resolvedores de parsers
- casos de uso de application

Se requiere definir una estrategia de **bootstrap** y **dependency injection** para cablear estas dependencias de forma consistente con la arquitectura adoptada.

Las alternativas consideradas son:

1. **Constructor injection manual** mediante un `create_app()` que instancia y conecta todos los componentes.
2. **Lightweight DI container** usando una librería como `dependency-injector`.
3. **Registry pattern global** con registro de dependencias en diccionarios o singletons compartidos.

Dado que el proyecto tiene también un objetivo pedagógico explícito —practicar arquitectura usada en entornos industriales— la decisión debe privilegiar claridad, trazabilidad y disciplina arquitectónica.

---

## Decisión

El sistema utilizará **constructor injection manual** en un único **composition root** ubicado en:

```

src/bank_ingest/bootstrap.py

```

Este módulo expondrá una función del tipo:

```python
create_app()
```

responsable de:

1. cargar configuración
2. construir clientes técnicos
3. instanciar adaptadores concretos
4. instanciar servicios y casos de uso
5. conectar dependencias entre puertos y adaptadores
6. devolver un contenedor liviano de servicios de aplicación o la composición final requerida por el entrypoint

No se utilizará, por ahora, un DI container externo.

Tampoco se permitirá el uso de registros globales de dependencias, service locators implícitos ni singletons accesibles por import.

---

## Justificación

### 1. Máxima claridad del grafo de dependencias

En un sistema pequeño o mediano, el cableado manual permite ver de forma explícita qué depende de qué.

Esto es especialmente valioso en una arquitectura hexagonal, donde una de las disciplinas más importantes es mantener la dirección correcta de las dependencias: hacia el dominio y nunca desde el dominio hacia la infraestructura.

Un `bootstrap.py` explícito actúa como punto único de ensamblaje y hace visible:

- qué puertos existen
- qué adaptadores los satisfacen
- qué casos de uso dependen de cuáles puertos
- qué componentes técnicos son compartidos

---

### 2. Mejor alineación con el objetivo pedagógico del proyecto

El proyecto acepta conscientemente una arquitectura formal, incluso si para una v1 podría parecer más pesada de lo estrictamente necesario, porque uno de sus objetivos es aprender prácticas de software más cercanas a entornos industriales.

El wiring manual obliga a comprender el sistema de forma explícita:

- dónde termina application
- dónde empieza infrastructure
- qué dependencia pertenece a cada capa
- qué contrato satisface cada adaptador

Un DI container ocultaría parte de esa comprensión detrás de providers, wiring declarativo o mecanismos de resolución automática.

---

### 3. Menor complejidad accidental en la versión inicial

Con aproximadamente 15 componentes a cablear, introducir un contenedor de DI agregaría otra capa conceptual sin aportar todavía un beneficio proporcional.

En esta etapa, el problema principal no es administrar un grafo de dependencias demasiado grande, sino mantener el sistema entendible y correctamente separado.

El constructor injection manual resuelve ese problema con menor complejidad operacional.

---

### 4. Mejor testabilidad sin magia

Cuando las dependencias se inyectan por constructor y el composition root está aislado en `bootstrap.py`, los tests pueden instanciar casos de uso directamente con fakes, stubs o adaptadores de prueba.

Esto evita:

- estado global compartido
- dependencia en un contenedor activo
- resolución implícita en tiempo de ejecución
- dificultad para aislar pruebas unitarias

---

### 5. Evita service locator disfrazado

El patrón de registro global fue descartado porque tiende a introducir estado global implícito y hace menos evidente el origen real de las dependencias.

Eso debilita la disciplina arquitectónica del proyecto y dificulta:

- razonamiento sobre el sistema
- debugging
- testing
- refactors seguros

---

## Forma de implementación

El composition root debe mantenerse concentrado en un único módulo.

Ejemplo conceptual:

```python
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

Este ejemplo es ilustrativo. La estructura exacta podrá ajustarse con el crecimiento del proyecto.

---

## Criterio para futura migración a un DI container

La decisión actual **no prohíbe** el uso futuro de un DI container.

Se adopta constructor injection manual como estrategia inicial y se define el siguiente criterio de revisión:

Se reconsiderará migrar a un DI container cuando se cumplan **dos o más** de las siguientes condiciones:

1. Existan **múltiples entrypoints** con wiring distinto
   Ejemplo: CLI, scheduler, worker de reprocesamiento, API HTTP, scripts de backfill.

2. Exista **duplicación relevante del wiring** entre entrypoints o módulos de arranque.

3. La configuración por entorno se vuelva **significativamente condicional**
   Ejemplo: adaptadores distintos en dev, test, prod o perfiles con servicios opcionales.

4. Sea necesario administrar de forma explícita el **lifecycle** de recursos compartidos
   Ejemplo: startup/shutdown coordinado, pools, sesiones, clients complejos.

5. El armado manual en tests se vuelva demasiado verboso o repetitivo.

6. El `bootstrap.py` deje de ser fácil de leer y mantener
   Como señal orientativa, esto puede ocurrir alrededor de **25–30 componentes cableados**, aunque no constituye un umbral rígido.

Mientras estas condiciones no se cumplan, la claridad del wiring manual se considera superior al beneficio de introducir un contenedor externo.

---

## Consecuencias

### Beneficios

- wiring explícito y fácil de inspeccionar
- alineación con arquitectura hexagonal
- menor complejidad accidental en v1
- alto valor pedagógico
- alta testabilidad
- ausencia de magia o resolución implícita

---

### Costos

- mayor verbosidad en `bootstrap.py`
- necesidad de actualizar manualmente el composition root al agregar dependencias
- posible crecimiento del archivo de arranque con el tiempo

Estos costos se consideran aceptables en la etapa actual del proyecto.

---

## Alternativas consideradas

### 1. Lightweight DI container

Se consideró utilizar una librería de dependency injection.

**Ventajas:**

- reduce wiring repetitivo
- facilita escenarios con múltiples entrypoints
- mejora manejo de providers y lifecycle cuando el sistema crece

**Desventajas:**

- agrega complejidad conceptual innecesaria en la etapa actual
- oculta parte del grafo de dependencias
- reduce parte del valor pedagógico del wiring explícito
- puede incentivar uso prematuro de abstracciones de framework

Se decide **posponer** esta opción para una etapa futura en la que el costo del wiring manual deje de ser razonable.

---

### 2. Registry pattern global

Se consideró registrar dependencias en estructuras globales accesibles desde distintos módulos.

**Ventajas:**

- implementación rápida
- poco código inicial

**Desventajas:**

- introduce estado global implícito
- dificulta testing
- reduce claridad arquitectónica
- favorece acoplamiento oculto
- se aproxima a un service locator, lo cual contradice el objetivo de dependencias explícitas

Esta alternativa fue descartada.

---

## Referencias

- Alistair Cockburn — _Hexagonal Architecture (Ports and Adapters)_
- Robert C. Martin — _Clean Architecture_
- Martin Fowler — _Inversion of Control Containers and the Dependency Injection Pattern_
- Eric Evans — _Domain-Driven Design_

---

## Estado

Esta decisión queda **aceptada** para la versión inicial del sistema.

La migración a un DI container queda explícitamente diferida y deberá registrarse mediante un nuevo ADR si en el futuro se cumplen los criterios definidos en este documento.
