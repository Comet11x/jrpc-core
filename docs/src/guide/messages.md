# Messages API

All message primitives live in the `jrpc_core.messages` module.

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

## Type Aliases

### `JsonRpcId`

```python
JsonRpcId = str | int | float | None
```

Type alias for a JSON-RPC message identifier. A valid identifier is a `str`, `int`, `float`, or `None`. The `None` variant is permitted only in notifications.

### `JsonRpcParams`

```python
JsonRpcParams = dict[str, Any] | list[Any] | None
```

Type alias for JSON-RPC `params` values. Parameters may be a named mapping (`dict`), a positional list (`list`), or `None` when omitted.

---

## `JsonRpcErrorCode`

```python
class JsonRpcErrorCode(Enum)
```

Enumeration of standard JSON-RPC 2.0 error codes. Each member maps to the integer code defined by the specification or common extensions (`-32xxx` reserved, `-320xx` server-defined).

### Members

| Member | Value | Description |
|---|---|---|
| `ParseError` | `-32700` | Invalid JSON was received by the server. |
| `InternalError` | `-32603` | An internal JSON-RPC error occurred. |
| `InvalidParams` | `-32602` | The parameters sent with the method are invalid. |
| `MethodNotFound` | `-32601` | The method does not exist or is not available. |
| `InvalidRequest` | `-32600` | The JSON sent is not a valid request object. |
| `ExecutionError` | `-32000` | A server-defined execution error occurred. |
| `ConversionError` | `-32001` | A server-defined conversion error occurred. |

### Methods

#### `__int__() -> int`

Return the integer value of this error code.

```python
>>> int(JsonRpcErrorCode.ParseError)
-32700
```

#### `description() -> str`

Return a human-readable description of this error code.

```python
>>> JsonRpcErrorCode.ParseError.description()
'Parse error'
```

#### `default() -> JsonRpcErrorCode` *(static)*

Return the default error code used when no other code is appropriate. Returns `InternalError`.

```python
>>> JsonRpcErrorCode.default()
<JsonRpcErrorCode.InternalError: -32603>
```

#### `into(data: Any = None) -> JsonRpcError`

Create a `JsonRpcError` from this code.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `data` | `Any` | `None` | Optional extra payload attached to the error. |

**Returns:** A new `JsonRpcError` with this code and its description.

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

Supported JSON-RPC protocol versions.

| Member | Value |
|---|---|
| `Version1` | `"1.0"` |
| `Version2` | `"2.0"` |

---

## `JsonRpcError`

```python
class JsonRpcError(BaseModel)
```

A JSON-RPC 2.0 error object.

### Attributes

| Attribute | Type | Default | Description |
|---|---|---|---|
| `code` | `JsonRpcErrorCode \| int` | `JsonRpcErrorCode.InternalError` | An integer error code. |
| `message` | `str` | `"Something went wrong"` | A short human-readable description. |
| `data` | `Any \| None` | `None` | Optional extra information about the error. |

### Methods

#### `default() -> JsonRpcError` *(static)*

Return a default error with `JsonRpcErrorCode.InternalError`.

```python
>>> JsonRpcError.default()
JsonRpcError(code=<JsonRpcErrorCode.InternalError: -32603>, message='Something went wrong', data=None)
```

#### `from_data(*, data: Any, code: JsonRpcErrorCode = InternalError, message: str = ...) -> JsonRpcError` *(static)*

Create a `JsonRpcError` from arbitrary data with explicit code and message.

| Parameter | Type | Default | Description |
|---|---|---|---|---|
| `data` | `Any` | *(required)* | Extra payload attached to the error. |
| `code` | `JsonRpcErrorCode` | `InternalError` | The error code. |
| `message` | `str` | `InternalError.description()` | A short human-readable description. |

**Returns:** A new `JsonRpcError` instance.

```python
>>> JsonRpcError.from_data(data={"detail": "oops"})
JsonRpcError(code=<JsonRpcErrorCode.InternalError: -32603>, message='Internal error', data={'detail': 'oops'})
>>> JsonRpcError.from_data(data="bad", code=JsonRpcErrorCode.InvalidParams, message="invalid")
JsonRpcError(code=<JsonRpcErrorCode.InvalidParams: -32602>, message='invalid', data='bad')
```

#### `from_error(error: JsonRpcError | Any) -> JsonRpcError` *(static)*

Convert an arbitrary value into a `JsonRpcError`. If *error* is already a `JsonRpcError` it is returned as-is. Otherwise the function attempts to extract a `code` attribute and builds an error around it, falling back to `JsonRpcErrorCode.InternalError`.

| Parameter | Type | Description |
|---|---|---|
| `error` | `JsonRpcError \| Any` | The value to convert. |

**Returns:** A `JsonRpcError` instance.

```python
>>> JsonRpcError.from_error(RuntimeError("oops"))
JsonRpcError(code=<JsonRpcErrorCode.InternalError: -32603>, message='Internal error', data=RuntimeError('oops'))
```

#### `try_from(value: Option[JsonRpcError | Any]) -> Option[JsonRpcError]` *(static)*

Attempt to convert an `Option` into an error.

| Parameter | Type | Description |
|---|---|---|
| `value` | `Option[JsonRpcError \| Any]` | An `Option` that may contain a value to convert. |

**Returns:** `Some(JsonRpcError)` if *value* was `Some`, otherwise `Nothing`.

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

A JSON-RPC 2.0 request object. Contains a `method` name, an optional `params` payload, and an `id` that the client uses to correlate the response.

### Attributes

| Attribute | Type | Default | Description |
|---|---|---|---|
| `method` | `str` | *(required)* | The name of the remote procedure to invoke. Must be a non-empty string. |
| `id` | `JsonRpcId` | `str(uuid4())` | A unique identifier for this request (auto-generated UUID by default). |
| `params` | `JsonRpcParams` | `None` | Optional positional or named arguments for the method. |
| `jsonrpc` | `JsonRpcVersion` | `Version2` | The protocol version. |

### Methods

#### `try_from_dict(data: dict) -> Result[JsonRpcRequest, Exception]` *(classmethod)*

Attempt to build a request from a plain dictionary.

| Parameter | Type | Description |
|---|---|---|
| `data` | `dict[str, Any]` | A dictionary with JSON-RPC request fields. |

**Returns:** `Ok(request)` on success, or `Err(exception)` on validation failure.

```python
>>> JsonRpcRequest.try_from_dict({"method": "add", "id": 1}).is_ok()
True
```

#### `try_from_json(data: str) -> Result[JsonRpcRequest, Exception]` *(classmethod)*

Attempt to build a request from a JSON string.

| Parameter | Type | Description |
|---|---|---|
| `data` | `str` | A JSON-encoded string representing a request. |

**Returns:** `Ok(request)` on success, or `Err(exception)` on parse/validation failure.

```python
>>> JsonRpcRequest.try_from_json('{"method":"add","id":1}').is_ok()
True
```

#### `to_dict() -> dict[str, Any]`

Serialize the request to a plain dictionary. The `params` key is omitted when `None`.

**Returns:** A dictionary suitable for JSON serialisation.

```python
>>> JsonRpcRequest(method="add", params=[1, 2]).to_dict()
{'method': 'add', 'id': '<uuid>', 'params': [1, 2], 'jsonrpc': '2.0'}
```

#### `to_json() -> str`

Serialize the request to a JSON string.

**Returns:** A compact JSON representation of this request.

#### `serialize() -> str`

Serialize the request to a JSON string. Alias for `to_json()`.

**Returns:** A compact JSON representation of this request.

#### `into(result: Result[Any, JsonRpcError]) -> JsonRpcResponse`

Create a `JsonRpcResponse` from a handler result. Accepts a `Result`, a `JsonRpcError`, or a raw value.

| Parameter | Type | Description |
|---|---|---|
| `result` | `Result[Any, JsonRpcError]` | The outcome of processing this request. |

**Returns:** A response carrying either the unwrapped result or the error.

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

A JSON-RPC 2.0 notification object. Identical to a request but omits the `id` field, indicating that no response is expected from the server.

### Attributes

| Attribute | Type | Default | Description |
|---|---|---|---|
| `method` | `str` | *(required)* | The name of the event or procedure being announced. Must be a non-empty string. |
| `params` | `JsonRpcParams` | `None` | Optional positional or named arguments. |
| `jsonrpc` | `JsonRpcVersion` | `Version2` | The protocol version. |

::: warning
A notification must **not** contain an `id` field. Attempting to construct one with an `id` raises a validation error.
:::

### Methods

#### `try_from_dict(data: dict) -> Result[JsonRpcNotification, Exception]` *(classmethod)*

Attempt to build a notification from a plain dictionary.

| Parameter | Type | Description |
|---|---|---|
| `data` | `dict[str, Any]` | A dictionary with JSON-RPC notification fields. |

**Returns:** `Ok(notification)` on success, or `Err(exception)` on validation failure.

#### `try_from_json(data: str) -> Result[JsonRpcNotification, Exception]` *(classmethod)*

Attempt to build a notification from a JSON string.

| Parameter | Type | Description |
|---|---|---|
| `data` | `str` | A JSON-encoded string representing a notification. |

**Returns:** `Ok(notification)` on success, or `Err(exception)` on parse/validation failure.

#### `to_dict() -> dict[str, Any]`

Serialize the notification to a plain dictionary. The `params` key is omitted when `None`.

**Returns:** A dictionary suitable for JSON serialisation.

#### `to_json() -> str`

Serialize the notification to a JSON string.

**Returns:** A compact JSON representation of this notification.

#### `serialize() -> str`

Serialize the notification to a JSON string. Alias for `to_json()`.

**Returns:** A compact JSON representation of this notification.

---

## `JsonRpcResponse`

```python
class JsonRpcResponse(BaseModel)
```

A JSON-RPC 2.0 response object. Exactly one of `result` or `error` must be set. The `id` matches the `id` of the originating request.

### Attributes

| Attribute | Type | Default | Description |
|---|---|---|---|
| `id` | `JsonRpcId` | *(required)* | The identifier of the request this response corresponds to. |
| `result` | `Any` | `None` | The return value when the method executed successfully. |
| `error` | `JsonRpcError \| None` | `None` | A `JsonRpcError` when the method failed. |
| `jsonrpc` | `JsonRpcVersion` | `Version2` | The protocol version. |

::: warning
A response must have **either** a `result` **or** an `error`, not both. Attempting to set both raises a validation error.
:::

### Methods

#### `from_result(id, result) -> JsonRpcResponse` *(static)*

Build a response from a `Result`.

| Parameter | Type | Description |
|---|---|---|
| `id` | `JsonRpcId` | The request identifier to echo back. |
| `result` | `Result[Any, JsonRpcError]` | The handler's outcome. |

**Returns:** A fully constructed `JsonRpcResponse`.

```python
>>> from pyfplib import Result
>>> JsonRpcResponse.from_result(1, Result.ok("data"))
JsonRpcResponse(id=1, result='data', error=None, ...)
>>> JsonRpcResponse.from_result(2, Result.err(JsonRpcError(code=JsonRpcErrorCode.InternalError)))
JsonRpcResponse(id=2, result=None, error=JsonRpcError(...), ...)
```

#### `from_jrpc_error(id, error) -> JsonRpcResponse` *(static)*

Build an error response.

| Parameter | Type | Description |
|---|---|---|
| `id` | `JsonRpcId` | The request identifier to echo back. |
| `error` | `JsonRpcError \| Exception` | The error to include. |

**Returns:** A `JsonRpcResponse` with only `error` set.

#### `from_jrpc_result(id, result) -> JsonRpcResponse` *(static)*

Build a successful response.

| Parameter | Type | Description |
|---|---|---|
| `id` | `JsonRpcId` | The request identifier to echo back. |
| `result` | `Any` | The return value of the method. |

**Returns:** A `JsonRpcResponse` with only `result` set.

#### `try_from_dict(data: dict) -> Result[JsonRpcResponse, Exception]` *(static)*

Attempt to build a response from a plain dictionary.

| Parameter | Type | Description |
|---|---|---|
| `data` | `dict[str, Any]` | A dictionary with JSON-RPC response fields. |

**Returns:** `Ok(response)` on success, or `Err(exception)` on validation failure.

#### `try_from_json(data: str) -> Result[JsonRpcResponse, Exception]` *(static)*

Attempt to build a response from a JSON string.

| Parameter | Type | Description |
|---|---|---|
| `data` | `str` | A JSON-encoded string representing a response. |

**Returns:** `Ok(response)` on success, or `Err(exception)` on parse/validation failure.

#### `to_dict() -> dict[str, Any]`

Serialize the response to a plain dictionary. When an `error` is present the `result` key is removed and the error code is coerced to `int`. When `result` is present the `error` key is removed.

**Returns:** A dictionary suitable for JSON serialisation.

#### `to_json() -> str`

Serialize the response to a JSON string.

**Returns:** A compact JSON representation of this response.

#### `serialize() -> str`

Serialize the response to a JSON string. Alias for `to_json()`.

**Returns:** A compact JSON representation of this response.

---

## `try_parse()`

```python
def try_parse(data: str) -> Result[JsonRpcResponse | JsonRpcNotification | JsonRpcRequest, JsonRpcError]
```

Attempt to parse a JSON string as a JSON-RPC message. The function first tries to parse as a `JsonRpcResponse`; if that fails it falls back to `JsonRpcNotification`; if that fails it falls back to `JsonRpcRequest`. If all of them fail, the parse error from the request attempt is returned.

| Parameter | Type | Description |
|---|---|---|
| `data` | `str` | A JSON-encoded string. |

**Returns:** `Ok(request | notification | response)` on success, or `Err(JsonRpcError)` containing the parse failure.

```python
>>> try_parse('{"jsonrpc":"2.0","method":"add","id":1}')
Result.ok(JsonRpcRequest(method='add', id=1, ...))
```
