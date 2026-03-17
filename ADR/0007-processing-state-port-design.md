# ADR-0007: Diseño del ProcessingStatePort

**Estado:** Aceptado
**Fecha:** 2026-03-16
**Autor:** Proyecto `bank_ingest`

---

## Contexto

El sistema `bank_ingest` procesa correos electrónicos de notificaciones bancarias obtenidos desde Gmail.  
Una vez procesado un mensaje, el sistema debe actualizar su **estado de procesamiento** para evitar reprocesamientos y permitir observabilidad del pipeline.

En Gmail, este estado se representa mediante **labels** aplicados al mensaje, por ejemplo:

- `parsed`
- `error`

Estas etiquetas permiten distinguir mensajes que ya fueron procesados de aquellos que aún deben procesarse o que fallaron.

Sin embargo, en una arquitectura hexagonal, el dominio y la capa application no deben depender directamente de conceptos específicos de la infraestructura (como labels de Gmail).

Por lo tanto, es necesario definir un **port de salida** que permita expresar el estado del procesamiento sin acoplar el sistema a la semántica específica de Gmail.

Este port se denomina:

```

ProcessingStatePort

```

---

## Decisión

El `ProcessingStatePort` expondrá **operaciones orientadas al resultado del procesamiento**, no operaciones de manipulación directa de labels.

El contrato mínimo del port será:

```python
class ProcessingStatePort(Protocol):

    def mark_processed(self, message_id: MessageId) -> None:
        ...

    def mark_failed(self, message_id: MessageId, reason: str | None = None) -> None:
        ...

    def mark_skipped(self, message_id: MessageId, reason: str | None = None) -> None:
        ...
```

Este port describe **transiciones del pipeline de procesamiento**, no operaciones genéricas de etiquetado.

La implementación concreta en el adaptador de Gmail será responsable de traducir estas operaciones a modificaciones de labels en Gmail.

---

## Traducción en el adaptador Gmail

El adaptador `GmailProcessingStateAdapter` implementará el port y mapeará cada operación a la manipulación de labels.

Ejemplo conceptual:

| Operación del port | Acción en Gmail                       |
| ------------------ | ------------------------------------- |
| `mark_processed`   | agregar label `parsed`                |
| `mark_failed`      | agregar label `error`                 |
| `mark_skipped`     | agregar label `skipped` o equivalente |

Los detalles exactos de labels permanecen encapsulados dentro del adaptador.

De esta manera:

- el dominio no depende de Gmail
- el comportamiento externo sigue siendo observable mediante labels

---

## Razonamiento arquitectónico

### Separación de dominio e infraestructura

El dominio y la capa application deben expresar **intenciones de negocio**, no detalles técnicos de una API externa.

Exponer operaciones como:

```
add_label
remove_label
set_labels
```

introduciría semántica específica de Gmail en la interfaz del port.

Esto violaría la separación deseada entre application e infraestructura.

El uso de operaciones como:

```
mark_processed
mark_failed
```

expresa el lenguaje natural del pipeline.

---

### Claridad semántica del pipeline

El sistema posee tres resultados principales para un mensaje:

1. **Processed**
   El mensaje fue parseado correctamente y se generó un evento válido.

2. **Failed**
   Ocurrió un error durante parsing o procesamiento.

3. **Skipped**
   El mensaje no corresponde a un tipo soportado o no debe procesarse.

Estas categorías permiten distinguir claramente los estados del pipeline.

---

## Manejo de fallos parciales

Puede ocurrir el siguiente escenario:

```
mensaje parseado correctamente
↓
evento persistido
↓
fallo al actualizar labels en Gmail
```

Este caso se considera un **fallo de sincronización externa**, no un fallo del procesamiento de negocio.

Por lo tanto:

- el evento persistido **no debe revertirse**
- el sistema debe registrar el incidente
- el error debe ser observable en logs o artefactos de error

Esto evita acoplar la consistencia del sistema interno a la disponibilidad de Gmail.

El sistema debe tratar la actualización de estado como **operación posterior al procesamiento principal**.

Ejemplo conceptual:

```python
event_repository.save(event)

try:
    processing_state.mark_processed(message.id)
except Exception:
    logger.error("Failed to update processing state")
```

Esto permite que el sistema interno permanezca consistente incluso si Gmail falla temporalmente.

---

## Alternativas consideradas

### 1. Port basado en labels

Exponer operaciones genéricas como:

```
add_label(label)
remove_label(label)
```

**Ventajas**

- máxima flexibilidad
- alineación directa con Gmail

**Desventajas**

- introduce semántica específica de Gmail
- acopla la capa application a la infraestructura
- reduce claridad del lenguaje del dominio

Esta opción fue descartada.

---

### 2. Abstracción genérica de "tags"

Otra alternativa era exponer un sistema de "tags" abstractos.

Ejemplo:

```
add_tag("processed")
add_tag("error")
```

**Ventajas**

- desacopla de Gmail

**Desventajas**

- introduce una abstracción innecesariamente genérica
- no refleja claramente el estado del pipeline
- complica el modelo conceptual sin beneficio real

Esta opción fue descartada.

---

## Consecuencias

### Beneficios

- desacoplamiento entre dominio y Gmail
- interfaz del port alineada con el lenguaje del pipeline
- claridad semántica en application
- facilidad de testing mediante adaptadores fake
- encapsulación completa de detalles de infraestructura

---

### Costos

- menor flexibilidad si se necesitaran operaciones más complejas sobre labels
- posible necesidad de extender el port en el futuro si aparecen nuevos estados

Estos costos se consideran aceptables para la versión actual del sistema.

---

## Referencias

- Alistair Cockburn — _Hexagonal Architecture (Ports and Adapters)_
- Eric Evans — _Domain-Driven Design_
- Robert C. Martin — _Clean Architecture_

---

## Estado

Esta decisión queda **aceptada** para la versión actual del sistema.

Si en el futuro el sistema necesitara manejar estados adicionales o sincronización más compleja con proveedores externos, la interfaz del port podrá extenderse mediante un nuevo ADR.
