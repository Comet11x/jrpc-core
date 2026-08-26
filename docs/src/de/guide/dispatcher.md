# Dispatcher-API

Die Dispatcher-Schicht befindet sich im `jrpc_core.dispatcher` Modul.

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

Verpackt einen Aufrufbaren als JSON-RPC-Methode mit optionaler Validierung und Konvertierung.

### Konstruktor

```python
JsonRpcMethodWrapper(
    *,
    name: str,
    method: Callable[..., Any],
    validator: Callable[..., Option[JsonRpcError] | bool] | None = None,
    converter: Callable[..., Option[Any] | Result[Any, Exception | JsonRpcError] | Any] | None = None,
)
```

| Parameter | Typ | Standard | Beschreibung |
|---|---|---|---|
| `name` | `str` | *(erforderlich)* | Der JSON-RPC-Methodenname. |
| `method` | `Callable[..., Any]` | *(erforderlich)* | Der Aufrufbare, der aufgerufen wird, wenn diese Methode dispatched wird. |
| `validator` | `Callable[..., Option[JsonRpcError] \| bool] \| None` | `None` | Ein optionaler Aufrufbarer, der die geparsten `params` empfängt und ein Ablehnungssignal zurückgibt. |
| `converter` | `Callable[..., Option[Any] \| Result[Any, Exception \| JsonRpcError] \| Any] \| None` | `None` | Ein optionaler Aufrufbarer, der die geparsten `params` vor dem Aufruf der Methode transformiert. |

### Validator-Protokoll

Der Validator erhält die geparsten `params` und kann zurückgeben:

| Rückgabewert | Verhalten |
|---|---|
| `Some(JsonRpcError)` | Lehnt mit diesem Fehler ab |
| `Some(Exception)` | Lehnt mit diesem Fehler, verpackt in `InvalidParams`, ab |
| `False` | Lehnt mit einem allgemeinen `InvalidParams`-Fehler ab |
| `Exception` oder `JsonRpcError` | Lehnt mit diesem Fehler direkt ab |
| `True`, `None` oder jeder andere wahre Wert | Akzeptiert — fährt mit Konvertierung oder Methodenausführung fort |

### Converter-Protokoll

Der Converter erhält das rohe `params`-Payload und kann zurückgeben:

| Rückgabewert | Verhalten |
|---|---|
| `Some(value)` | Verwendet `value` als Methodenargument |
| `Nothing()` | Lehnt mit `ConversionError` ab |
| `Ok(value)` | Verwendet `value` als Methodenargument |
| `Err(reason)` | Lehnt mit `ConversionError` ab, `reason` wird an `data` angehängt |
| Jeder andere Wert | Verwendet den Wert direkt als Methodenargument |
| Wirft `Exception` | Lehnt mit `ConversionError` ab, die Ausnahme wird an `data` angehängt |

### Attribute

| Attribut | Typ | Beschreibung |
|---|---|---|
| `name` | `str` | Der JSON-RPC-Methodenname, unter dem dieser Wrapper registriert ist. |

### Methoden

#### `__hash__() -> int`

Gibt einen Hash basierend auf dem Methodennamen zurück. Zwei Wrapper mit demselben Namen haben denselben Hash.

#### `__eq__(other) -> bool`

Vergleicht zwei Wrapper nach Methodennamen.

#### `__call__(params: Option[Any]) -> Result[Any, JsonRpcError]`

Führt die verpackte Methode mit optionalen Parametern aus. Validierung läuft zuerst, dann Konvertierung; wenn einer der Schritte die Parameter ablehnt, wird der Aufruf mit einem `Err` abgebrochen.

| Parameter | Typ | Beschreibung |
|---|---|---|
| `params` | `Option[Any]` | Ein `Option`, das die Methodenparameter enthält. `Some` bedeutet, dass Parameter bereitgestellt wurden; `Nothing` bedeutet keine. |

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
JsonRpcDispatcher(
    response_handler: Callable[[JsonRpcResponse], None] | None = None,
)
```

| Parameter | Typ | Standard | Beschreibung |
|---|---|---|---|
| `response_handler` | `Callable[[JsonRpcResponse], None] \| None` | `None` | Optionaler Callback, der aufgerufen wird, wenn eine `JsonRpcResponse` direkt dispatched wird. |

### Klassenattribute

| Attribut | Typ | Beschreibung |
|---|---|---|
| `ERROR_CASE` | `JsonRpcResponseCtorWrapper.State` | Auswahlschema für Fehlerantworten. |
| `RESULT_CASE` | `JsonRpcResponseCtorWrapper.State` | Auswahlschema für erfolgreiche Ergebnisse. |
| `BOTH_CASES` | `JsonRpcResponseCtorWrapper._When` | Auswahlschema, das beide Ergebnisse matched. |

### Attribute

| Attribut | Typ | Beschreibung |
|---|---|---|
| `request_handler_registry` | `JsonRpcHandlerCollection` | Register für Anfrage-Handler. |
| `notification_handler_registry` | `JsonRpcHandlerCollection` | Register für Benachrichtigungs-Handler. |

### Methoden

#### `emplace_request_handler(*, name, method, validator=None, converter=None) -> bool`

Registriert einen Anfrage-Handler in einem Aufruf. Praktische Kurzform für `request_handler_registry.add(JsonRpcMethodWrapper(...))`.

| Parameter | Typ | Standard | Beschreibung |
|---|---|---|---|
| `name` | `str` | *(erforderlich)* | Der JSON-RPC-Methodenname. |
| `method` | `Callable[..., Any]` | *(erforderlich)* | Der Aufrufbare, der beim Dispatch aufgerufen wird. |
| `validator` | `Callable[..., Option[JsonRpcError] \| bool] \| None` | `None` | Optionaler Parameter-Validator. |
| `converter` | `Callable[..., Option[Any] \| Result[Any, Exception \| JsonRpcError] \| Any] \| None` | `None` | Optionaler Parameter-Converter. |

**Gibt zurück:** `True` wenn neu registriert, `False` wenn der Name bereits existiert.

#### `emplace_notification_handler(*, name, method, validator=None, converter=None) -> bool`

Registriert einen Benachrichtigungs-Handler in einem Aufruf. Praktische Kurzform für `notification_handler_registry.add(JsonRpcMethodWrapper(...))`.

| Parameter | Typ | Standard | Beschreibung |
|---|---|---|---|
| `name` | `str` | *(erforderlich)* | Der JSON-RPC-Methodenname. |
| `method` | `Callable[..., Any]` | *(erforderlich)* | Der Aufrufbare, der beim Dispatch aufgerufen wird. |
| `validator` | `Callable[..., Option[JsonRpcError] \| bool] \| None` | `None` | Optionaler Parameter-Validator. |
| `converter` | `Callable[..., Option[Any] \| Result[Any, Exception \| JsonRpcError] \| Any] \| None` | `None` | Optionaler Parameter-Converter. |

**Gibt zurück:** `True` wenn neu registriert, `False` wenn der Name bereits existiert.

#### `emplace_custom_response_ctor(method, ctor, *states)`

Registriert einen benutzerdefinierten Antwort-Konstruktor für *method*.

| Parameter | Typ | Beschreibung |
|---|---|---|
| `method` | `str` | Der JSON-RPC-Methodenname, auf den der Konstruktor zutrifft. |
| `ctor` | `Callable[..., JsonRpcResponse]` | Aufrufbarer, der eine `JsonRpcResponse` erstellt. |
| `*states` | `JsonRpcResponseCtorWrapper.State` | Optionale State-Member, die einschränken, wann *ctor* verwendet wird. |

#### `add_custom_response_ctor(ctor: JsonRpcResponseCtorWrapper)`

Registriert einen vorgefertigten benutzerdefinierten Antwort-Konstruktor. Ersetzt jeden zuvor für dieselbe Methode registrierten Konstruktor.

| Parameter | Typ | Beschreibung |
|---|---|---|
| `ctor` | `JsonRpcResponseCtorWrapper` | Der Wrapper, der einen Konstruktor an einen Methodennamen bindet. |

#### `__call__(data) -> Option[Result[JsonRpcResponse, JsonRpcError]]`

Dispatcht eine JSON-RPC-Nachricht.

| Parameter | Typ | Beschreibung |
|---|---|---|
| `data` | `str \| JsonRpcRequest \| JsonRpcNotification \| JsonRpcResponse \| Result[...]` | Ein JSON-String, `JsonRpcRequest`, `JsonRpcNotification`, `JsonRpcResponse` oder `Result`. |

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

#### `try_parse(data: str) -> Result[JsonRpcResponse \| JsonRpcNotification \| JsonRpcRequest, JsonRpcError]` *(Klassenmethode)*

Versucht, einen JSON-String in eine Antwort, Anfrage oder Benachrichtigung zu parsen. Versucht zuerst `JsonRpcResponse`; bei Misserfolg wird auf `JsonRpcNotification` zurückgegriffen; bei weiterem Misserfolg auf `JsonRpcRequest`.

| Parameter | Typ | Beschreibung |
|---|---|---|
| `data` | `str` | Ein JSON-kodierter String. |

**Gibt zurück:** `Ok(response | notification | request)` bei Erfolg oder `Err(JsonRpcError)` bei Parsefehler.

---

## `JsonRpcResponseCtorWrapper`

```python
class JsonRpcResponseCtorWrapper
```

Bindet einen benutzerdefinierten `JsonRpcResponse`-Konstruktor an einen Methodennamen. Der Wrapper zeichnet auf, *wann* der Konstruktor zutrifft — erfolgreiche Ergebnisse, Fehler oder beide — damit der Dispatcher den richtigen Antworttyp pro Ergebnis auswählen kann.

### Konstruktor

```python
JsonRpcResponseCtorWrapper(
    method: str,
    ctor: Callable[..., JsonRpcResponse],
    *states: JsonRpcResponseCtorWrapper.State,
)
```

| Parameter | Typ | Standard | Beschreibung |
|---|---|---|---|
| `method` | `str` | *(erforderlich)* | Der JSON-RPC-Methodenname, auf den dieser Konstruktor zutrifft. |
| `ctor` | `Callable[..., JsonRpcResponse]` | *(erforderlich)* | Aufrufbarer, der Schlüsselargumente (`id`, `result` oder `error`, und `jsonrpc`) empfängt und eine `JsonRpcResponse` zurückgibt. |
| `*states` | `State` | Beide Ergebnisse | Optionale `State`-Member, die einschränken, wann *ctor* verwendet wird. |

### Innere Klasse: `State`

```python
class State(Enum)
```

Auswahlschema, das steuert, wann ein Konstruktor angewendet wird.

| Member | Wert | Beschreibung |
|---|---|---|
| `Result` | `1` | Der Konstruktor behandelt erfolgreiche Ergebnisse. |
| `Error` | `2` | Der Konstruktor behandelt Fehlerantworten. |

### Attribute

| Attribut | Typ | Beschreibung |
|---|---|---|
| `method` | `str` | Der JSON-RPC-Methodenname, an den dieser Konstruktor gebunden ist. |
| `when` | `_When` | Das Auswahlschema für diesen Konstruktor. |
