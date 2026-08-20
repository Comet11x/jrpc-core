# Cos'è jrpc-core?

**jrpc-core** è una libreria Python leggera che implementa la [specifica JSON-RPC 2.0](https://www.jsonrpc.org/specification) con due livelli principali:

| Livello | Modulo | Scopo |
|---|---|---|
| **Messaggi** | `jrpc_core.messages` | Modelli Pydantic per richieste, risposte, notifiche ed errori |
| **Dispatcher** | `jrpc_core.dispatcher` | Instradamento basato su registro dei messaggi in arrivo verso handler |

## Principi di Progettazione

- **Type-safe** — ogni modello è un `BaseModel` di Pydantic con tipi di campo e validatori espliciti.
- **Funzionale** — la gestione degli errori utilizza `Result` e `Option` da [pyfplib](https://pypi.org/project/pyfplib/) invece delle eccezioni.
- **Leggero** — dipende solo da `pydantic` e `pyfplib`, non richiede runtime async.
- **Serializzabile** — percorso pulito tra oggetti Python e stringhe JSON.

## Architettura

```
Stringa JSON in arrivo
        │
        ▼
   try_parse()
        │
   ┌────┴────┐
   │         │
Richiesta  Notifica
   │         │
   ▼         ▼
JsonRpcDispatcher.__call__()
   │
   ├──► ricerca nel registro handler
   │
   ▼
JsonRpcResponse
```

## Prossimi Passi

- [Per Iniziare](/it/guide/getting-started) — installazione e prima richiesta
- [API Messaggi](/it/guide/messages) — riferimento completo per tutti i modelli di messaggio
- [API Dispatcher](/it/guide/dispatcher) — riferimento completo per l'instradamento e la registrazione degli handler
