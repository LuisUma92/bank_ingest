# ADR-0002: Gmail como fuente de ingestión de mensajes

**Estado:** Aceptado
**Fecha:** 2026-03-16
**Autor:** Proyecto `bank_ingest`

---

## Contexto

El sistema `bank_ingest` necesita una fuente confiable desde la cual obtener notificaciones bancarias que llegan por correo electrónico. Actualmente estas notificaciones llegan a una cuenta de **Gmail** y el usuario ya utiliza reglas y etiquetas para organizarlas manualmente.

El flujo manual actual es:

1. Los bancos envían correos de notificación de transacciones.
2. Gmail aplica filtros automáticos.
3. Los mensajes relevantes se etiquetan con **"Transacciones"**.
4. El usuario revisa manualmente estos correos y extrae la información.

El sistema debe automatizar la ingestión de estos mensajes para poder:

- identificar notificaciones relevantes
- extraer información financiera
- registrar los eventos en una base de datos
- mantener trazabilidad del procesamiento

Existen dos alternativas principales para obtener los mensajes desde Gmail:

1. **IMAP**
2. **Gmail API**

---

## Decisión

El sistema utilizará **Gmail API** como mecanismo oficial para obtener mensajes.

Los mensajes a procesar serán aquellos que posean la etiqueta:

```
Transacciones
```

El sistema actualizará el estado del mensaje mediante etiquetas adicionales según el resultado del procesamiento.

| Resultado | Acción                    |
| --------- | ------------------------- |
| éxito     | agregar etiqueta `parsed` |
| error     | agregar etiqueta `error`  |

Los mensajes que generen error permanecerán **no leídos** para facilitar su revisión manual desde la interfaz de Gmail.

---

## Justificación

### 1. Integración directa con el modelo de etiquetas de Gmail

Gmail no utiliza carpetas tradicionales como otros servidores IMAP. Utiliza un sistema de **labels** donde un mismo mensaje puede tener múltiples etiquetas.

La Gmail API permite trabajar directamente con este modelo:

- consultar mensajes por etiqueta
- agregar o eliminar etiquetas
- actualizar estado de lectura
- recuperar metadatos y contenido completo

IMAP expone las etiquetas como si fueran carpetas, lo cual introduce ambigüedades y duplicaciones.

---

### 2. Mejor control de estado del procesamiento

El sistema utiliza etiquetas para representar el estado del procesamiento.

Estados definidos:

| Estado    | Representación  |
| --------- | --------------- |
| pendiente | `Transacciones` |
| procesado | `parsed`        |
| error     | `error`         |

Esto permite observar el estado directamente desde Gmail sin depender del sistema.

---

### 3. Mayor robustez frente a duplicados

Cada mensaje de Gmail posee un identificador único:

```
message_id
thread_id
```

Estos identificadores permiten:

- evitar reprocesar mensajes
- mantener trazabilidad
- relacionar eventos con su origen

IMAP puede generar duplicados cuando un mensaje tiene múltiples etiquetas.

---

### 4. Seguridad mediante OAuth2

El acceso a Gmail se realiza mediante **OAuth2**, lo que implica que:

- el sistema no almacena contraseñas
- el usuario autoriza el acceso explícitamente
- los tokens pueden revocarse en cualquier momento

Los archivos utilizados son:

```
credentials.json
token.json
```

Estos archivos contienen:

- client_id
- client_secret
- access_token
- refresh_token

Nunca se almacenan contraseñas del usuario.

---

### 5. Compatibilidad con arquitectura hexagonal

La Gmail API se implementa como un **adaptador outbound** que satisface el puerto:

```
MessageSourcePort
```

Esto permite que el dominio y la aplicación no dependan directamente de Gmail.

Si en el futuro se quisiera utilizar otra fuente de mensajes (por ejemplo IMAP, Exchange o archivos locales), bastaría con implementar otro adaptador.

---

## Modelo de ingestión

El sistema realiza consultas periódicas a Gmail para obtener mensajes con la etiqueta:

```
Transacciones
```

La lógica de consulta excluye mensajes ya procesados.

Consulta conceptual:

```
label:Transacciones -label:parsed
```

El sistema recupera:

- metadata del mensaje
- cuerpo en texto plano
- cuerpo HTML
- headers relevantes
- snippet

Estos datos se transforman en una representación interna del dominio llamada:

```
SourceMessage
```

---

## Flujo de procesamiento

El flujo de ingestión será el siguiente:

1. consultar Gmail por mensajes con etiqueta `Transacciones`
2. excluir mensajes ya etiquetados como `parsed`
3. descargar el contenido del mensaje
4. convertir el mensaje en `SourceMessage`
5. almacenar artefactos en `data/raw_messages`
6. clasificar el mensaje
7. ejecutar el parser correspondiente
8. persistir evento financiero
9. actualizar etiquetas en Gmail

Resultado:

### éxito

```
+ parsed
```

### error

```
+ error
```

Los mensajes con error se mantienen **no leídos**.

---

## Ubicación del adaptador Gmail

Dentro del proyecto el adaptador Gmail se ubica en:

```
src/bank_ingest/adapters/outbound/gmail
```

Archivos principales:

```
auth.py
client.py
mapper.py
labels.py
```

Responsabilidades:

| archivo   | responsabilidad                  |
| --------- | -------------------------------- |
| auth.py   | autenticación OAuth              |
| client.py | comunicación con Gmail API       |
| mapper.py | conversión Gmail → SourceMessage |
| labels.py | operaciones sobre etiquetas      |

---

## Observabilidad

El estado del sistema puede observarse en dos niveles.

### Gmail

El usuario puede ver:

- mensajes pendientes
- mensajes procesados
- mensajes con error

directamente desde la interfaz de Gmail.

---

### Sistema local

El sistema mantiene artefactos de ingestión en:

```
data/raw_messages
data/rendered
data/parsed
data/errors
```

Esto permite depurar el procesamiento si el formato del correo cambia.

---

## Consecuencias

### Beneficios

- integración natural con Gmail
- estado visible desde el cliente de correo
- control fino de etiquetas
- menor riesgo de duplicados
- seguridad basada en OAuth2
- alineación con arquitectura hexagonal

---

### Costos

- dependencia de Gmail API
- necesidad de configurar OAuth2
- ligera complejidad adicional frente a IMAP simple

---

## Alternativas consideradas

### IMAP

IMAP fue considerado como alternativa.

Ventajas:

- protocolo estándar
- compatible con múltiples proveedores

Desventajas:

- tratamiento ambiguo de etiquetas Gmail
- duplicación de mensajes
- menor control sobre metadata
- dificultad para manipular etiquetas

Por estas razones se decidió utilizar Gmail API.

---

## Referencias

Google Gmail API Documentation
<https://developers.google.com/gmail/api>

Alistair Cockburn — Hexagonal Architecture
<https://alistair.cockburn.us/hexagonal-architecture>

OAuth2 Authorization Framework
RFC 6749

---

## Estado

Esta decisión queda **aceptada** para la versión inicial del sistema.
