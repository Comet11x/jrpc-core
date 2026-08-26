# API Messaggi

Tutte le primitive dei messaggi si trovano nel modulo `jrpc_core.messages`.

```python
from jrpc_core.messages import (
    JsonRpcRequest,
    JsonRpcNotification,
    JsonRpcResponse,
    JsonRpcError,
    JsonRpcErrorCode,
    JsonRpcVersion,
    try_parse,
)
```

---

## Alias di Tipo

### `JsonRpcId`

```python
JsonRpcId = str | int | float | None
```

Alias di tipo per l'identificatore di un messaggio JSON-RPC. Un identificatore valido è un `str`, `int`, `float` o `None`. La variante `None` è consentita solo nelle notifiche.

### `JsonRpcParams`

```python
JsonRpcParams = dict[str, Any] | list[Any] | None
```

Alias di tipo per i valori `params` di JSON-RPC. I parametri possono essere una mappa con nome (`dict`), una lista posizionale (`list`) o `None` quando omessi.

---

## `JsonRpcErrorCode`

```python
class JsonRpcErrorCode(Enum)
```

Enumerazione dei codici di errore standard JSON-RPC 2.0. Ogni membro corrisponde al codice intero definito dalla specifica o da estensioni comuni (`-32xxx` riservati, `-320xx` definiti dal server).

### Membri

| Membro | Valore | Descrizione |
|---|---|---|
| `ParseError` | `-32700` | Il server ha ricevuto JSON non valido. |
| `InternalError` | `-32603` | Si è verificato un errore JSON-RPC interno. |
| `InvalidParams` | `-32602` | I parametri inviati con il metodo non sono validi. |
| `MethodNotFound` | `-32601` | Il metodo non esiste o non è disponibile. |
| `InvalidRequest` | `-32600` | Il JSON inviato non è un oggetto richiesta valido. |
| `ExecutionError` | `-32000` | Si è verificato un errore di esecuzione definito dal server. |
| `ConversionError` | `-32001` | Si è verificato un errore di conversione definito dal server. |

### Metodi

#### `__int__() -> int`

Restituisce il valore intero di questo codice di errore.

```python
>>> int(JsonRpcErrorCode.ParseError)
-32700
```

#### `description() -> str`

Restituisce una descrizione leggibile di questo codice di errore.

```python
>>> JsonRpcErrorCode.ParseError.description()
'Parse error'
```

#### `default() -> JsonRpcErrorCode` *(static)*

Restituisce il codice di errore predefinito utilizzato quando nessun altro codice è appropriato. Restituisce `InternalError`.

```python
>>> JsonRpcErrorCode.default()
<JsonRpcErrorCode.InternalError: -32603>
```

#### `into(data: Any = None) -> JsonRpcError`

Crea un `JsonRpcError` da questo codice.

| Parametro | Tipo | Predefinito | Descrizione |
|---|---|---|---|
| `data` | `Any` | `None` | Payload extra opzionale allegato all'errore. |

**Restituisce:** Un nuovo `JsonRpcError` con questo codice e la sua descrizione.

```python
>>> err = JsonRpcErrorCode.ParseError.into()
>>> err.code
<JsonRpcErrorCode.ParseError: -32700>
>>> err.message
'Parse error'
```

---

## `JsonRpcVersion`

```python
class JsonRpcVersion(StrEnum)
```

Versioni del protocollo JSON-RPC supportate.

| Membro | Valore |
|---|---|
| `Version1` | `"1.0"` |
| `Version2` | `"2.0"` |

---

## `JsonRpcError`

```python
class JsonRpcError(BaseModel)
```

Un oggetto di errore JSON-RPC 2.0.

### Attributi

| Attributo | Tipo | Predefinito | Descrizione |
|---|---|---|---|
| `code` | `JsonRpcErrorCode \| int` | `JsonRpcErrorCode.InternalError` | Un codice di errore intero. |
| `message` | `str` | `"Something went wrong"` | Una breve descrizione leggibile. |
| `data` | `Any \| None` | `None` | Informazioni extra opzionali sull'errore. |

### Metodi

#### `default() -> JsonRpcError` *(static)*

Restituisce un errore predefinito con `JsonRpcErrorCode.InternalError`.

```python
>>> JsonRpcError.default()
JsonRpcError(code=<JsonRpcErrorCode.InternalError: -32603>, message='Something went wrong', data=None)
```

#### `from_data(*, data: Any, code: JsonRpcErrorCode = InternalError, message: str = ...) -> JsonRpcError` *(static)*

Crea un `JsonRpcError` da dati arbitrari con codice e messaggio espliciti.

| Parametro | Tipo | Predefinito | Descrizione |
|---|---|---|---|
| `data` | `Any` | *(obbligatorio)* | Payload extra allegato all'errore. |
| `code` | `JsonRpcErrorCode` | `InternalError` | Il codice di errore. |
| `message` | `str` | `InternalError.description()` | Una breve descrizione leggibile. |

**Restituisce:** Una nuova istanza di `JsonRpcError`.

```python
>>> JsonRpcError.from_data(data={"detail": "oops"})
JsonRpcError(code=<JsonRpcErrorCode.InternalError: -32603>, message='Internal error', data={'detail': 'oops'})
>>> JsonRpcError.from_data(data="bad", code=JsonRpcErrorCode.InvalidParams, message="invalid")
JsonRpcError(code=<JsonRpcErrorCode.InvalidParams: -32602>, message='invalid', data='bad')
```

#### `from_error(error: JsonRpcError | Any) -> JsonRpcError` *(static)*

Converte un valore arbitrario in un `JsonRpcError`. Se *error* è già un `JsonRpcError` viene restituito così com'è. Altrimenti la funzione tenta di estrarre un attributo `code` e costruisce un errore attorno ad esso, ricadendo su `JsonRpcErrorCode.InternalError`.

| Parametro | Tipo | Descrizione |
|---|---|---|
| `error` | `JsonRpcError \| Any` | Il valore da convertire. |

**Restituisce:** Un'istanza di `JsonRpcError`.

```python
>>> JsonRpcError.from_error(RuntimeError("oops"))
JsonRpcError(code=<JsonRpcErrorCode.InternalError: -32603>, message='Internal error', data=RuntimeError('oops'))
```

#### `try_from(value: Option[JsonRpcError | Any]) -> Option[JsonRpcError]` *(static)*

Tenta di convertire un `Option` in un errore.

| Parametro | Tipo | Descrizione |
|---|---|---|
| `value` | `Option[JsonRpcError \| Any]` | Un `Option` che può contenere un valore da convertire. |

**Restituisce:** `Some(JsonRpcError)` se *value* era `Some`, altrimenti `Nothing`.

```python
>>> from pyfplib import Some, Nothing
>>> JsonRpcError.try_from(Some(RuntimeError("x"))).is_some()
True
>>> JsonRpcError.try_from(Nothing()).is_some()
False
```

---

## `JsonRpcRequest`

```python
class JsonRpcRequest(BaseModel)
```

Un oggetto richiesta JSON-RPC 2.0. Contiene un nome `method`, un payload opzionale `params` e un `id` che il client utilizza per correlare la risposta.

### Attributi

| Attributo | Tipo | Predefinito | Descrizione |
|---|---|---|---|
| `method` | `str` | *(obbligatorio)* | Il nome della procedura remota da invocare. Deve essere una stringa non vuota. |
| `id` | `JsonRpcId` | `str(uuid4())` | Un identificatore univoco per questa richiesta (UUID generato automaticamente per predefinito). |
| `params` | `JsonRpcParams` | `None` | Argomenti posizionali o con nome opzionali per il metodo. |
| `jsonrpc` | `JsonRpcVersion` | `Version2` | La versione del protocollo. |

### Metodi

#### `try_from_dict(data: dict) -> Result[JsonRpcRequest, Exception]` *(classmethod)*

Tenta di costruire una richiesta da un dizionario semplice.

| Parametro | Tipo | Descrizione |
|---|---|---|
| `data` | `dict[str, Any]` | Un dizionario con i campi della richiesta JSON-RPC. |

**Restituisce:** `Ok(request)` in caso di successo, oppure `Err(exception)` in caso di errore di validazione.

```python
>>> JsonRpcRequest.try_from_dict({"method": "add", "id": 1}).is_ok()
True
```

#### `try_from_json(data: str) -> Result[JsonRpcRequest, Exception]` *(classmethod)*

Tenta di costruire una richiesta da una stringa JSON.

| Parametro | Tipo | Descrizione |
|---|---|---|
| `data` | `str` | Una stringa codificata JSON che rappresenta una richiesta. |

**Restituisce:** `Ok(request)` in caso di successo, oppure `Err(exception)` in caso di errore di parsing/validazione.

```python
>>> JsonRpcRequest.try_from_json('{"method":"add","id":1}').is_ok()
True
```

#### `to_dict() -> dict[str, Any]`

Serializza la richiesta in un dizionario semplice. La chiave `params` viene omessa quando è `None`.

**Restituisce:** Un dizionario adatto alla serializzazione JSON.

```python
>>> JsonRpcRequest(method="add", params=[1, 2]).to_dict()
{'method': 'add', 'id': '<uuid>', 'params': [1, 2], 'jsonrpc': '2.0'}
```

#### `to_json() -> str`

Serializza la richiesta in una stringa JSON.

**Restituisce:** Una rappresentazione JSON compatta di questa richiesta.

#### `serialize() -> str`

Serializza la richiesta in una stringa JSON. Alias di `to_json()`.

**Restituisce:** Una rappresentazione JSON compatta di questa richiesta.

#### `into(result: Result[Any, JsonRpcError]) -> JsonRpcResponse`

Crea un `JsonRpcResponse` dal risultato di un handler. Accetta un `Result`, un `JsonRpcError` o un valore grezzo.

| Parametro | Tipo | Descrizione |
|---|---|---|
| `result` | `Result[Any, JsonRpcError]` | L'esito dell'elaborazione di questa richiesta. |

**Restituisce:** Una risposta contenente il risultato decodificato o l'errore.

```python
>>> from pyfplib import Result
>>> req = JsonRpcRequest(method="add", id=1)
>>> req.into(Result.ok(3))
JsonRpcResponse(id=1, result=3, error=None, ...)
```

---

## `JsonRpcNotification`

```python
class JsonRpcNotification(BaseModel)
```

Un oggetto notifica JSON-RPC 2.0. Identico a una richiesta ma omette il campo `id`, indicando che non è attesa alcuna risposta dal server.

### Attributi

| Attributo | Tipo | Predefinito | Descrizione |
|---|---|---|---|
| `method` | `str` | *(obbligatorio)* | Il nome dell'evento o della procedura annunciata. Deve essere una stringa non vuota. |
| `params` | `JsonRpcParams` | `None` | Argomenti posizionali o con nome opzionali. |
| `jsonrpc` | `JsonRpcVersion` | `Version2` | La versione del protocollo. |

::: warning
Una notifica **non** deve contenere un campo `id`. Tentare di costruirne una con un `id` genera un errore di validazione.
:::

### Metodi

#### `try_from_dict(data: dict) -> Result[JsonRpcNotification, Exception]` *(classmethod)*

Tenta di costruire una notifica da un dizionario semplice.

| Parametro | Tipo | Descrizione |
|---|---|---|
| `data` | `dict[str, Any]` | Un dizionario con i campi della notifica JSON-RPC. |

**Restituisce:** `Ok(notification)` in caso di successo, oppure `Err(exception)` in caso di errore di validazione.

#### `try_from_json(data: str) -> Result[JsonRpcNotification, Exception]` *(classmethod)*

Tenta di costruire una notifica da una stringa JSON.

| Parametro | Tipo | Descrizione |
|---|---|---|
| `data` | `str` | Una stringa codificata JSON che rappresenta una notifica. |

**Restituisce:** `Ok(notification)` in caso di successo, oppure `Err(exception)` in caso di errore di parsing/validazione.

#### `to_dict() -> dict[str, Any]`

Serializza la notifica in un dizionario semplice. La chiave `params` viene omessa quando è `None`.

**Restituisce:** Un dizionario adatto alla serializzazione JSON.

#### `to_json() -> str`

Serializza la notifica in una stringa JSON.

**Restituisce:** Una rappresentazione JSON compatta di questa notifica.

#### `serialize() -> str`

Serializza la notifica in una stringa JSON. Alias di `to_json()`.

**Restituisce:** Una rappresentazione JSON compatta di questa notifica.

---

## `JsonRpcResponse`

```python
class JsonRpcResponse(BaseModel)
```

Un oggetto risposta JSON-RPC 2.0. Esattamente uno tra `result` e `error` deve essere impostato. L'`id` corrisponde all'`id` della richiesta originale.

### Attributi

| Attributo | Tipo | Predefinito | Descrizione |
|---|---|---|---|
| `id` | `JsonRpcId` | *(obbligatorio)* | L'identificatore della richiesta a cui questa risposta corrisponde. |
| `result` | `Any` | `None` | Il valore di ritorno quando il metodo è stato eseguito con successo. |
| `error` | `JsonRpcError \| None` | `None` | Un `JsonRpcError` quando il metodo ha fallito. |
| `jsonrpc` | `JsonRpcVersion` | `Version2` | La versione del protocollo. |

::: warning
Una risposta deve avere **o** un `result` **o** un `error`, non entrambi. Tentare di impostarne entrambi genera un errore di validazione.
:::

### Metodi

#### `from_result(id, result) -> JsonRpcResponse` *(static)*

Costruisce una risposta da un `Result`.

| Parametro | Tipo | Descrizione |
|---|---|---|
| `id` | `JsonRpcId` | L'identificatore della richiesta da ripetere nella risposta. |
| `result` | `Result[Any, JsonRpcError]` | L'esito dell'handler. |

**Restituisce:** Un `JsonRpcResponse` completamente costruito.

```python
>>> from pyfplib import Result
>>> JsonRpcResponse.from_result(1, Result.ok("data"))
JsonRpcResponse(id=1, result='data', error=None, ...)
>>> JsonRpcResponse.from_result(2, Result.err(JsonRpcError(code=JsonRpcErrorCode.InternalError)))
JsonRpcResponse(id=2, result=None, error=JsonRpcError(...), ...)
```

#### `from_jrpc_error(id, error) -> JsonRpcResponse` *(static)*

Costruisce una risposta di errore.

| Parametro | Tipo | Descrizione |
|---|---|---|
| `id` | `JsonRpcId` | L'identificatore della richiesta da ripetere nella risposta. |
| `error` | `JsonRpcError \| Exception` | L'errore da includere. |

**Restituisce:** Un `JsonRpcResponse` con solo `error` impostato.

#### `from_jrpc_result(id, result) -> JsonRpcResponse` *(static)*

Costruisce una risposta di successo.

| Parametro | Tipo | Descrizione |
|---|---|---|
| `id` | `JsonRpcId` | L'identificatore della richiesta da ripetere nella risposta. |
| `result` | `Any` | Il valore di ritorno del metodo. |

**Restituisce:** Un `JsonRpcResponse` con solo `result` impostato.

#### `try_from_dict(data: dict) -> Result[JsonRpcResponse, Exception]` *(static)*

Tenta di costruire una risposta da un dizionario semplice.

| Parametro | Tipo | Descrizione |
|---|---|---|
| `data` | `dict[str, Any]` | Un dizionario con i campi della risposta JSON-RPC. |

**Restituisce:** `Ok(response)` in caso di successo, oppure `Err(exception)` in caso di errore di validazione.

#### `try_from_json(data: str) -> Result[JsonRpcResponse, Exception]` *(static)*

Tenta di costruire una risposta da una stringa JSON.

| Parametro | Tipo | Descrizione |
|---|---|---|
| `data` | `str` | Una stringa codificata JSON che rappresenta una risposta. |

**Restituisce:** `Ok(response)` in caso di successo, oppure `Err(exception)` in caso di errore di parsing/validazione.

#### `to_dict() -> dict[str, Any]`

Serializza la risposta in un dizionario semplice. Quando è presente un `error` la chiave `result` viene rimossa e il codice di errore viene convertito in `int`. Quando è presente `result` la chiave `error` viene rimossa.

**Restituisce:** Un dizionario adatto alla serializzazione JSON.

#### `to_json() -> str`

Serializza la risposta in una stringa JSON.

**Restituisce:** Una rappresentazione JSON compatta di questa risposta.

#### `serialize() -> str`

Serializza la risposta in una stringa JSON. Alias di `to_json()`.

**Restituisce:** Una rappresentazione JSON compatta di questa risposta.

---

## `try_parse()`

```python
def try_parse(data: str) -> Result[JsonRpcResponse | JsonRpcNotification | JsonRpcRequest, JsonRpcError]
```

Tenta di analizzare una stringa JSON come messaggio JSON-RPC. La funzione prova prima a parsare come `JsonRpcResponse`; se fallisce ricade su `JsonRpcNotification`; se fallisce di nuovo ricade su `JsonRpcRequest`. Se tutti i tentativi falliscono, viene restituito l'errore di parsing del tentativo di richiesta.

| Parametro | Tipo | Descrizione |
|---|---|---|
| `data` | `str` | Una stringa codificata JSON. |

**Restituisce:** `Ok(response | notification | request)` in caso di successo, oppure `Err(JsonRpcError)` contenente l'errore di parsing.

```python
>>> try_parse('{"jsonrpc":"2.0","method":"add","id":1}')
Result.ok(JsonRpcRequest(method='add', id=1, ...))
```
