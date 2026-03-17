# ADR-0006: Estrategia de selección de parsers

**Estado:** Aceptado
**Fecha:** 2026-03-16
**Autor:** Proyecto `bank_ingest`

---

## Contexto

El sistema `bank_ingest` procesa correos electrónicos de notificaciones bancarias con el objetivo de extraer eventos financieros estructurados.

El flujo general de procesamiento es:

1. Obtener mensaje desde la fuente (Gmail).
2. Clasificar el mensaje.
3. Seleccionar el parser adecuado.
4. Parsear el contenido.
5. Persistir el evento resultante.
6. Actualizar el estado del mensaje.

La clasificación ocurre en dos dimensiones:

- **Banco emisor** (`Bank`)
- **Tipo de notificación** (`NotificationType`)

Ejemplo:

```

Bank.BAC
NotificationType.TRANSACTION_NOTIFICATION

```

Una vez clasificado el mensaje, el sistema debe seleccionar automáticamente el parser correcto.

Se espera que el sistema crezca aproximadamente a:

- ~5 bancos
- ~3 tipos de notificación por banco

Lo que implica alrededor de **15 combinaciones posibles de parsers**.

Se evaluaron tres estrategias principales:

1. **Registry explícito**
2. **Auto-discovery de parsers**
3. **Chain of Responsibility**

---

## Decisión

El sistema utilizará un **registry explícito de parsers**, indexado por la combinación:

```

(Bank, NotificationType)

```

El registry será responsable de resolver qué parser corresponde a una clasificación determinada.

Ejemplo conceptual:

```python
registry: dict[tuple[Bank, NotificationType], BaseParser]
```

La resolución seguirá el flujo:

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

Cada combinación `(Bank, NotificationType)` debe mapear a **exactamente un parser**.

---

## Registro asistido por metadata del parser

Para reducir duplicación, cada parser declarará su identidad mediante atributos de clase:

```python
class BacTransactionNotificationParser(BaseParser):

    bank = Bank.BAC
    notification_type = NotificationType.TRANSACTION_NOTIFICATION
```

El registry permitirá registrar parsers mediante:

```python
registry.register_parser(BacTransactionNotificationParser())
```

Internamente, el registry construirá la clave:

```
(parser.bank, parser.notification_type)
```

Esto evita duplicar información entre el parser y el registry.

---

## Restricciones del registry

El registry debe garantizar las siguientes propiedades:

### Unicidad

No puede existir más de un parser para una misma combinación:

```
(Bank, NotificationType)
```

Si ocurre una colisión, el sistema debe fallar durante bootstrap.

---

### Resolución determinista

La selección del parser no debe depender de heurísticas ni del orden de evaluación.

Dado un `(Bank, NotificationType)`, el resultado debe ser siempre el mismo parser.

---

### Inicialización explícita

El conjunto de parsers disponibles debe declararse explícitamente en el composition root o en un módulo de registro.

Ejemplo:

```python
def build_parser_registry() -> ParserRegistry:
    registry = ParserRegistry()

    registry.register_parser(BacTransactionNotificationParser())
    registry.register_parser(BacDebitNotificationParser())

    return registry
```

Esto mantiene la visibilidad de los componentes activos en el sistema.

---

## `can_parse()` como verificación defensiva

El `BaseParser` puede exponer un método:

```python
def can_parse(message: RawMessage) -> bool
```

Este método **no se utilizará para seleccionar el parser**, sino como:

- verificación defensiva
- validación interna del parser
- herramienta útil en tests
- protección ante errores de clasificación

La selección principal del parser seguirá siendo responsabilidad del `ParserRegistry`.

---

## Alternativas consideradas

### 1. Auto-discovery de parsers

Se consideró implementar un mecanismo que escanee módulos de parsers y registre automáticamente las clases disponibles mediante decoradores, metaclasses o introspección de paquetes.

Ejemplo conceptual:

```
scan parsers/*
↓
import modules
↓
auto-register parsers
```

**Ventajas:**

- menor trabajo manual al agregar nuevos parsers
- extensibilidad automática

**Desventajas:**

- dependencia en side-effects de import
- mayor dificultad de debugging
- parsers activos pueden depender del orden de importación
- reduce visibilidad del sistema
- introduce "magia" innecesaria

Dado que el número esperado de parsers es relativamente pequeño (~15), el beneficio no justifica la complejidad adicional.

Por lo tanto, esta opción fue descartada.

---

### 2. Chain of Responsibility

Otra opción considerada fue permitir que cada parser implementara:

```python
can_parse(message)
```

y probar parsers secuencialmente hasta encontrar uno que acepte el mensaje.

Ejemplo:

```
for parser in parsers:
    if parser.can_parse(message):
        return parser
```

**Ventajas:**

- parsers encapsulan su propia lógica de reconocimiento
- mayor flexibilidad en casos ambiguos

**Desventajas:**

- duplica lógica de clasificación dentro de parsers
- puede volver el sistema menos predecible
- el orden de evaluación se vuelve relevante
- menor claridad arquitectónica

Dado que el sistema ya posee una etapa explícita de **clasificación previa**, esta estrategia introduciría redundancia innecesaria.

Por lo tanto, fue descartada.

---

## Consecuencias

### Beneficios

- selección de parser simple y determinista
- separación clara entre **clasificación** y **parsing**
- registry pequeño y fácil de mantener
- visibilidad explícita de los parsers disponibles
- comportamiento predecible

---

### Costos

- el registry debe actualizarse al agregar nuevos parsers
- se requiere disciplina para mantener el registro consistente

Dado el tamaño esperado del sistema, estos costos se consideran mínimos.

---

## Referencias

- Alistair Cockburn — _Hexagonal Architecture_
- Martin Fowler — _Patterns of Enterprise Application Architecture_
- Eric Evans — _Domain-Driven Design_

---

## Estado

Esta decisión queda **aceptada** para la versión actual del sistema.

Si en el futuro el número de parsers creciera significativamente o se introdujera un sistema de plugins externos, podría reconsiderarse una estrategia de descubrimiento automático mediante un nuevo ADR.
