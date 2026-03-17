# ADR-0004: Estrategia de parsers para notificaciones bancarias

**Estado:** Aceptado
**Fecha:** 2026-03-16
**Autor:** Proyecto `bank_ingest`

---

## Contexto

El sistema `bank_ingest` debe procesar correos electrónicos enviados por múltiples bancos que contienen notificaciones de eventos financieros.

Estas notificaciones presentan varias características que afectan el diseño del sistema:

1. Cada banco utiliza **formatos de correo distintos**.
2. Un mismo banco puede enviar **varios tipos de notificación**.
3. Los formatos de los correos **pueden cambiar con el tiempo**.
4. Los mensajes pueden contener tanto **HTML como texto plano**.
5. La estructura semántica de los datos no es uniforme entre bancos.

Ejemplos de tipos de notificación posibles:

- uso de tarjeta de crédito
- uso de tarjeta de débito
- pago de tarjeta
- transferencia recibida
- transferencia enviada
- débito automático
- alerta de retiro

El sistema debe extraer de estos correos un conjunto de **eventos financieros normalizados** que puedan almacenarse y analizarse posteriormente.

En la versión inicial del sistema el alcance se limita a:

- Banco: **BAC**
- Tipo de notificación: **transacción con tarjeta**
- Etiqueta Gmail: **Transacciones**

---

## Decisión

El sistema utilizará una arquitectura de parsers **modular y extensible** organizada por banco y tipo de notificación.

La estructura general será:

```
parser/
├── base.py
└── bac/
    ├── classifier.py
    ├── transaction_notification.py
    └── patterns.py
```

Cada banco tendrá su propio módulo.

Cada tipo de notificación tendrá su propio parser independiente.

---

## Principios de diseño

### 1. Separación entre clasificación y parsing

El sistema separa dos responsabilidades:

**Clasificación**

Determinar:

- a qué banco pertenece el mensaje
- qué tipo de notificación representa

**Parsing**

Extraer los datos estructurados del mensaje.

Esta separación permite:

- mejorar mantenibilidad
- facilitar extensión del sistema
- reducir complejidad en parsers individuales

---

### 2. Parser base abstracto

Todos los parsers deben implementar un contrato común definido en:

```
parser/base.py
```

Este contrato establece las operaciones mínimas que debe soportar un parser.

Ejemplo conceptual:

```
class BaseParser(ABC):

    def can_parse(message: SourceMessage) -> bool:
        ...

    def parse(message: SourceMessage) -> FinancialEvent:
        ...
```

Responsabilidades:

- determinar si el parser puede procesar el mensaje
- extraer los campos requeridos
- producir un evento financiero normalizado

---

### 3. Clasificadores por banco

Cada banco tiene un **clasificador específico**.

Ubicación:

```
parser/<bank>/classifier.py
```

El clasificador analiza características del mensaje como:

- dirección del remitente
- dominio del remitente
- asunto del correo
- frases características
- estructura del HTML
- patrones de texto

Ejemplo de decisión:

```
if sender_domain == "baccredomatic.com":
    bank = BAC
```

El clasificador también determina el tipo de notificación.

---

### 4. Parsers específicos por tipo de notificación

Cada tipo de notificación se implementa como un parser independiente.

Ejemplo:

```
transaction_notification.py
```

Responsabilidad:

extraer campos estructurados de la notificación.

Campos definidos para la versión inicial:

| campo              | descripción            |
| ------------------ | ---------------------- |
| merchant           | comercio               |
| transaction_date   | fecha                  |
| card_brand         | marca de tarjeta       |
| card_last4         | últimos 4 dígitos      |
| authorization_code | código de autorización |
| transaction_type   | tipo de transacción    |
| amount             | monto                  |
| currency           | moneda                 |

---

### 5. Aislamiento de patrones

Los patrones de parsing se ubican en:

```
patterns.py
```

Esto incluye:

- expresiones regulares
- frases identificadoras
- selectores HTML
- fragmentos de texto relevantes

Separar los patrones del parser permite:

- modificar expresiones sin alterar lógica principal
- facilitar mantenimiento
- mejorar legibilidad

---

## Flujo de parsing

El proceso completo de parsing es el siguiente:

1. obtener `SourceMessage`
2. ejecutar clasificadores de banco
3. identificar tipo de notificación
4. seleccionar parser correspondiente
5. ejecutar parser
6. generar `FinancialEvent`

Si el parser falla:

- se registra un error
- el mensaje se etiqueta como `error`
- el mensaje permanece no leído

---

## Modelo de salida

El parser produce un evento financiero normalizado.

Ejemplo conceptual:

```json
{
  "bank": "BAC",
  "event_type": "card_transaction",
  "merchant": "AMPM",
  "transaction_date": "2026-03-15",
  "card_brand": "VISA",
  "card_last4": "1234",
  "authorization_code": "A82F3D",
  "transaction_type": "purchase",
  "amount": 12000,
  "currency": "CRC"
}
```

Este evento será persistido en la base de datos.

---

## Manejo de errores

Errores posibles incluyen:

- campo obligatorio no encontrado
- formato inesperado
- notificación desconocida
- cambios en estructura del correo

Cuando ocurre un error:

1. se genera un artefacto en `data/errors`
2. el mensaje se etiqueta como `error`
3. el mensaje permanece no leído

Esto permite revisión manual.

---

## Escalabilidad

La estrategia permite agregar nuevos bancos fácilmente.

Ejemplo:

```
parser/
├── bac/
├── bcr/
├── bncr/
└── scotia/
```

Dentro de cada banco se pueden agregar múltiples parsers:

```
parser/bac/
├── classifier.py
├── transaction_notification.py
├── debit_notification.py
└── payment_notification.py
```

---

## Relación con arquitectura hexagonal

Los parsers se implementan como **adaptadores outbound**.

Su función es traducir datos externos (correos) hacia modelos del dominio.

El dominio no debe depender de:

- expresiones regulares
- estructuras HTML
- formatos específicos de bancos

Los parsers encapsulan estas dependencias.

---

## Consecuencias

### Beneficios

- arquitectura extensible
- parsers pequeños y especializados
- separación clara de responsabilidades
- mayor mantenibilidad
- facilidad para agregar nuevos bancos

---

### Costos

- mayor número de archivos
- necesidad de mantener clasificadores
- mayor disciplina de diseño

Estos costos se consideran aceptables debido a la naturaleza heterogénea de las notificaciones bancarias.

---

## Alternativas consideradas

### Parser único

Una alternativa sería implementar un único parser que maneje todos los bancos y notificaciones.

Esta opción fue descartada porque:

- generaría archivos muy complejos
- dificultaría mantenimiento
- dificultaría agregar nuevos bancos
- aumentaría riesgo de regresiones

---

## Referencias

Eric Evans — Domain-Driven Design

Martin Fowler — Patterns of Enterprise Application Architecture

Alistair Cockburn — Hexagonal Architecture
<https://alistair.cockburn.us/hexagonal-architecture>

---

## Estado

Esta estrategia queda **aceptada** para la versión inicial del sistema.
