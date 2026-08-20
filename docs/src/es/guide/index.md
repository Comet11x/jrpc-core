# ¿Qué es jrpc-core?

**jrpc-core** es una biblioteca Python ligera que implementa la [especificación JSON-RPC 2.0](https://www.jsonrpc.org/specification) con dos capas principales:

| Capa | Módulo | Propósito |
|---|---|---|
| **Mensajes** | `jrpc_core.messages` | Modelos Pydantic para solicitudes, respuestas, notificaciones y errores |
| **Dispatcher** | `jrpc_core.dispatcher` | Enrutamiento basado en registro de mensajes entrantes a llamadas de handler |

## Principios de Diseño

- **Type-safe** — cada modelo es un `BaseModel` de Pydantic con tipos de campo y validadores explícitos.
- **Funcional** — el manejo de errores usa `Result` y `Option` de [pyfplib](https://pypi.org/project/pyfplib/) en lugar de excepciones.
- **Ligero** — solo depende de `pydantic` y `pyfplib`, no requiere runtime async.
- **Serializable** — ida y vuelta limpia entre objetos Python y cadenas JSON.

## Arquitectura

```
Cadena JSON entrante
        │
        ▼
   try_parse()
        │
   ┌────┴────┐
   │         │
Solicitud  Notificación
   │         │
   ▼         ▼
JsonRpcDispatcher.__call__()
   │
   ├──► búsqueda en el registro de handlers
   │
   ▼
JsonRpcResponse
```

## Próximos Pasos

- [Primeros Pasos](/es/guide/getting-started) — instalación y primera solicitud
- [API de Mensajes](/es/guide/messages) — referencia completa de todos los modelos de mensaje
- [API de Dispatcher](/es/guide/dispatcher) — referencia completa de enrutamiento y registro de handlers
