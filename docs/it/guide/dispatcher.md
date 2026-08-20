# API Dispatcher

Il livello dispatcher si trova nel modulo `jrpc_core.dispatcher`.

```python
from jrpc_core.dispatcher import (
    JsonRpcDispatcher,
    JsonRpcMethodWrapper,
    JsonRpcHandlerCollection,
)
```

---

## `JsonRpcMethodWrapper`

```python
class JsonRpcMethodWrapper
```

Wrappa un callable come metodo JSON-RPC con validatori di parametri opzionali.

### Costruttore

```python
JsonRpcMethodWrapper(
    *,
    name: str,
    method: Callable[..., Any],
    validators: list[Callable[..., Option[JsonRpcError]]] | None = None,
)
```

| Parametro | Tipo | Predefinito | Descrizione |
|---|---|---|---|
| `name` | `str` | *(obbligatorio)* | Il nome del metodo JSON-RPC. |
| `method` | `Callable[..., Any]` | *(obbligatorio)* | Il callable da invocare quando questo metodo viene dispatchato. |
| `validators` | `list[Callable[..., Option[JsonRpcError]]] \| None` | `None` | Una lista opzionale di callable che ricevono i `params` analizzati e restituiscono un segnale di rifiuto. |

### Protocollo Validatore

Ogni validatore riceve i `params` analizzati e può restituire:

| Valore di ritorno | Comportamento |
|---|---|
| `Some(JsonRpcError)` o `Some(Exception)` | Rifiuta con quell'errore wrappato in `InvalidParams` |
| `False` | Rifiuta con un errore generico `InvalidParams` |
| `Exception` o `JsonRpcError` | Rifiuta con quell'errore direttamente |
| `True`, `None` o qualsiasi altro valore truthy | Accetta — prosegue con il validatore successivo o con l'invocazione del metodo |

### Attributi

| Attributo | Tipo | Descrizione |
|---|---|---|
| `name` | `str` | Il nome del metodo JSON-RPC sotto cui questo wrapper è registrato. |

### Metodi

#### `__hash__() -> int`

Restituisce un hash basato sul nome del metodo. Due wrapper con lo stesso nome hanno lo stesso hash.

#### `__eq__(other) -> bool`

Confronta due wrapper per nome del metodo.

#### `__call__(args: Option[Any]) -> Result[Any, JsonRpcError]`

Esegue il metodo wrappato con parametri opzionali. I validatori vengono eseguiti prima del metodo. Se un validatore rifiuta i parametri, la chiamata si interrompe con un `Err`.

| Parametro | Tipo | Descrizione |
|---|---|---|
| `args` | `Option[Any]` | Un `Option` contenente i parametri del metodo. `Some` significa che i parametri sono stati forniti; `None` significa nessun parametro. |

**Restituisce:** `Ok(result)` in caso di successo, oppure `Err(JsonRpcError)` in caso di errore.

```python
>>> from pyfplib import Some, Nothing, Result
>>> wrapper = JsonRpcMethodWrapper(name="add", method=lambda a: a[0] + a[1])
>>> wrapper(Some([1, 2]))
Result.ok(3)
>>> wrapper(Nothing())
Result.ok(...)  # calls method with no args
```

---

## `JsonRpcHandlerCollection`

```python
class JsonRpcHandlerCollection
```

Un registro di istanze `JsonRpcMethodWrapper` indicizzate per nome del metodo.

### Costruttore

```python
JsonRpcHandlerCollection()
```

Inizializza una collezione di handler vuota.

### Metodi

#### `add(method: JsonRpcMethodWrapper) -> bool`

Registra un method wrapper. Se un metodo con lo stesso nome esiste già, la chiamata non ha effetto.

| Parametro | Tipo | Descrizione |
|---|---|---|
| `method` | `JsonRpcMethodWrapper` | Il wrapper da registrare. |

**Restituisce:** `True` se il metodo è stato registrato per la prima volta, `False` se esisteva già.

```python
>>> collection = JsonRpcHandlerCollection()
>>> wrapper = JsonRpcMethodWrapper(name="add", method=lambda a: a)
>>> collection.add(wrapper)
True
>>> collection.add(wrapper)  # duplicate
False
```

#### `try_get(name: str) -> Option[JsonRpcMethodWrapper]`

Cerca un metodo per nome.

| Parametro | Tipo | Descrizione |
|---|---|---|
| `name` | `str` | Il nome del metodo JSON-RPC. |

**Restituisce:** `Some(wrapper)` se trovato, altrimenti `Nothing`.

#### `exists(name: str) -> bool`

Verifica se un metodo è registrato.

| Parametro | Tipo | Descrizione |
|---|---|---|
| `name` | `str` | Il nome del metodo JSON-RPC. |

**Restituisce:** `True` se esiste un wrapper con quel nome.

#### `remove_by_name(name: str) -> bool`

Rimuove un metodo per nome.

| Parametro | Tipo | Descrizione |
|---|---|---|
| `name` | `str` | Il nome del metodo JSON-RPC da rimuovere. |

**Restituisce:** `True` se il metodo esisteva ed è stato rimosso, `False` altrimenti.

#### `remove(method: str | JsonRpcMethodWrapper) -> bool`

Rimuove un metodo per nome o istanza di wrapper.

| Parametro | Tipo | Descrizione |
|---|---|---|
| `method` | `str \| JsonRpcMethodWrapper` | O una stringa con il nome del metodo o un `JsonRpcMethodWrapper`. |

**Restituisce:** `True` se il metodo esisteva ed è stato rimosso, `False` altrimenti.

```python
>>> collection = JsonRpcHandlerCollection()
>>> wrapper = JsonRpcMethodWrapper(name="add", method=lambda a: a)
>>> collection.add(wrapper)
True
>>> collection.remove("add")
True
>>> collection.remove("add")
False
```

---

## `JsonRpcDispatcher`

```python
class JsonRpcDispatcher
```

Instrada i messaggi JSON-RPC in arrivo verso gli handler registrati. Mantiene registri separati per le richieste (che attendono una risposta) e le notifiche (fire-and-forget).

### Costruttore

```python
JsonRpcDispatcher()
```

Inizializza il dispatcher con registri di handler vuoti.

### Attributi

| Attributo | Tipo | Descrizione |
|---|---|---|
| `request_handler_registry` | `JsonRpcHandlerCollection` | Registro degli handler per le richieste. |
| `notification_handler_registry` | `JsonRpcHandlerCollection` | Registro degli handler per le notifiche. |

### Metodi

#### `__call__(data: str | JsonRpcRequest | JsonRpcNotification) -> Option[Result[JsonRpcResponse, JsonRpcError]]`

Dispatcha un messaggio JSON-RPC.

| Parametro | Tipo | Descrizione |
|---|---|---|
| `data` | `str \| JsonRpcRequest \| JsonRpcNotification` | Una stringa JSON, un `JsonRpcRequest` o un `JsonRpcNotification`. |

**Restituisce:**

| Ingresso | Handler trovato | Handler non trovato |
|---|---|---|
| `str` (parsing ok) | Delega all'elaborazione richiesta/notifica | — |
| `str` (parsing fallito) | `Some(Err(ParseError))` | — |
| `JsonRpcRequest` | `Some(Ok(response))` | `Some(Err(MethodNotFound))` via risposta |
| `JsonRpcNotification` | `Nothing` (successo) | `Some(Err(MethodNotFound))` |
| Tipo sconosciuto | `Some(Err(InternalError))` | — |

```python
>>> from pyfplib import Some, Ok
>>> dispatcher = JsonRpcDispatcher()
>>> dispatcher.request_handler_registry.add(
...     JsonRpcMethodWrapper(name="add", method=lambda a: a[0] + a[1])
... )
True
>>> result = dispatcher(JsonRpcRequest(method="add", params=[1, 2], id=1))
>>> result.unwrap().unwrap().result
3
```

#### `try_parse(data: str) -> Result[JsonRpcRequest | JsonRpcNotification, JsonRpcError]` *(classmethod)*

Tenta di analizzare una stringa JSON in una richiesta o notifica. Prima prova con `JsonRpcRequest`; in caso di fallimento ricade su `JsonRpcNotification`.

| Parametro | Tipo | Descrizione |
|---|---|---|
| `data` | `str` | Una stringa codificata JSON. |

**Restituisce:** `Ok(request | notification)` in caso di successo, oppure `Err(JsonRpcError)` in caso di errore di parsing.
