# Was ist jrpc-core?

**jrpc-core** ist eine leichtgewichtige Python-Bibliothek, die die [JSON-RPC 2.0-Spezifikation](https://www.jsonrpc.org/specification) mit zwei Kernschichten implementiert:

| Schicht | Modul | Zweck |
|---|---|---|
| **Nachrichten** | `jrpc_core.messages` | Pydantic-Modelle für Anfragen, Antworten, Benachrichtigungen und Fehler |
| **Dispatcher** | `jrpc_core.dispatcher` | Registerbasierte Weiterleitung eingehender Nachrichten an Handler-Aufrufe |

## Designprinzipien

- **Typsicher** — jedes Modell ist ein Pydantic-`BaseModel` mit expliziten Feldtypen und Validatoren.
- **Funktional** — Fehlerbehandlung verwendet `Result` und `Option` aus [pyfplib](https://pypi.org/project/pyfplib/) statt Ausnahmen.
- **Leichtgewichtig** — hängt nur von `pydantic` und `pyfplib` ab, kein Async-Laufzeitumfeld erforderlich.
- **Serialisierbar** — sauberer Rückweg zwischen Python-Objekten und JSON-Strings.

## Architektur

```
Eingehender JSON-String
        │
        ▼
   try_parse()
        │
   ┌────┴────┐
   │         │
Anfrage  Benachrichtigung
   │         │
   ▼         ▼
JsonRpcDispatcher.__call__()
   │
   ├──► Handler-Register-Suche
   │
   ▼
JsonRpcResponse
```

## Nächste Schritte

- [Erste Schritte](/de/guide/getting-started) — Installation und erste Anfrage
- [Nachrichten-API](/de/guide/messages) — vollständige Referenz für alle Nachrichtenmodelle
- [Dispatcher-API](/de/guide/dispatcher) — vollständige Referenz für Routing und Handler-Registrierung
