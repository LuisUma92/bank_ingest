# CLAUDE.md — Proyecto `bank_ingest`

Documento de orientación para asistentes de desarrollo (Claude, ChatGPT, Copilot u otros) que trabajen sobre este repositorio.
Este archivo describe **cómo está diseñado el sistema, cómo debe evolucionar y qué reglas arquitectónicas deben respetarse**.

Para minimizar redundancia, este documento **remite a los ADR (Architecture Decision Records)** donde se documentan las decisiones completas.

---

## 1. Propósito del proyecto

`bank_ingest` es un sistema que:

1. obtiene correos de Gmail etiquetados como **Transacciones**
2. identifica notificaciones bancarias
3. extrae eventos financieros estructurados
4. persiste los eventos en una base de datos
5. marca el correo según el resultado del procesamiento

El objetivo principal es **automatizar la extracción de datos financieros desde correos electrónicos**.

Un objetivo secundario explícito es **aprender y practicar arquitectura de software industrial**.

---

## 2. Alcance de la versión inicial

La primera versión soporta:

Banco soportado:

```
BAC
```

Tipo de notificación:

```
notificación de transacción de tarjeta
```

Campos extraídos:

```
merchant
transaction_date
card_brand
card_last4
authorization_code
transaction_type
amount
currency
```

El sistema debe poder extenderse posteriormente a otros bancos y otros tipos de notificación.

La estrategia de extensión está definida en:

```
ADR-0004-parser-strategy.md
```

---

## 3. Arquitectura general

El sistema utiliza **arquitectura hexagonal (Ports and Adapters)**.

Referencia completa:

```
ADR-0001-architecture.md
```

Capas principales:

```
domain
application
adapters
shared
```

Principio fundamental:

**El dominio nunca depende de infraestructura externa.**

Dependencias permitidas:

```
adapters → application → domain
```

Dependencias prohibidas:

```
domain → adapters
domain → frameworks externos
```

---

## 4. Estructura del proyecto

Estructura relevante:

```
src/bank_ingest/
```

Submódulos:

```
domain/
application/
adapters/
shared/
```

Descripción resumida:

| carpeta     | responsabilidad                   |
| ----------- | --------------------------------- |
| domain      | modelo del problema               |
| application | casos de uso                      |
| adapters    | integración con sistemas externos |
| shared      | utilidades comunes                |

Explicación completa en:

```
ADR-0001-architecture.md
```

---

## 5. Flujo principal del sistema

Pipeline de procesamiento:

1. consultar Gmail
2. obtener mensajes etiquetados `Transacciones`
3. convertir mensaje a `SourceMessage`
4. almacenar mensaje en `data/raw_messages`
5. clasificar banco y tipo de notificación
6. seleccionar parser correspondiente
7. extraer evento financiero
8. persistir evento
9. actualizar etiquetas del correo

Resultados posibles:

| resultado | acción                    |
| --------- | ------------------------- |
| éxito     | agregar etiqueta `parsed` |
| error     | agregar etiqueta `error`  |

Los errores permanecen **no leídos**.

La decisión completa se documenta en:

```
ADR-0002-gmail-as-source.md
```

---

## 6. Fuente de mensajes

Fuente de ingestión:

```
Gmail API
```

Etiqueta utilizada:

```
Transacciones
```

El sistema busca mensajes:

```
label:Transacciones -label:parsed
```

Detalles en:

```
ADR-0002-gmail-as-source.md
```

---

## 7. Política de almacenamiento local

El sistema mantiene artefactos operativos en:

```
data/
```

Estructura:

```
data/
 ├── db/
 ├── raw_messages/
 ├── rendered/
 ├── parsed/
 └── errors/
```

Finalidad:

- depuración
- auditoría
- reproducibilidad
- desarrollo de parsers

La persistencia de artefactos es configurable mediante flags.

Detalles completos:

```
ADR-0003-storage-policy.md
```

---

## 8. Estrategia de parsers

Los parsers se organizan por banco y tipo de notificación.

Ejemplo:

```
parser/
 ├── base.py
 └── bac/
     ├── classifier.py
     └── transaction_notification.py
```

Responsabilidades separadas:

| componente | función                                  |
| ---------- | ---------------------------------------- |
| classifier | identificar banco y tipo de notificación |
| parser     | extraer campos estructurados             |

Detalles completos:

```
ADR-0004-parser-strategy.md
```

---

## 9. Seguridad

El sistema utiliza **OAuth2** para autenticarse con Gmail.

Archivos necesarios:

```
credentials.json
token.json
```

Estos archivos:

- no deben versionarse
- deben tener permisos restrictivos
- se ubican fuera del repositorio

El sistema **nunca almacena contraseñas**.

Referencia:

```
ADR-0002-gmail-as-source.md
```

---

## 10. Base de datos

Persistencia inicial:

```
SQLite + SQLAlchemy
```

Ubicación:

```
data/db/
```

La base de datos contiene eventos financieros normalizados.

El dominio no depende de SQLAlchemy.

El acceso se realiza mediante el patrón:

```
Repository
```

---

## 11. Observabilidad

El sistema tiene dos niveles de observabilidad.

### Logs

Directorio:

```
logs/
```

Contiene eventos de ejecución.

---

### Artefactos operativos

Directorio:

```
data/
```

Contiene datos del pipeline para auditoría y depuración.

---

## 12. Testing

Los tests se organizan en:

```
tests/
```

Subcarpetas:

```
unit/
integration/
fixtures/
```

Los tests unitarios deben cubrir:

- parsers
- normalización
- lógica de dominio

Los tests de integración deben cubrir:

- Gmail adapter (mockeado)
- persistencia
- filesystem storage

---

## 13. Reglas para contribuciones automáticas

Cuando un asistente de desarrollo genere código debe respetar:

### 1. No romper la arquitectura

No introducir dependencias desde:

```
domain → adapters
```

---

### 2. Parsers deben ser pequeños

Cada tipo de notificación debe tener su propio parser.

No crear archivos monolíticos.

---

### 3. No duplicar lógica

Las utilidades deben ir a:

```
shared/
```

---

### 4. No escribir directamente al filesystem

El acceso a `data/` debe realizarse mediante adaptadores de storage.

---

### 5. Mantener trazabilidad

Cada evento financiero debe mantener referencia al mensaje original.

---

## 14. Cambios arquitectónicos

Las decisiones arquitectónicas deben documentarse mediante **ADR**.

Directorio:

```
ADR/
```

Ejemplo:

```
ADR-0005-new-bank-parser.md
```

---

## 15. Futuras extensiones

Extensiones previstas:

- soporte para múltiples bancos
- nuevos tipos de notificación
- exportación automática a Google Sheets
- dashboards financieros
- rotación automática de artefactos en `data/`
- métricas de procesamiento
- soporte para múltiples cuentas de correo

Estas extensiones **no deben romper la arquitectura hexagonal**.

---

## 16. Principio rector del proyecto

Este sistema prioriza:

```
claridad arquitectónica
modularidad
extensibilidad
observabilidad
```

sobre simplicidad extrema de implementación.

El objetivo es construir un sistema pequeño pero **arquitectónicamente sólido**.
