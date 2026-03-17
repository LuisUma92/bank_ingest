# ADR-0003: Política de almacenamiento local (`data/`)

**Estado:** Aceptado
**Fecha:** 2026-03-16
**Autor:** Proyecto `bank_ingest`

---

## Contexto

El sistema `bank_ingest` procesa correos electrónicos que contienen notificaciones financieras enviadas por bancos.
Durante el desarrollo y la operación del sistema es necesario poder:

- depurar errores de parsing
- auditar eventos financieros extraídos
- reprocesar mensajes si cambian los parsers
- investigar cambios en el formato de correos enviados por los bancos

Una estrategia común en sistemas de ingestión de datos es almacenar **artefactos intermedios del pipeline** para facilitar observabilidad y reproducibilidad.

Sin embargo, el almacenamiento indiscriminado de estos artefactos también presenta desventajas:

- mayor consumo de disco
- exposición potencial de datos financieros sensibles
- complejidad operativa innecesaria en producción

Por esta razón se requiere una política explícita para el almacenamiento de artefactos generados durante el procesamiento.

---

## Decisión

El sistema mantendrá un directorio estructurado llamado:

```id="p4t0yh"
data/
```

Este directorio almacenará artefactos operativos generados durante el pipeline de ingestión.

La estructura definida es:

```id="p7ow7l"
data/
├── db/
├── raw_messages/
├── rendered/
├── parsed/
└── errors/
```

Cada subdirectorio representa una etapa distinta del pipeline de procesamiento.

La persistencia de cada tipo de artefacto será **configurable mediante banderas de configuración**.

---

## Descripción de cada directorio

### `data/db`

Contiene la base de datos local utilizada por el sistema.

Inicialmente se utilizará:

```id="6q6m4n"
SQLite
```

Motivaciones:

- simplicidad de despliegue
- base autocontenida
- facilidad de respaldo
- volumen de datos esperado bajo

El archivo principal será algo similar a:

```id="ptum61"
data/db/bank_ingest.sqlite
```

---

### `data/raw_messages`

Contiene copias del mensaje original descargado desde Gmail.

Formato típico:

```id="c7jvch"
.eml
.json
```

Contenido posible:

- headers completos
- cuerpo HTML
- cuerpo en texto plano
- metadata de Gmail
- identificadores del mensaje

Este artefacto permite:

- reprocesar mensajes si cambian los parsers
- analizar cambios en el formato de los correos
- auditar el origen de un evento financiero

---

### `data/rendered`

Contiene representaciones intermedias del mensaje preparadas para el parser.

Ejemplos:

- texto limpio extraído del HTML
- versión normalizada del contenido
- estructura simplificada de campos relevantes

Este paso intermedio facilita:

- depuración del parser
- aislamiento de errores en extracción de texto
- desarrollo incremental de parsers

---

### `data/parsed`

Contiene el resultado estructurado del proceso de parsing antes o después de persistirlo en la base de datos.

Ejemplo:

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

Estos artefactos permiten:

- inspeccionar rápidamente resultados de parsing
- validar parsers durante desarrollo
- reproducir errores reportados

---

### `data/errors`

Contiene información sobre mensajes que no pudieron procesarse correctamente.

Cada error debe incluir:

- identificador del mensaje
- motivo del error
- fragmentos relevantes del contenido
- contexto necesario para depuración

Ejemplo:

```json
{
  "message_id": "...",
  "error": "missing_authorization_code",
  "parser": "bac.transaction_notification",
  "excerpt": "...texto relevante..."
}
```

Estos artefactos permiten diagnosticar problemas de parsing o cambios en el formato de los correos.

---

## Organización interna

Dentro de cada directorio se recomienda organizar archivos por fecha para facilitar inspección y rotación.

Ejemplo:

```id="5q17dz"
raw_messages/
└── 2026/
    └── 03/
        └── 16/
```

Esto permite:

- identificar fácilmente cuándo se procesó un mensaje
- eliminar datos antiguos sin inspeccionar cada archivo
- facilitar auditorías temporales

---

## Política de configuración

La persistencia de artefactos será controlada mediante banderas configurables.

Ejemplos:

```id="ufsqw2"
STORE_RAW_MESSAGES=true
STORE_RENDERED_MESSAGES=true
STORE_PARSED_OUTPUT=true
STORE_ERROR_ARTIFACTS=true
```

Estas banderas permiten ajustar el comportamiento del sistema según el entorno:

### Desarrollo

```id="v4mk09"
STORE_RAW_MESSAGES=true
STORE_RENDERED_MESSAGES=true
STORE_PARSED_OUTPUT=true
STORE_ERROR_ARTIFACTS=true
```

### Producción mínima

```id="8nq0yr"
STORE_RAW_MESSAGES=true
STORE_RENDERED_MESSAGES=false
STORE_PARSED_OUTPUT=false
STORE_ERROR_ARTIFACTS=true
```

---

## Seguridad

Los datos almacenados en `data/` pueden contener información financiera sensible.

Por esta razón se establecen las siguientes prácticas:

- el directorio `data/` **no se versiona en git**
- el acceso al directorio debe restringirse a usuarios autorizados
- se recomienda usar permisos restrictivos en el sistema de archivos
- los backups deben protegerse adecuadamente

---

## Retención de datos

La política inicial de retención será conservadora para facilitar desarrollo y depuración.

Sugerencias iniciales:

| artefacto    | retención sugerida |
| ------------ | ------------------ |
| raw_messages | 90 días            |
| rendered     | 30 días            |
| parsed       | 30 días            |
| errors       | 180 días           |

La implementación de rotación automática se definirá en ADR posteriores.

---

## Relación con arquitectura hexagonal

El almacenamiento en `data/` se implementa mediante **adaptadores de almacenamiento** ubicados en:

```id="fwv9d6"
src/bank_ingest/adapters/outbound/storage
```

Estos adaptadores implementan puertos definidos en el dominio.

Esto permite que el dominio no dependa directamente del filesystem.

---

## Consecuencias

### Beneficios

- mejor depuración de parsers
- trazabilidad de eventos financieros
- posibilidad de reprocesar mensajes
- observabilidad del pipeline
- soporte para auditorías

---

### Costos

- mayor uso de disco
- necesidad de gestionar retención
- exposición potencial de datos sensibles si no se protege el sistema

Estos costos se consideran aceptables debido a los beneficios para desarrollo y operación.

---

## Alternativas consideradas

### No almacenar artefactos

Una alternativa sería no almacenar ningún artefacto intermedio y depender exclusivamente de la base de datos.

Esta opción fue descartada porque:

- dificulta depurar parsers
- impide reprocesar mensajes
- reduce observabilidad del pipeline
- complica auditorías

---

## Referencias

Martin Fowler — Feature Toggles
<https://martinfowler.com/articles/feature-toggles.html>

Alistair Cockburn — Hexagonal Architecture
<https://alistair.cockburn.us/hexagonal-architecture>

---

## Estado

Esta política queda **aceptada** para la versión inicial del sistema.
