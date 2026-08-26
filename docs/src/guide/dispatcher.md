# Dispatcher API

The dispatcher layer lives in the `jrpc_core.dispatcher` module.

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

Wraps a callable as a JSON-RPC method with optional validation and conversion.

### Constructor

```python
JsonRpcMethodWrapper(
    *,
    name: str,
    method: Callable[..., Any],
    validator: Callable[..., Option[JsonRpcError] | bool] | None = None,
    converter: Callable[..., Option[Any] | Result[Any, Exception | JsonRpcError] | Any] | None = None,
)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `name` | `str` | *(required)* | The JSON-RPC method name. |
| `method` | `Callable[..., Any]` | *(required)* | The callable to invoke when this method is dispatched. |
| `validator` | `Callable[..., Option[JsonRpcError] \| bool] \| None` | `None` | An optional callable that receives the parsed `params` and returns a rejection signal. |
| `converter` | `Callable[..., Option[Any] \| Result[Any, Exception \| JsonRpcError] \| Any] \| None` | `None` | An optional callable that transforms the parsed `params` before the method is invoked. |

### Validator Protocol

The validator receives the parsed `params` and may return:

| Return value | Behaviour |
|---|---|
| `Some(JsonRpcError)` | Rejects with that error |
| `Some(Exception)` | Rejects with that error wrapped in `InvalidParams` |
| `False` | Rejects with a generic `InvalidParams` error |
| `Exception` or `JsonRpcError` | Rejects with that error directly |
| `True`, `None`, or any other truthy value | Accepts — continues to conversion or method invocation |

### Converter Protocol

The converter receives the raw `params` payload and may return:

| Return value | Behaviour |
|---|---|
| `Some(value)` | Uses `value` as the method argument |
| `Nothing()` | Rejects with `ConversionError` |
| `Ok(value)` | Uses `value` as the method argument |
| `Err(reason)` | Rejects with `ConversionError`, attaching `reason` to `data` |
| Any other value | Uses the value directly as the method argument |
| Raises `Exception` | Rejects with `ConversionError`, attaching the exception to `data` |

### Attributes

| Attribute | Type | Description |
|---|---|---|
| `name` | `str` | The JSON-RPC method name this wrapper is registered under. |

### Methods

#### `__hash__() -> int`

Return a hash based on the method name. Two wrappers with the same name have the same hash.

#### `__eq__(other) -> bool`

Compare two wrappers by method name.

#### `__call__(params: Option[Any]) -> Result[Any, JsonRpcError]`

Execute the wrapped method with optional parameters. Validation runs first, then conversion; if either step rejects the parameters the call short-circuits with an `Err`.

| Parameter | Type | Description |
|---|---|---|
| `params` | `Option[Any]` | An `Option` containing the method parameters. `Some` means parameters were provided; `Nothing` means none. |

**Returns:** `Ok(result)` on success, or `Err(JsonRpcError)` on failure.

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

A registry of `JsonRpcMethodWrapper` instances keyed by method name.

### Constructor

```python
JsonRpcHandlerCollection()
```

Initialise an empty handler collection.

### Methods

#### `add(method: JsonRpcMethodWrapper) -> bool`

Register a method wrapper. If a method with the same name already exists, the call is a no-op.

| Parameter | Type | Description |
|---|---|---|
| `method` | `JsonRpcMethodWrapper` | The wrapper to register. |

**Returns:** `True` if the method was newly registered, `False` if it already existed.

```python
>>> collection = JsonRpcHandlerCollection()
>>> wrapper = JsonRpcMethodWrapper(name="add", method=lambda a: a)
>>> collection.add(wrapper)
True
>>> collection.add(wrapper)  # duplicate
False
```

#### `try_get(name: str) -> Option[JsonRpcMethodWrapper]`

Look up a method by name.

| Parameter | Type | Description |
|---|---|---|
| `name` | `str` | The JSON-RPC method name. |

**Returns:** `Some(wrapper)` if found, otherwise `Nothing`.

#### `exists(name: str) -> bool`

Check whether a method is registered.

| Parameter | Type | Description |
|---|---|---|
| `name` | `str` | The JSON-RPC method name. |

**Returns:** `True` if a wrapper with that name exists.

#### `remove_by_name(name: str) -> bool`

Remove a method by name.

| Parameter | Type | Description |
|---|---|---|
| `name` | `str` | The JSON-RPC method name to remove. |

**Returns:** `True` if the method existed and was removed, `False` otherwise.

#### `remove(method: str | JsonRpcMethodWrapper) -> bool`

Remove a method by name or wrapper instance.

| Parameter | Type | Description |
|---|---|---|
| `method` | `str \| JsonRpcMethodWrapper` | Either a method name string or a `JsonRpcMethodWrapper`. |

**Returns:** `True` if the method existed and was removed, `False` otherwise.

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

Routes incoming JSON-RPC messages to registered handlers. Maintains separate registries for requests (which expect a response) and notifications (fire-and-forget).

### Constructor

```python
JsonRpcDispatcher(
    response_handler: Callable[[JsonRpcResponse], None] | None = None,
)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `response_handler` | `Callable[[JsonRpcResponse], None] \| None` | `None` | Optional callback invoked when a `JsonRpcResponse` is dispatched directly. |

### Class Attributes

| Attribute | Type | Description |
|---|---|---|
| `ERROR_CASE` | `JsonRpcResponseCtorWrapper.State` | Outcome selector for error responses. |
| `RESULT_CASE` | `JsonRpcResponseCtorWrapper.State` | Outcome selector for successful results. |
| `BOTH_CASES` | `JsonRpcResponseCtorWrapper._When` | Outcome selector matching both outcomes. |

### Attributes

| Attribute | Type | Description |
|---|---|---|
| `request_handler_registry` | `JsonRpcHandlerCollection` | Registry for request handlers. |
| `notification_handler_registry` | `JsonRpcHandlerCollection` | Registry for notification handlers. |

### Methods

#### `emplace_request_handler(*, name, method, validator=None, converter=None) -> bool`

Register a request handler in one call. Convenience for `request_handler_registry.add(JsonRpcMethodWrapper(...))`.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `name` | `str` | *(required)* | The JSON-RPC method name. |
| `method` | `Callable[..., Any]` | *(required)* | The callable to invoke when dispatched. |
| `validator` | `Callable[..., Option[JsonRpcError] \| bool] \| None` | `None` | Optional parameter validator. |
| `converter` | `Callable[..., Option[Any] \| Result[Any, Exception \| JsonRpcError] \| Any] \| None` | `None` | Optional parameter converter. |

**Returns:** `True` if newly registered, `False` if the name already exists.

#### `emplace_notification_handler(*, name, method, validator=None, converter=None) -> bool`

Register a notification handler in one call. Convenience for `notification_handler_registry.add(JsonRpcMethodWrapper(...))`.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `name` | `str` | *(required)* | The JSON-RPC method name. |
| `method` | `Callable[..., Any]` | *(required)* | The callable to invoke when dispatched. |
| `validator` | `Callable[..., Option[JsonRpcError] \| bool] \| None` | `None` | Optional parameter validator. |
| `converter` | `Callable[..., Option[Any] \| Result[Any, Exception \| JsonRpcError] \| Any] \| None` | `None` | Optional parameter converter. |

**Returns:** `True` if newly registered, `False` if the name already exists.

#### `emplace_custom_response_ctor(method, ctor, *states)`

Register a custom response constructor for *method*.

| Parameter | Type | Description |
|---|---|---|
| `method` | `str` | The JSON-RPC method name the constructor applies to. |
| `ctor` | `Callable[..., JsonRpcResponse]` | Callable building a `JsonRpcResponse`. |
| `*states` | `JsonRpcResponseCtorWrapper.State` | Optional state members restricting when *ctor* is used. |

#### `add_custom_response_ctor(ctor: JsonRpcResponseCtorWrapper)`

Register a pre-built custom response constructor. Replaces any constructor previously registered for the same method.

| Parameter | Type | Description |
|---|---|---|
| `ctor` | `JsonRpcResponseCtorWrapper` | The wrapper binding a constructor to a method name. |

#### `__call__(data) -> Option[Result[JsonRpcResponse, JsonRpcError]]`

Dispatch a JSON-RPC message.

| Parameter | Type | Description |
|---|---|---|
| `data` | `str \| JsonRpcRequest \| JsonRpcNotification \| JsonRpcResponse \| Result[...]` | A JSON string, `JsonRpcRequest`, `JsonRpcNotification`, `JsonRpcResponse`, or `Result`. |

**Returns:**

| Input | Handler found | Handler not found |
|---|---|---|
| `str` (parse ok) | Delegates to request/notification handling | — |
| `str` (parse fail) | `Some(Err(ParseError))` | — |
| `JsonRpcRequest` | `Some(Ok(response))` | `Some(Err(MethodNotFound))` via response |
| `JsonRpcNotification` | `Nothing` (success) | `Some(Err(MethodNotFound))` |
| Unknown type | `Some(Err(InternalError))` | — |

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

#### `try_parse(data: str) -> Result[JsonRpcResponse | JsonRpcNotification | JsonRpcRequest, JsonRpcError]` *(classmethod)*

Attempt to parse a JSON string into a response, request, or notification. First tries `JsonRpcResponse`; on failure falls back to `JsonRpcNotification`; on failure falls back to `JsonRpcRequest`.

| Parameter | Type | Description |
|---|---|---|
| `data` | `str` | A JSON-encoded string. |

**Returns:** `Ok(response | notification | request)` on success, or `Err(JsonRpcError)` on parse failure.

---

## `JsonRpcResponseCtorWrapper`

```python
class JsonRpcResponseCtorWrapper
```

Binds a custom `JsonRpcResponse` constructor to a method name. The wrapper records *when* the constructor applies — successful results, errors, or both — so the dispatcher can pick the right response type per outcome.

### Constructor

```python
JsonRpcResponseCtorWrapper(
    method: str,
    ctor: Callable[..., JsonRpcResponse],
    *states: JsonRpcResponseCtorWrapper.State,
)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `method` | `str` | *(required)* | The JSON-RPC method name this constructor applies to. |
| `ctor` | `Callable[..., JsonRpcResponse]` | *(required)* | Callable receiving keyword arguments (`id`, `result` or `error`, and `jsonrpc`) and returning a `JsonRpcResponse`. |
| `*states` | `State` | Both outcomes | Optional `State` members limiting when *ctor* is used. |

### Inner Class: `State`

```python
class State(Enum)
```

Outcome selector controlling when a constructor is applied.

| Member | Value | Description |
|---|---|---|
| `Result` | `1` | The constructor handles successful results. |
| `Error` | `2` | The constructor handles error responses. |

### Attributes

| Attribute | Type | Description |
|---|---|---|
| `method` | `str` | The JSON-RPC method name this constructor is bound to. |
| `when` | `_When` | The outcome selector for this constructor. |
