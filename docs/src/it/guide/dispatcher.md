# API Dispatcher

Il livello dispatcher si trova nel modulo `jrpc_core.dispatcher`.

```python
from jrpc_core.dispatcher import (
    JsonRpcDispatcher,
    JsonRpcMethodWrapper,
    JsonRpcHandlerCollection,
    JsonRpcResponseCtorWrapper,
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
    validator: Callable[..., Option[JsonRpcError] | bool] | None = None,
    converter: Callable[..., Option[Any] | Result[Any, Exception | JsonRpcError] | Any] | None = None,
)
```

| Parametro | Tipo | Predefinito | Descrizione |
|---|---|---|---|
| `name` | `str` | *(obbligatorio)* | Il nome del metodo JSON-RPC. |
| `method` | `Callable[..., Any]` | *(obbligatorio)* | Il callable da invocare quando questo metodo viene dispatchato. |
| `validator` | `Callable[..., Option[JsonRpcError] \| bool] \| None` | `None` | Un callable opzionale che riceve i `params` analizzati e restituisce un segnale di rifiuto. |
| `converter` | `Callable[..., Option[Any] \| Result[Any, Exception \| JsonRpcError] \| Any] \| None` | `None` | Un callable opzionale che trasforma i `params` analizzati prima dell'invocazione del metodo. |

### Protocollo Validatore

Ogni validatore riceve i `params` analizzati e può restituire:

| Valore di ritorno | Comportamento |
|---|---|
| `Some(JsonRpcError)` | Rifiuta con quell'errore wrappato in `InvalidParams` |
| `Some(Exception)` | Rifiuta con quell'errore wrappato in `InvalidParams` |
| `False` | Rifiuta con un errore generico `InvalidParams` |
| `Exception` o `JsonRpcError` | Rifiuta con quell'errore direttamente |
| `True`, `None` o qualsiasi altro valore truthy | Accetta — prosegue con la conversione o con l'invocazione del metodo |

### Protocollo Convertitore

Il convertitore riceve il payload `params` grezzo e può restituire:

| Valore di ritorno | Comportamento |
|---|---|
| `Some(value)` | Usa `value` come argomento del metodo |
| `Nothing()` | Rifiuta con `ConversionError` |
| `Ok(value)` | Usa `value` come argomento del metodo |
| `Err(reason)` | Rifiuta con `ConversionError`, allegando `reason` ai dati |
| Qualsiasi altro valore | Usa il valore direttamente come argomento del metodo |
| Solleva `Exception` | Rifiuta con `ConversionError`, allegando l'eccezione ai dati |

### Attributi

| Attributo | Tipo | Descrizione |
|---|---|---|
| `name` | `str` | Il nome del metodo JSON-RPC sotto cui questo wrapper è registrato. |

### Metodi

#### `__hash__() -> int`

Restituisce un hash basato sul nome del metodo. Due wrapper con lo stesso nome hanno lo stesso hash.

#### `__eq__(other) -> bool`

Confronta due wrapper per nome del metodo.

#### `__call__(params: Option[Any]) -> Result[Any, JsonRpcError]`

Esegue il metodo wrappato con parametri opzionali. I validatori vengono eseguiti prima del metodo, poi la conversione; se uno qualsiasi dei due passaggi rifiuta i parametri, la chiamata si interrompe con un `Err`.

| Parametro | Tipo | Descrizione |
|---|---|---|
| `params` | `Option[Any]` | Un `Option` contenente i parametri del metodo. `Some` significa che i parametri sono stati forniti; `None` significa nessun parametro. |

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
JsonRpcDispatcher(
    response_handler: Callable[[JsonRpcResponse], None] | None = None,
)
```

| Parametro | Tipo | Predefinito | Descrizione |
|---|---|---|---|
| `response_handler` | `Callable[[JsonRpcResponse], None] \| None` | `None` | Callback opzionale invocata quando un `JsonRpcResponse` viene dispatchato direttamente. |

### Attributi di Classe

| Attributo | Tipo | Descrizione |
|---|---|---|
| `ERROR_CASE` | `JsonRpcResponseCtorWrapper.State` | Selettore esito per le risposte di errore. |
| `RESULT_CASE` | `JsonRpcResponseCtorWrapper.State` | Selettore esito per i risultati di successo. |
| `BOTH_CASES` | `JsonRpcResponseCtorWrapper._When` | Selettore esito che corrisponde a entrambi gli esiti. |

### Attributi

| Attributo | Tipo | Descrizione |
|---|---|---|
| `request_handler_registry` | `JsonRpcHandlerCollection` | Registro degli handler per le richieste. |
| `notification_handler_registry` | `JsonRpcHandlerCollection` | Registro degli handler per le notifiche. |

### Metodi

#### `emplace_request_handler(*, name, method, validator=None, converter=None) -> bool`

Registra un handler per le richieste in una singola chiamata. Funzione di comodo per `request_handler_registry.add(JsonRpcMethodWrapper(...))`.

| Parametro | Tipo | Predefinito | Descrizione |
|---|---|---|---|
| `name` | `str` | *(obbligatorio)* | Il nome del metodo JSON-RPC. |
| `method` | `Callable[..., Any]` | *(obbligatorio)* | Il callable da invocare quando dispatchato. |
| `validator` | `Callable[..., Option[JsonRpcError] \| bool] \| None` | `None` | Validatore opzionale dei parametri. |
| `converter` | `Callable[..., Option[Any] \| Result[Any, Exception \| JsonRpcError] \| Any] \| None` | `None` | Convertitore opzionale dei parametri. |

**Restituisce:** `True` se registrato per la prima volta, `False` se il nome esisteva già.

#### `emplace_notification_handler(*, name, method, validator=None, converter=None) -> bool`

Registra un handler per le notifiche in una singola chiamata. Funzione di comodo per `notification_handler_registry.add(JsonRpcMethodWrapper(...))`.

| Parametro | Tipo | Predefinito | Descrizione |
|---|---|---|---|
| `name` | `str` | *(obbligatorio)* | Il nome del metodo JSON-RPC. |
| `method` | `Callable[..., Any]` | *(obbligatorio)* | Il callable da invocare quando dispatchato. |
| `validator` | `Callable[..., Option[JsonRpcError] \| bool] \| None` | `None` | Validatore opzionale dei parametri. |
| `converter` | `Callable[..., Option[Any] \| Result[Any, Exception \| JsonRpcError] \| Any] \| None` | `None` | Convertitore opzionale dei parametri. |

**Restituisce:** `True` se registrato per la prima volta, `False` se il nome esisteva già.

#### `emplace_custom_response_ctor(method, ctor, *states)`

Registra un costruttore di risposte personalizzato per *method*.

| Parametro | Tipo | Descrizione |
|---|---|---|
| `method` | `str` | Il nome del metodo JSON-RPC a cui il costruttore si applica. |
| `ctor` | `Callable[..., JsonRpcResponse]` | Callable che costruisce un `JsonRpcResponse`. |
| `*states` | `JsonRpcResponseCtorWrapper.State` | Membri di stato opzionali che limitano quando il *ctor* viene usato. |

#### `add_custom_response_ctor(ctor: JsonRpcResponseCtorWrapper)`

Registra un costruttore di risposte personalizzato pre-costruito. Sostituisce qualsiasi costruttore precedentemente registrato per lo stesso metodo.

| Parametro | Tipo | Descrizione |
|---|---|---|
| `ctor` | `JsonRpcResponseCtorWrapper` | Il wrapper che lega un costruttore a un nome di metodo. |

#### `__call__(data) -> Option[Result[JsonRpcResponse, JsonRpcError]]`

Dispatcha un messaggio JSON-RPC.

| Parametro | Tipo | Descrizione |
|---|---|---|
| `data` | `str \| JsonRpcRequest \| JsonRpcNotification \| JsonRpcResponse \| Result[...]` | Una stringa JSON, un `JsonRpcRequest`, un `JsonRpcNotification`, un `JsonRpcResponse` o un `Result`. |

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

#### `try_parse(data: str) -> Result[JsonRpcResponse | JsonRpcRequest | JsonRpcNotification, JsonRpcError]` *(classmethod)*

Tenta di analizzare una stringa JSON in una risposta, richiesta o notifica. Prima prova con `JsonRpcResponse`; in caso di fallimento ricade su `JsonRpcNotification`; in caso di fallimento ricade su `JsonRpcRequest`.

| Parametro | Tipo | Descrizione |
|---|---|---|
| `data` | `str` | Una stringa codificata JSON. |

**Restituisce:** `Ok(response | notification | request)` in caso di successo, oppure `Err(JsonRpcError)` in caso di errore di parsing.

---

## `JsonRpcResponseCtorWrapper`

```python
class JsonRpcResponseCtorWrapper
```

Lega un costruttore personalizzato di `JsonRpcResponse` a un nome di metodo. Il wrapper registra *quando* il costruttore si applica — risultati di successo, errori o entrambi — in modo che il dispatcher possa scegliere il tipo di risposta giusto per ciascun esito.

### Costruttore

```python
JsonRpcResponseCtorWrapper(
    method: str,
    ctor: Callable[..., JsonRpcResponse],
    *states: JsonRpcResponseCtorWrapper.State,
)
```

| Parametro | Tipo | Predefinito | Descrizione |
|---|---|---|---|
| `method` | `str` | *(obbligatorio)* | Il nome del metodo JSON-RPC a cui il costruttore si applica. |
| `ctor` | `Callable[..., JsonRpcResponse]` | *(obbligatorio)* | Callable che riceve argomenti keyword (`id`, `result` o `error`, e `jsonrpc`) e restituisce un `JsonRpcResponse`. |
| `*states` | `State` | Entrambi gli esiti | Membri `State` opzionali che limitano quando il *ctor* viene usato. |

### Classe Interna: `State`

```python
class State(Enum)
```

Selettore esito che controlla quando un costruttore viene applicato.

| Membro | Valore | Descrizione |
|---|---|---|
| `Result` | `1` | Il costruttore gestisce i risultati di successo. |
| `Error` | `2` | Il costruttore gestisce le risposte di errore. |

### Attributi

| Attributo | Tipo | Descrizione |
|---|---|---|
| `method` | `str` | Il nome del metodo JSON-RPC a cui questo costruttore è legato. |
| `when` | `_When` | Il selettore esito per questo costruttore. |
