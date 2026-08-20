# Dispatcher API

The dispatcher layer lives in the `jrpc_core.dispatcher` module.

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

Wraps a callable as a JSON-RPC method with optional parameter validators.

### Constructor

```python
JsonRpcMethodWrapper(
    *,
    name: str,
    method: Callable[..., Any],
    validators: list[Callable[..., Option[JsonRpcError]]] | None = None,
)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `name` | `str` | *(required)* | The JSON-RPC method name. |
| `method` | `Callable[..., Any]` | *(required)* | The callable to invoke when this method is dispatched. |
| `validators` | `list[Callable[..., Option[JsonRpcError]]] \| None` | `None` | An optional list of callables that receive the parsed `params` and return a rejection signal. |

### Validator Protocol

Each validator receives the parsed `params` and may return:

| Return value | Behaviour |
|---|---|
| `Some(JsonRpcError)` or `Some(Exception)` | Rejects with that error wrapped in `InvalidParams` |
| `False` | Rejects with a generic `InvalidParams` error |
| `Exception` or `JsonRpcError` | Rejects with that error directly |
| `True`, `None`, or any other truthy value | Accepts — continues to next validator or method invocation |

### Attributes

| Attribute | Type | Description |
|---|---|---|
| `name` | `str` | The JSON-RPC method name this wrapper is registered under. |

### Methods

#### `__hash__() -> int`

Return a hash based on the method name. Two wrappers with the same name have the same hash.

#### `__eq__(other) -> bool`

Compare two wrappers by method name.

#### `__call__(args: Option[Any]) -> Result[Any, JsonRpcError]`

Execute the wrapped method with optional parameters. Validators are run before the method. If any validator rejects the parameters the call short-circuits with an `Err`.

| Parameter | Type | Description |
|---|---|---|
| `args` | `Option[Any]` | An `Option` containing the method parameters. `Some` means parameters were provided; `None` means none. |

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
JsonRpcDispatcher()
```

Initialise the dispatcher with empty handler registries.

### Attributes

| Attribute | Type | Description |
|---|---|---|
| `request_handler_registry` | `JsonRpcHandlerCollection` | Registry for request handlers. |
| `notification_handler_registry` | `JsonRpcHandlerCollection` | Registry for notification handlers. |

### Methods

#### `__call__(data: str | JsonRpcRequest | JsonRpcNotification) -> Option[Result[JsonRpcResponse, JsonRpcError]]`

Dispatch a JSON-RPC message.

| Parameter | Type | Description |
|---|---|---|
| `data` | `str \| JsonRpcRequest \| JsonRpcNotification` | A JSON string, `JsonRpcRequest`, or `JsonRpcNotification`. |

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

#### `try_parse(data: str) -> Result[JsonRpcRequest | JsonRpcNotification, JsonRpcError]` *(classmethod)*

Attempt to parse a JSON string into a request or notification. First tries `JsonRpcRequest`; on failure falls back to `JsonRpcNotification`.

| Parameter | Type | Description |
|---|---|---|
| `data` | `str` | A JSON-encoded string. |

**Returns:** `Ok(request | notification)` on success, or `Err(JsonRpcError)` on parse failure.
