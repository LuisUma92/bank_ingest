# bank_ingest

Sistema de extraccion automatizada de eventos financieros desde correos electronicos bancarios.

## Objetivo

Automatizar la captura de transacciones financieras notificadas por correo electronico, extrayendo datos estructurados y persistiendolos en una base de datos local.

El pipeline completo:

1. Consulta Gmail por mensajes etiquetados como **Transacciones**
2. Clasifica el banco y tipo de notificacion
3. Extrae campos financieros estructurados (comercio, monto, tarjeta, fecha, etc.)
4. Persiste el evento en SQLite
5. Marca el correo segun el resultado (`parsed` o `error`)

## Arquitectura

El sistema utiliza **arquitectura hexagonal (Ports and Adapters)** con principios de Domain-Driven Design.

```
adapters → application → domain
```

| Capa | Responsabilidad |
|------|----------------|
| **domain** | Modelo del problema: entidades, value objects, ports (interfaces) |
| **application** | Casos de uso que orquestan el pipeline de procesamiento |
| **adapters** | Integracion con sistemas externos (Gmail, SQLite, filesystem) |
| **shared** | Utilidades comunes (fechas, montos, texto) |

Principio fundamental: **el dominio nunca depende de infraestructura externa**.

### Parsers

Los parsers se organizan por banco y tipo de notificacion, permitiendo agregar nuevos bancos sin modificar el sistema existente.

```
parser/
├── base.py          # Contrato comun (ABC)
├── registry.py      # Registro de parsers por (banco, tipo)
└── bac/
    ├── classifier.py
    ├── patterns.py
    └── transaction_notification.py
```

## Version inicial

- **Banco**: BAC Credomatic
- **Tipo**: Notificacion de transaccion de tarjeta
- **Campos**: comercio, fecha, marca de tarjeta, ultimos 4 digitos, codigo de autorizacion, tipo de transaccion, monto, moneda

## Requisitos

- Python >= 3.12
- Credenciales OAuth2 de Gmail API (`credentials.json`)

## Instalacion

```bash
uv sync
```

## Uso

```bash
bank-ingest --help
```

## Tests

```bash
pytest
```

## Decisiones arquitectonicas

Documentadas en [`ADR/`](ADR/):

| ADR | Tema |
|-----|------|
| 0000 | Estructura del proyecto |
| 0001 | Arquitectura hexagonal |
| 0002 | Gmail como fuente de ingestion |
| 0003 | Politica de almacenamiento local |
| 0004 | Estrategia de parsers |
| 0005 | Bootstrap y dependency injection |
| 0006 | Parser registry |
| 0007 | Processing state port |
