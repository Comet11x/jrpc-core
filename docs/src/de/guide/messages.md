# Nachrichten-API

Alle Nachrichten-Primitive befinden sich im `jrpc_core.messages` Modul.

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

## Typ-Aliase

### `JsonRpcId`

```python
JsonRpcId = str | int | float | None
```

Typ-Alias für einen JSON-RPC-Nachrichtenbezeichner. Ein gültiger Bezeichner ist ein `str`, `int`, `float` oder `None`. Die `None`-Variante ist nur in Benachrichtigungen erlaubt.

### `JsonRpcParams`

```python
JsonRpcParams = dict[str, Any] | list[Any] | None
```

Typ-Alias für JSON-RPC `params`-Werte. Parameter können eine benannte Zuordnung (`dict`), eine positionale Liste (`list`) oder `None` bei Weglassung sein.

---

## `JsonRpcErrorCode`

```python
class JsonRpcErrorCode(Enum)
```

Aufzählung der standardmäßigen JSON-RPC 2.0-Fehlercodes. Jedes Element ordnet dem ganzzahligen Code zu, der durch die Spezifikation oder gängige Erweiterungen definiert ist (`-32xxx` reserviert, `-320xx` serverdefiniert).

### Elemente

| Element | Wert | Beschreibung |
|---|---|---|
| `ParseError` | `-32700` | Der Server hat ungültiges JSON empfangen. |
| `InternalError` | `-32603` | Ein interner JSON-RPC-Fehler ist aufgetreten. |
| `InvalidParams` | `-32602` | Die mit der Methode gesendeten Parameter sind ungültig. |
| `MethodNotFound` | `-32601` | Die Methode existiert nicht oder ist nicht verfügbar. |
| `InvalidRequest` | `-32600` | Das gesendete JSON ist kein gültiges Anfrageobjekt. |
| `ExecutionError` | `-32000` | Ein serverdefinierter Ausführungsfehler ist aufgetreten. |

### Methoden

#### `__int__() -> int`

Gibt den ganzzahligen Wert dieses Fehlercodes zurück.

```python
>>> int(JsonRpcErrorCode.ParseError)
-32700
```

#### `description() -> str`

Gibt eine menschenlesbare Beschreibung dieses Fehlercodes zurück.

```python
>>> JsonRpcErrorCode.ParseError.description()
'Parse error'
```

#### `default() -> JsonRpcErrorCode` *(statisch)*

Gibt den Standardfehlercode zurück, der verwendet wird, wenn kein anderer Code passt. Gibt `InternalError` zurück.

```python
>>> JsonRpcErrorCode.default()
<JsonRpcErrorCode.InternalError: -32603>
```

#### `into(data: Any = None) -> JsonRpcError`

Erstellt einen `JsonRpcError` aus diesem Code.

| Parameter | Typ | Standard | Beschreibung |
|---|---|---|---|
| `data` | `Any` | `None` | Optionale zusätzliche Nutzlast, die dem Fehler beigefügt wird. |

**Gibt zurück:** Einen neuen `JsonRpcError` mit diesem Code und seiner Beschreibung.

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

Unterstützte JSON-RPC-Protokollversionen.

| Element | Wert |
|---|---|
| `Version1` | `"1.0"` |
| `Version2` | `"2.0"` |

---

## `JsonRpcError`

```python
class JsonRpcError(BaseModel)
```

Ein JSON-RPC 2.0-Fehlerobjekt.

### Attribute

| Attribut | Typ | Standard | Beschreibung |
|---|---|---|---|
| `code` | `JsonRpcErrorCode \| int` | `JsonRpcErrorCode.InternalError` | Ein ganzzahliger Fehlercode. |
| `message` | `str` | `"Something went wrong"` | Eine kurze, menschenlesbare Beschreibung. |
| `data` | `Any \| None` | `None` | Optionale zusätzliche Informationen über den Fehler. |

### Methoden

#### `default() -> JsonRpcError` *(statisch)*

Gibt einen Standardfehler mit `JsonRpcErrorCode.InternalError` zurück.

```python
>>> JsonRpcError.default()
JsonRpcError(code=<JsonRpcErrorCode.InternalError: -32603>, message='Something went wrong', data=None)
```

#### `from_error(error: JsonRpcError | Any) -> JsonRpcError` *(statisch)*

Konvertiert einen beliebigen Wert in einen `JsonRpcError`. Wenn *error* bereits ein `JsonRpcError` ist, wird er unverändert zurückgegeben. Andernfalls versucht die Funktion, ein `code`-Attribut zu extrahieren und baut einen Fehler darum auf, wobei auf `JsonRpcErrorCode.InternalError` zurückgegriffen wird.

| Parameter | Typ | Beschreibung |
|---|---|---|
| `error` | `JsonRpcError \| Any` | Der zu konvertierende Wert. |

**Gibt zurück:** Eine `JsonRpcError`-Instanz.

```python
>>> JsonRpcError.from_error(RuntimeError("oops"))
JsonRpcError(code=<JsonRpcErrorCode.InternalError: -32603>, message='Internal error', data=RuntimeError('oops'))
```

#### `try_from(value: Option[JsonRpcError | Any]) -> Option[JsonRpcError]` *(statisch)*

Versucht, ein `Option` in einen Fehler zu konvertieren.

| Parameter | Typ | Beschreibung |
|---|---|---|
| `value` | `Option[JsonRpcError \| Any]` | Ein `Option`, das einen zu konvertierenden Wert enthalten kann. |

**Gibt zurück:** `Some(JsonRpcError)`, wenn *value* `Some` war, andernfalls `Nothing`.

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

Ein JSON-RPC 2.0-Anfrageobjekt. Enthält einen `method`-Namen, eine optionale `params`-Nutzlast und eine `id`, die der Client zur Zuordnung der Antwort verwendet.

### Attribute

| Attribut | Typ | Standard | Beschreibung |
|---|---|---|---|
| `method` | `str` | *(erforderlich)* | Der Name des aufzurufenden Remote-Verfahrens. Muss ein nicht-leerer String sein. |
| `id` | `JsonRpcId` | `str(uuid4())` | Ein eindeutiger Bezeichner für diese Anfrage (standardmäßig automatisch generierte UUID). |
| `params` | `JsonRpcParams` | `None` | Optionale positionsgebundene oder benannte Argumente für die Methode. |
| `jsonrpc` | `JsonRpcVersion` | `Version2` | Die Protokollversion. |

### Methoden

#### `try_from_dict(data: dict) -> Result[JsonRpcRequest, Exception]` *(Klassenmethode)*

Versucht, eine Anfrage aus einem einfachen Dictionary zu erstellen.

| Parameter | Typ | Beschreibung |
|---|---|---|
| `data` | `dict[str, Any]` | Ein Dictionary mit JSON-RPC-Anlegefeldern. |

**Gibt zurück:** `Ok(request)` bei Erfolg oder `Err(exception)` bei Validierungsfehler.

```python
>>> JsonRpcRequest.try_from_dict({"method": "add", "id": 1}).is_ok()
True
```

#### `try_from_json(data: str) -> Result[JsonRpcRequest, Exception]` *(Klassenmethode)*

Versucht, eine Anfrage aus einem JSON-String zu erstellen.

| Parameter | Typ | Beschreibung |
|---|---|---|
| `data` | `str` | Ein JSON-kodierter String, der eine Anfrage darstellt. |

**Gibt zurück:** `Ok(request)` bei Erfolg oder `Err(exception)` bei Parse-/Validierungsfehler.

```python
>>> JsonRpcRequest.try_from_json('{"method":"add","id":1}').is_ok()
True
```

#### `to_dict() -> dict[str, Any]`

Serialisiert die Anfrage in ein einfaches Dictionary. Der `params`-Schlüssel wird weggelassen, wenn `None`.

**Gibt zurück:** Ein Dictionary, das für JSON-Serialisierung geeignet ist.

```python
>>> JsonRpcRequest(method="add", params=[1, 2]).to_dict()
{'method': 'add', 'id': '<uuid>', 'params': [1, 2], 'jsonrpc': '2.0'}
```

#### `to_json() -> str`

Serialisiert die Anfrage in einen JSON-String.

**Gibt zurück:** Eine kompakte JSON-Darstellung dieser Anfrage.

#### `into(result: Result[Any, JsonRpcError]) -> JsonRpcResponse`

Erstellt eine `JsonRpcResponse` aus einem Handler-Ergebnis. Akzeptiert ein `Result`, einen `JsonRpcError` oder einen Rohwert.

| Parameter | Typ | Beschreibung |
|---|---|---|
| `result` | `Result[Any, JsonRpcError]` | Das Ergebnis der Verarbeitung dieser Anfrage. |

**Gibt zurück:** Eine Antwort, die entweder das entpackte Ergebnis oder den Fehler enthält.

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

Ein JSON-RPC 2.0-Benachrichtigungsobjekt. Identisch mit einer Anfrage, lässt aber das `id`-Feld weg, was anzeigt, dass keine Antwort vom Server erwartet wird.

### Attribute

| Attribut | Typ | Standard | Beschreibung |
|---|---|---|---|
| `method` | `str` | *(erforderlich)* | Der Name des Ereignisses oder Verfahrens, das angekündigt wird. Muss ein nicht-leerer String sein. |
| `params` | `JsonRpcParams` | `None` | Optionale positionsgebundene oder benannte Argumente. |
| `jsonrpc` | `JsonRpcVersion` | `Version2` | Die Protokollversion. |

::: warning
Eine Benachrichtigung darf **kein** `id`-Feld enthalten. Der Versuch, eine mit `id` zu erstellen, löst einen Validierungsfehler aus.
:::

### Methoden

#### `try_from_dict(data: dict) -> Result[JsonRpcNotification, Exception]` *(Klassenmethode)*

Versucht, eine Benachrichtigung aus einem einfachen Dictionary zu erstellen.

| Parameter | Typ | Beschreibung |
|---|---|---|
| `data` | `dict[str, Any]` | Ein Dictionary mit JSON-RPC-Benachrichtigungsfeldern. |

**Gibt zurück:** `Ok(notification)` bei Erfolg oder `Err(exception)` bei Validierungsfehler.

#### `try_from_json(data: str) -> Result[JsonRpcNotification, Exception]` *(Klassenmethode)*

Versucht, eine Benachrichtigung aus einem JSON-String zu erstellen.

| Parameter | Typ | Beschreibung |
|---|---|---|
| `data` | `str` | Ein JSON-kodierter String, der eine Benachrichtigung darstellt. |

**Gibt zurück:** `Ok(notification)` bei Erfolg oder `Err(exception)` bei Parse-/Validierungsfehler.

#### `to_dict() -> dict[str, Any]`

Serialisiert die Benachrichtigung in ein einfaches Dictionary. Der `params`-Schlüssel wird weggelassen, wenn `None`.

**Gibt zurück:** Ein Dictionary, das für JSON-Serialisierung geeignet ist.

#### `to_json() -> str`

Serialisiert die Benachrichtigung in einen JSON-String.

**Gibt zurück:** Eine kompakte JSON-Darstellung dieser Benachrichtigung.

---

## `JsonRpcResponse`

```python
class JsonRpcResponse(BaseModel)
```

Ein JSON-RPC 2.0-Antwortobjekt. Genau eines von `result` oder `error` muss gesetzt sein. Die `id` stimmt mit der `id` der ursprünglichen Anfrage überein.

### Attribute

| Attribut | Typ | Standard | Beschreibung |
|---|---|---|---|
| `id` | `JsonRpcId` | *(erforderlich)* | Der Bezeichner der Anfrage, auf die sich diese Antwort bezieht. |
| `result` | `Any` | `None` | Der Rückgabewert, wenn die Methode erfolgreich ausgeführt wurde. |
| `error` | `JsonRpcError \| None` | `None` | Ein `JsonRpcError`, wenn die Methode fehlgeschlagen ist. |
| `jsonrpc` | `JsonRpcVersion` | `Version2` | Die Protokollversion. |

::: warning
Eine Antwort muss **entweder** ein `result` **oder** ein `error` haben, nicht beides. Der Versuch, beide zu setzen, löst einen Validierungsfehler aus.
:::

### Methoden

#### `from_result(id, result) -> JsonRpcResponse` *(statisch)*

Erstellt eine Antwort aus einem `Result`.

| Parameter | Typ | Beschreibung |
|---|---|---|
| `id` | `JsonRpcId` | Der Anfragebezeichner, der zurückgegeben werden soll. |
| `result` | `Result[Any, JsonRpcError]` | Das Ergebnis des Handlers. |

**Gibt zurück:** Eine vollständig konstruierte `JsonRpcResponse`.

```python
>>> from pyfplib import Result
>>> JsonRpcResponse.from_result(1, Result.ok("data"))
JsonRpcResponse(id=1, result='data', error=None, ...)
>>> JsonRpcResponse.from_result(2, Result.err(JsonRpcError(code=JsonRpcErrorCode.InternalError)))
JsonRpcResponse(id=2, result=None, error=JsonRpcError(...), ...)
```

#### `from_jrpc_error(id, error) -> JsonRpcResponse` *(statisch)*

Erstellt eine Fehlerantwort.

| Parameter | Typ | Beschreibung |
|---|---|---|
| `id` | `JsonRpcId` | Der Anfragebezeichner, der zurückgegeben werden soll. |
| `error` | `JsonRpcError` | Der Fehler, der beigefügt werden soll. |

**Gibt zurück:** Eine `JsonRpcResponse`, bei der nur `error` gesetzt ist.

#### `from_jrpc_result(id, result) -> JsonRpcResponse` *(statisch)*

Erstellt eine erfolgreiche Antwort.

| Parameter | Typ | Beschreibung |
|---|---|---|
| `id` | `JsonRpcId` | Der Anfragebezeichner, der zurückgegeben werden soll. |
| `result` | `Any` | Der Rückgabewert der Methode. |

**Gibt zurück:** Eine `JsonRpcResponse`, bei der nur `result` gesetzt ist.

#### `try_from_dict(data: dict) -> Result[JsonRpcResponse, Exception]` *(statisch)*

Versucht, eine Antwort aus einem einfachen Dictionary zu erstellen.

| Parameter | Typ | Beschreibung |
|---|---|---|
| `data` | `dict[str, Any]` | Ein Dictionary mit JSON-RPC-Antwortfeldern. |

**Gibt zurück:** `Ok(response)` bei Erfolg oder `Err(exception)` bei Validierungsfehler.

#### `try_from_json(data: str) -> Result[JsonRpcResponse, Exception]` *(statisch)*

Versucht, eine Antwort aus einem JSON-String zu erstellen.

| Parameter | Typ | Beschreibung |
|---|---|---|
| `data` | `str` | Ein JSON-kodierter String, der eine Antwort darstellt. |

**Gibt zurück:** `Ok(response)` bei Erfolg oder `Err(exception)` bei Parse-/Validierungsfehler.

#### `to_dict() -> dict[str, Any]`

Serialisiert die Antwort in ein einfaches Dictionary. Wenn ein `error` vorhanden ist, wird der `result`-Schlüssel entfernt und der Fehlercode in `int` umgewandelt. Wenn `result` vorhanden ist, wird der `error`-Schlüssel entfernt.

**Gibt zurück:** Ein Dictionary, das für JSON-Serialisierung geeignet ist.

#### `to_json() -> str`

Serialisiert die Antwort in einen JSON-String.

**Gibt zurück:** Eine kompakte JSON-Darstellung dieser Antwort.

---

## `try_parse()`

```python
def try_parse(data: str) -> Result[JsonRpcRequest | JsonRpcNotification, JsonRpcError]
```

Versucht, einen JSON-String als JSON-RPC-Nachricht zu parsen. Die Funktion versucht zuerst, als `JsonRpcRequest` zu parsen; bei Misserfolg wird auf `JsonRpcNotification` zurückgegriffen. Wenn beide fehlschlagen, wird der Parsefehler vom Anfrageversuch zurückgegeben.

| Parameter | Typ | Beschreibung |
|---|---|---|
| `data` | `str` | Ein JSON-kodierter String. |

**Gibt zurück:** `Ok(request | notification)` bei Erfolg oder `Err(JsonRpcError)` mit dem Parsefehler.

::: warning
Da `JsonRpcRequest` `id` standardmäßig über `uuid4()` setzt, wird eine Benachrichtigungsnutzlast (ohne `id`) als Anfrage erfolgreich sein. Verwenden Sie `JsonRpcNotification.try_from_json` direkt, wenn Sie die Benachrichtigungsform erzwingen müssen.
:::

```python
>>> try_parse('{"jsonrpc":"2.0","method":"add","id":1}')
Result.ok(JsonRpcRequest(method='add', id=1, ...))
```
