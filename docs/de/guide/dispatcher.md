# Dispatcher-API

Die Dispatcher-Schicht befindet sich im `jrpc_core.dispatcher` Modul.

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

Verpackt einen Aufrufbaren als JSON-RPC-Methode mit optionalen Parametervalidatoren.

### Konstruktor

```python
JsonRpcMethodWrapper(
    *,
    name: str,
    method: Callable[..., Any],
    validators: list[Callable[..., Option[JsonRpcError]]] | None = None,
)
```

| Parameter | Typ | Standard | Beschreibung |
|---|---|---|---|
| `name` | `str` | *(erforderlich)* | Der JSON-RPC-Methodenname. |
| `method` | `Callable[..., Any]` | *(erforderlich)* | Der Aufrufbare, der aufgerufen wird, wenn diese Methode dispatched wird. |
| `validators` | `list[Callable[..., Option[JsonRpcError]]] \| None` | `None` | Eine optionale Liste von Aufrufbaren, die die geparsten `params` erhalten und ein Ablehnungssignal zurückgeben. |

### Validator-Protokoll

Jeder Validator erhält die geparsten `params` und kann zurückgeben:

| Rückgabewert | Verhalten |
|---|---|
| `Some(JsonRpcError)` oder `Some(Exception)` | Lehnt mit diesem Fehler ab, verpackt in `InvalidParams` |
| `False` | Lehnt mit einem allgemeinen `InvalidParams`-Fehler ab |
| `Exception` oder `JsonRpcError` | Lehnt mit diesem Fehler direkt ab |
| `True`, `None` oder jeder andere wahre Wert | Akzeptiert — fährt mit dem nächsten Validator oder der Methodenausführung fort |

### Attribute

| Attribut | Typ | Beschreibung |
|---|---|---|
| `name` | `str` | Der JSON-RPC-Methodenname, unter dem dieser Wrapper registriert ist. |

### Methoden

#### `__hash__() -> int`

Gibt einen Hash basierend auf dem Methodennamen zurück. Zwei Wrapper mit demselben Namen haben denselben Hash.

#### `__eq__(other) -> bool`

Vergleicht zwei Wrapper nach Methodennamen.

#### `__call__(args: Option[Any]) -> Result[Any, JsonRpcError]`

Führt die verpackte Methode mit optionalen Parametern aus. Validatoren werden vor der Methode ausgeführt. Wenn ein Validator die Parameter ablehnt, wird der Aufruf mit einem `Err` abgebrochen.

| Parameter | Typ | Beschreibung |
|---|---|---|
| `args` | `Option[Any]` | Ein `Option`, das die Methodenparameter enthält. `Some` bedeutet, dass Parameter bereitgestellt wurden; `None` bedeutet keine. |

**Gibt zurück:** `Ok(result)` bei Erfolg oder `Err(JsonRpcError)` bei Fehlschlag.

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

Ein Register von `JsonRpcMethodWrapper`-Instanzen, nach Methodennamen geordnet.

### Konstruktor

```python
JsonRpcHandlerCollection()
```

Initialisiert eine leere Handler-Sammlung.

### Methoden

#### `add(method: JsonRpcMethodWrapper) -> bool`

Registriert einen Methoden-Wrapper. Wenn bereits eine Methode mit demselben Namen existiert, ist der Aufruf ein No-Op.

| Parameter | Typ | Beschreibung |
|---|---|---|
| `method` | `JsonRpcMethodWrapper` | Der zu registrierende Wrapper. |

**Gibt zurück:** `True`, wenn die Methode neu registriert wurde, `False`, wenn sie bereits existierte.

```python
>>> collection = JsonRpcHandlerCollection()
>>> wrapper = JsonRpcMethodWrapper(name="add", method=lambda a: a)
>>> collection.add(wrapper)
True
>>> collection.add(wrapper)  # duplicate
False
```

#### `try_get(name: str) -> Option[JsonRpcMethodWrapper]`

Sucht eine Methode nach Name.

| Parameter | Typ | Beschreibung |
|---|---|---|
| `name` | `str` | Der JSON-RPC-Methodenname. |

**Gibt zurück:** `Some(wrapper)` wenn gefunden, andernfalls `Nothing`.

#### `exists(name: str) -> bool`

Prüft, ob eine Methode registriert ist.

| Parameter | Typ | Beschreibung |
|---|---|---|
| `name` | `str` | Der JSON-RPC-Methodenname. |

**Gibt zurück:** `True`, wenn ein Wrapper mit diesem Namen existiert.

#### `remove_by_name(name: str) -> bool`

Entfernt eine Methode nach Name.

| Parameter | Typ | Beschreibung |
|---|---|---|
| `name` | `str` | Der zu entfernende JSON-RPC-Methodenname. |

**Gibt zurück:** `True`, wenn die Methode existierte und entfernt wurde, `False` andernfalls.

#### `remove(method: str \| JsonRpcMethodWrapper) -> bool`

Entfernt eine Methode nach Name oder Wrapper-Instanz.

| Parameter | Typ | Beschreibung |
|---|---|---|
| `method` | `str \| JsonRpcMethodWrapper` | Entweder ein Methodenname-String oder ein `JsonRpcMethodWrapper`. |

**Gibt zurück:** `True`, wenn die Methode existierte und entfernt wurde, `False` andernfalls.

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

Leitet eingehende JSON-RPC-Nachrichten an registrierte Handler weiter. Hält separate Register für Anfragen (die eine Antwort erwarten) und Benachrichtigungen (Fire-and-Forget).

### Konstruktor

```python
JsonRpcDispatcher()
```

Initialisiert den Dispatcher mit leeren Handler-Registern.

### Attribute

| Attribut | Typ | Beschreibung |
|---|---|---|
| `request_handler_registry` | `JsonRpcHandlerCollection` | Register für Anfrage-Handler. |
| `notification_handler_registry` | `JsonRpcHandlerCollection` | Register für Benachrichtigungs-Handler. |

### Methoden

#### `__call__(data: str \| JsonRpcRequest \| JsonRpcNotification) -> Option[Result[JsonRpcResponse, JsonRpcError]]`

Dispatcht eine JSON-RPC-Nachricht.

| Parameter | Typ | Beschreibung |
|---|---|---|
| `data` | `str \| JsonRpcRequest \| JsonRpcNotification` | Ein JSON-String, `JsonRpcRequest` oder `JsonRpcNotification`. |

**Gibt zurück:**

| Eingabe | Handler gefunden | Handler nicht gefunden |
|---|---|---|
| `str` (Parse erfolgreich) | Delegiert an Anfrage-/Benachrichtigungsbehandlung | — |
| `str` (Parse fehlgeschlagen) | `Some(Err(ParseError))` | — |
| `JsonRpcRequest` | `Some(Ok(response))` | `Some(Err(MethodNotFound))` über Antwort |
| `JsonRpcNotification` | `Nothing` (Erfolg) | `Some(Err(MethodNotFound))` |
| Unbekannter Typ | `Some(Err(InternalError))` | — |

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

#### `try_parse(data: str) -> Result[JsonRpcRequest \| JsonRpcNotification, JsonRpcError]` *(Klassenmethode)*

Versucht, einen JSON-String in eine Anfrage oder Benachrichtigung zu parsen. Versucht zuerst `JsonRpcRequest`; bei Misserfolg wird auf `JsonRpcNotification` zurückgegriffen.

| Parameter | Typ | Beschreibung |
|---|---|---|
| `data` | `str` | Ein JSON-kodierter String. |

**Gibt zurück:** `Ok(request | notification)` bei Erfolg oder `Err(JsonRpcError)` bei Parsefehler.
