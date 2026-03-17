# ADR-0001: Arquitectura del sistema `bank_ingest`

**Estado:** Aceptado
**Fecha:** 2026-03-16
**Autor:** Proyecto `bank_ingest`

---

## Contexto

El proyecto `bank_ingest` tiene como objetivo automatizar la ingestión, clasificación y procesamiento de correos electrónicos de notificaciones bancarias para extraer eventos financieros estructurados que puedan ser analizados posteriormente.

Actualmente el proceso se realiza manualmente. El sistema automatizado debe:

1. Leer correos de Gmail etiquetados como **"Transacciones"**.
2. Clasificar y parsear notificaciones bancarias.
3. Extraer información estructurada sobre eventos financieros.
4. Persistir los eventos en una base de datos local.
5. Marcar los correos en Gmail según el resultado del procesamiento.

Este proyecto también tiene un objetivo pedagógico explícito: **practicar arquitectura de software utilizada en entornos industriales**, específicamente arquitecturas orientadas a dominio y arquitecturas hexagonales.

Por esta razón se ha decidido adoptar una arquitectura formal desde el inicio, aun cuando para una v1 funcional podría ser considerada sobreingeniería.

---

## Decisión

El sistema se implementará utilizando una **arquitectura hexagonal (Ports and Adapters)** combinada con principios de **Domain-Driven Design (DDD)** y **Clean Architecture**.

Las decisiones arquitectónicas fundamentales son:

### 1. Separación estricta entre dominio e infraestructura

El sistema se organiza en las siguientes capas:

- **Domain**
- **Application**
- **Adapters**
- **Shared**

El dominio nunca debe depender de:

- Gmail API
- SQLAlchemy
- filesystem
- CLI
- Google Sheets
- frameworks externos

Las dependencias siempre deben apuntar **hacia el dominio**, nunca desde el dominio hacia afuera.

---

### 2. Uso de puertos y adaptadores

El dominio y la aplicación definen **puertos** (interfaces abstractas).

Los adaptadores implementan esos puertos para tecnologías concretas.

Ejemplos de puertos:

- `MessageSourcePort`
- `EventRepositoryPort`
- `MessageStorePort`
- `ProcessingStatePort`

Ejemplos de adaptadores:

- Gmail API adapter
- SQLAlchemy repository
- Filesystem storage
- Google Sheets exporter

Este patrón permite cambiar infraestructura sin modificar el dominio.

---

### 3. Organización del código

La estructura del proyecto será:

```
src/bank_ingest/
├── domain
├── application
├── adapters
└── shared
```

#### Domain

Define el modelo del problema.

Contiene:

- entidades
- value objects
- enums
- servicios de dominio
- excepciones de dominio
- puertos

El dominio describe **qué es el sistema**, no **cómo funciona técnicamente**.

---

#### Application

Define los **casos de uso**.

Orquesta el flujo de procesamiento:

1. obtener mensajes
2. clasificarlos
3. parsearlos
4. persistir eventos
5. actualizar estado del mensaje

La capa application depende del dominio y de los puertos definidos en él.

No depende directamente de Gmail ni de SQL.

---

#### Adapters

Contiene implementaciones concretas de los puertos.

Se divide en:

**Inbound adapters**

- CLI
- tareas programadas

**Outbound adapters**

- Gmail API
- Parsers específicos de bancos
- Persistencia SQLAlchemy
- Filesystem storage
- Exportadores externos

Los adaptadores traducen entre:

- modelos externos
- modelos del dominio

---

#### Shared

Utilidades técnicas reutilizables que no pertenecen al dominio.

Ejemplos:

- parsing de fechas
- operaciones monetarias
- hashing
- limpieza de texto

Debe mantenerse pequeño para evitar convertirse en un “cajón de sastre”.

---

### 4. Sistema de parsers extensible

El sistema debe soportar múltiples bancos y múltiples tipos de notificación.

La estrategia es:

```
parser/
 ├── base.py
 └── bac/
     ├── classifier.py
     └── transaction_notification.py
```

Cada banco tiene su propio módulo.

Cada tipo de notificación tiene su propio parser.

Esto evita crear archivos monolíticos a medida que el sistema crece.

---

### 5. Fuente de datos: Gmail

Los mensajes se obtienen desde **Gmail API**.

Se procesan únicamente correos con la etiqueta:

```
Transacciones
```

El sistema actualiza etiquetas según el resultado:

| Resultado | Acción                    |
| --------- | ------------------------- |
| éxito     | agregar etiqueta `parsed` |
| error     | agregar etiqueta `error`  |

Los errores deben permanecer **no leídos** para facilitar su revisión manual.

---

### 6. Persistencia

La persistencia inicial se realizará mediante:

**SQLite + SQLAlchemy**

Motivación:

- simplicidad de despliegue
- base local
- suficiente para el volumen esperado
- fácil backup

Posteriormente podría migrarse a PostgreSQL sin modificar el dominio.

---

### 7. Almacenamiento local de artefactos (`data/`)

El sistema mantiene un directorio `data/` para almacenar artefactos de procesamiento.

Esto cumple funciones de:

- depuración
- auditoría
- reproducibilidad
- desarrollo de parsers

Estructura:

```
data/
├── db
├── raw_messages
├── rendered
├── parsed
└── errors
```

#### raw_messages

Correos originales descargados.

Permite reprocesar mensajes si cambian los parsers.

---

#### rendered

Representación intermedia del mensaje.

Ejemplo:

- texto limpio extraído del HTML

---

#### parsed

Resultado estructurado del parser.

---

#### errors

Artefactos asociados a fallos de parsing.

Incluyen:

- mensaje original
- motivo del error
- fragmentos relevantes

---

### 8. Política de almacenamiento configurable

El almacenamiento de artefactos se controlará mediante **banderas de configuración**.

Ejemplos:

```
STORE_RAW_MESSAGES=true
STORE_RENDERED_MESSAGES=true
STORE_PARSED_OUTPUT=true
STORE_ERROR_ARTIFACTS=true
```

Esto permite cambiar el comportamiento sin modificar código.

La estrategia está inspirada en **feature toggles**.

---

### 9. Seguridad de credenciales

El acceso a Gmail utiliza **OAuth2**.

El sistema nunca almacena contraseñas.

Se utilizan dos archivos:

```
credentials.json
token.json
```

Ubicados fuera del repositorio.

Estos archivos:

- no se versionan
- tienen permisos restrictivos
- pueden revocarse desde la cuenta Google

---

### 10. Observabilidad

El sistema tendrá dos tipos de observabilidad.

#### Logs

Directorio:

```
logs/
```

Contiene eventos de ejecución del sistema.

---

#### Artefactos operativos

Directorio:

```
data/
```

Contiene datos de procesamiento útiles para auditoría.

---

## Consecuencias

### Beneficios

- arquitectura escalable
- independencia del dominio
- facilidad para agregar nuevos bancos
- facilidad para cambiar persistencia
- facilidad para depurar parsers
- trazabilidad del procesamiento

Además, esta arquitectura permite practicar principios utilizados en sistemas empresariales reales.

---

### Costos

- mayor complejidad inicial
- más archivos y capas
- mayor disciplina requerida para mantener separaciones correctas

Para un proyecto pequeño esto puede considerarse sobreingeniería, pero se acepta como decisión consciente con fines educativos y de calidad arquitectónica.

---

## Alternativas consideradas

### Arquitectura monolítica simple

Una estructura más simple podría haber sido:

```
src/
 parser/
 gmail/
 db/
 main.py
```

Esta opción fue descartada porque:

- mezcla lógica de dominio con infraestructura
- dificulta escalar a múltiples bancos
- complica testing
- reduce valor educativo del proyecto

---

## Referencias

Alistair Cockburn — _Hexagonal Architecture (Ports and Adapters)_
<https://alistair.cockburn.us/hexagonal-architecture>

Eric Evans — _Domain-Driven Design_

Martin Fowler — _Patterns of Enterprise Application Architecture_

Robert C. Martin — _Clean Architecture_

Martin Fowler — _Feature Toggles_
<https://martinfowler.com/articles/feature-toggles.html>

---

## Estado

Esta arquitectura se considera **aceptada** para la versión inicial del sistema.

Cambios futuros deberán registrarse mediante nuevos ADR.
