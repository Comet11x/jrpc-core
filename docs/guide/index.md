# What is jrpc-core?

**jrpc-core** is a lightweight Python library that implements the [JSON-RPC 2.0 specification](https://www.jsonrpc.org/specification) with two core layers:

| Layer | Module | Purpose |
|---|---|---|
| **Messages** | `jrpc_core.messages` | Pydantic models for requests, responses, notifications, and errors |
| **Dispatcher** | `jrpc_core.dispatcher` | Registry-based routing of incoming messages to handler callables |

## Design Principles

- **Type-safe** — every model is a Pydantic `BaseModel` with explicit field types and validators.
- **Functional** — error handling uses `Result` and `Option` from [pyfplib](https://pypi.org/project/pyfplib/) instead of exceptions.
- **Lightweight** — only depends on `pydantic` and `pyfplib`, no async runtime required.
- **Serialisable** — round-trips cleanly between Python objects and JSON strings.

## Architecture

```
Incoming JSON string
        │
        ▼
   try_parse()
        │
   ┌────┴────┐
   │         │
Request  Notification
   │         │
   ▼         ▼
JsonRpcDispatcher.__call__()
   │
   ├──► handler registry lookup
   │
   ▼
JsonRpcResponse
```

## Next Steps

- [Getting Started](/guide/getting-started) — install and run your first request
- [Messages API](/guide/messages) — full reference for all message models
- [Dispatcher API](/guide/dispatcher) — full reference for routing and handler registration
