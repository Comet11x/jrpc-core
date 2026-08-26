# 调度器 API

调度器层位于 `jrpc_core.dispatcher` 模块中。

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

将可调用对象包装为带有可选验证和转换的 JSON-RPC 方法。

### 构造函数

```python
JsonRpcMethodWrapper(
    *,
    name: str,
    method: Callable[..., Any],
    validator: Callable[..., Option[JsonRpcError] | bool] | None = None,
    converter: Callable[..., Option[Any] | Result[Any, Exception | JsonRpcError] | Any] | None = None,
)
```

| 参数 | 类型 | 默认值 | 描述 |
|---|---|---|---|
| `name` | `str` | *（必填）* | JSON-RPC 方法名称。 |
| `method` | `Callable[..., Any]` | *（必填）* | 此方法被调度时调用的可调用对象。 |
| `validator` | `Callable[..., Option[JsonRpcError] \| bool] \| None` | `None` | 可选的可调用对象，接收已解析的 `params` 并返回拒绝信号。 |
| `converter` | `Callable[..., Option[Any] \| Result[Any, Exception \| JsonRpcError] \| Any] \| None` | `None` | 可选的可调用对象，在方法调用前转换已解析的 `params`。 |

### 验证器协议

每个验证器接收已解析的 `params`，可以返回：

| 返回值 | 行为 |
|---|---|
| `Some(JsonRpcError)` | 以该错误拒绝 |
| `Some(Exception)` | 以包装在 `InvalidParams` 中的该错误拒绝 |
| `False` | 以通用 `InvalidParams` 错误拒绝 |
| `Exception` 或 `JsonRpcError` | 直接以该错误拒绝 |
| `True`、`None` 或任何其他真值 | 接受 — 继续到转换或方法调用 |

### 转换器协议

转换器接收原始 `params` 载荷，可以返回：

| 返回值 | 行为 |
|---|---|
| `Some(value)` | 使用 `value` 作为方法参数 |
| `Nothing()` | 以 `ConversionError` 拒绝 |
| `Ok(value)` | 使用 `value` 作为方法参数 |
| `Err(reason)` | 以 `ConversionError` 拒绝，将 `reason` 附加到 `data` |
| 任何其他值 | 直接使用该值作为方法参数 |
| 抛出 `Exception` | 以 `ConversionError` 拒绝，将异常附加到 `data` |

### 属性

| 属性 | 类型 | 描述 |
|---|---|---|
| `name` | `str` | 此包装器注册的 JSON-RPC 方法名称。 |

### 方法

#### `__hash__() -> int`

返回基于方法名称的哈希值。同名的两个包装器具有相同的哈希值。

#### `__eq__(other) -> bool`

通过方法名称比较两个包装器。

#### `__call__(params: Option[Any]) -> Result[Any, JsonRpcError]`

使用可选参数执行被包装的方法。验证在转换之前运行，然后调用方法；如果任一步骤拒绝参数，调用将以 `Err` 短路返回。

| 参数 | 类型 | 描述 |
|---|---|---|
| `params` | `Option[Any]` | 包含方法参数的 `Option`。`Some` 表示提供了参数；`Nothing` 表示没有参数。 |

**返回值：** 成功时返回 `Ok(result)`，失败时返回 `Err(JsonRpcError)`。

```python
>>> from pyfplib import Some, Nothing, Result
>>> wrapper = JsonRpcMethodWrapper(name="add", method=lambda a: a[0] + a[1])
>>> wrapper(Some([1, 2]))
Result.ok(3)
>>> wrapper(Nothing())
Result.ok(...)  # 调用无参数的方法
```

---

## `JsonRpcHandlerCollection`

```python
class JsonRpcHandlerCollection
```

以方法名称为键的 `JsonRpcMethodWrapper` 实例注册表。

### 构造函数

```python
JsonRpcHandlerCollection()
```

初始化一个空的处理程序集合。

### 方法

#### `add(method: JsonRpcMethodWrapper) -> bool`

注册一个方法包装器。如果同名方法已存在，则调用不执行任何操作。

| 参数 | 类型 | 描述 |
|---|---|---|
| `method` | `JsonRpcMethodWrapper` | 要注册的包装器。 |

**返回值：** 如果方法是新注册的返回 `True`，如果已存在返回 `False`。

```python
>>> collection = JsonRpcHandlerCollection()
>>> wrapper = JsonRpcMethodWrapper(name="add", method=lambda a: a)
>>> collection.add(wrapper)
True
>>> collection.add(wrapper)  # 重复
False
```

#### `try_get(name: str) -> Option[JsonRpcMethodWrapper]`

按名称查找方法。

| 参数 | 类型 | 描述 |
|---|---|---|
| `name` | `str` | JSON-RPC 方法名称。 |

**返回值：** 找到时返回 `Some(wrapper)`，否则返回 `Nothing`。

#### `exists(name: str) -> bool`

检查方法是否已注册。

| 参数 | 类型 | 描述 |
|---|---|---|
| `name` | `str` | JSON-RPC 方法名称。 |

**返回值：** 如果存在同名包装器返回 `True`。

#### `remove_by_name(name: str) -> bool`

按名称移除方法。

| 参数 | 类型 | 描述 |
|---|---|---|
| `name` | `str` | 要移除的 JSON-RPC 方法名称。 |

**返回值：** 如果方法存在并被移除返回 `True`，否则返回 `False`。

#### `remove(method: str | JsonRpcMethodWrapper) -> bool`

按名称或包装器实例移除方法。

| 参数 | 类型 | 描述 |
|---|---|---|
| `method` | `str \| JsonRpcMethodWrapper` | 方法名称字符串或 `JsonRpcMethodWrapper`。 |

**返回值：** 如果方法存在并被移除返回 `True`，否则返回 `False`。

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

将传入的 JSON-RPC 消息路由到已注册的处理程序。维护请求（期望响应）和通知（即发即忘）的独立注册表。

### 构造函数

```python
JsonRpcDispatcher(
    response_handler: Callable[[JsonRpcResponse], None] | None = None,
)
```

| 参数 | 类型 | 默认值 | 描述 |
|---|---|---|---|
| `response_handler` | `Callable[[JsonRpcResponse], None] \| None` | `None` | 当 `JsonRpcResponse` 被直接调度时调用的可选回调。 |

### 类属性

| 属性 | 类型 | 描述 |
|---|---|---|
| `ERROR_CASE` | `JsonRpcResponseCtorWrapper.State` | 错误响应的结果选择器。 |
| `RESULT_CASE` | `JsonRpcResponseCtorWrapper.State` | 成功结果的结果选择器。 |
| `BOTH_CASES` | `JsonRpcResponseCtorWrapper._When` | 匹配两种结果的结果选择器。 |

### 属性

| 属性 | 类型 | 描述 |
|---|---|---|
| `request_handler_registry` | `JsonRpcHandlerCollection` | 请求处理程序注册表。 |
| `notification_handler_registry` | `JsonRpcHandlerCollection` | 通知处理程序注册表。 |

### 方法

#### `emplace_request_handler(*, name, method, validator=None, converter=None) -> bool`

一次性注册请求处理程序。`request_handler_registry.add(JsonRpcMethodWrapper(...))` 的便捷方法。

| 参数 | 类型 | 默认值 | 描述 |
|---|---|---|---|
| `name` | `str` | *（必填）* | JSON-RPC 方法名称。 |
| `method` | `Callable[..., Any]` | *（必填）* | 被调度时调用的可调用对象。 |
| `validator` | `Callable[..., Option[JsonRpcError] \| bool] \| None` | `None` | 可选的参数验证器。 |
| `converter` | `Callable[..., Option[Any] \| Result[Any, Exception \| JsonRpcError] \| Any] \| None` | `None` | 可选的参数转换器。 |

**返回值：** 新注册时返回 `True`，名称已存在时返回 `False`。

#### `emplace_notification_handler(*, name, method, validator=None, converter=None) -> bool`

一次性注册通知处理程序。`notification_handler_registry.add(JsonRpcMethodWrapper(...))` 的便捷方法。

| 参数 | 类型 | 默认值 | 描述 |
|---|---|---|---|
| `name` | `str` | *（必填）* | JSON-RPC 方法名称。 |
| `method` | `Callable[..., Any]` | *（必填）* | 被调度时调用的可调用对象。 |
| `validator` | `Callable[..., Option[JsonRpcError] \| bool] \| None` | `None` | 可选的参数验证器。 |
| `converter` | `Callable[..., Option[Any] \| Result[Any, Exception \| JsonRpcError] \| Any] \| None` | `None` | 可选的参数转换器。 |

**返回值：** 新注册时返回 `True`，名称已存在时返回 `False`。

#### `emplace_custom_response_ctor(method, ctor, *states)`

为 *method* 注册自定义响应构造函数。

| 参数 | 类型 | 描述 |
|---|---|---|
| `method` | `str` | 构造函数适用的 JSON-RPC 方法名称。 |
| `ctor` | `Callable[..., JsonRpcResponse]` | 构建 `JsonRpcResponse` 的可调用对象。 |
| `*states` | `JsonRpcResponseCtorWrapper.State` | 可选的状态成员，限制 *ctor* 的使用时机。 |

#### `add_custom_response_ctor(ctor: JsonRpcResponseCtorWrapper)`

注册预构建的自定义响应构造函数。替换同一方法之前注册的任何构造函数。

| 参数 | 类型 | 描述 |
|---|---|---|
| `ctor` | `JsonRpcResponseCtorWrapper` | 将构造函数绑定到方法名称的包装器。 |

#### `__call__(data) -> Option[Result[JsonRpcResponse, JsonRpcError]]`

调度 JSON-RPC 消息。

| 参数 | 类型 | 描述 |
|---|---|---|
| `data` | `str \| JsonRpcRequest \| JsonRpcNotification \| JsonRpcResponse \| Result[...]` | JSON 字符串、`JsonRpcRequest`、`JsonRpcNotification`、`JsonRpcResponse` 或 `Result`。 |

**返回值：**

| 输入 | 找到处理程序 | 未找到处理程序 |
|---|---|---|
| `str`（解析成功） | 委托给请求/通知处理 | — |
| `str`（解析失败） | `Some(Err(ParseError))` | — |
| `JsonRpcRequest` | `Some(Ok(response))` | `Some(Err(MethodNotFound))`（通过响应） |
| `JsonRpcNotification` | `Nothing`（成功） | `Some(Err(MethodNotFound))` |
| 未知类型 | `Some(Err(InternalError))` | — |

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

尝试将 JSON 字符串解析为响应、请求或通知。首先尝试 `JsonRpcResponse`；失败时回退到 `JsonRpcNotification`；失败时回退到 `JsonRpcRequest`。

| 参数 | 类型 | 描述 |
|---|---|---|
| `data` | `str` | JSON 编码字符串。 |

**返回值：** 成功时返回 `Ok(response | notification | request)`，解析失败时返回 `Err(JsonRpcError)`。

---

## `JsonRpcResponseCtorWrapper`

```python
class JsonRpcResponseCtorWrapper
```

将自定义 `JsonRpcResponse` 构造函数绑定到方法名称。包装器记录构造函数何时适用 — 成功结果、错误或两者 — 以便调度器可以为每种结果选择正确的响应类型。

### 构造函数

```python
JsonRpcResponseCtorWrapper(
    method: str,
    ctor: Callable[..., JsonRpcResponse],
    *states: JsonRpcResponseCtorWrapper.State,
)
```

| 参数 | 类型 | 默认值 | 描述 |
|---|---|---|---|
| `method` | `str` | *（必填）* | 构造函数适用的 JSON-RPC 方法名称。 |
| `ctor` | `Callable[..., JsonRpcResponse]` | *（必填）* | 接收关键字参数（`id`、`result` 或 `error` 以及 `jsonrpc`）并返回 `JsonRpcResponse` 的可调用对象。 |
| `*states` | `State` | 两种结果 | 可选的 `State` 成员，限制 *ctor* 的使用时机。 |

### 内部类：`State`

```python
class State(Enum)
```

控制构造函数何时适用的结果选择器。

| 成员 | 值 | 描述 |
|---|---|---|
| `Result` | `1` | 构造函数处理成功结果。 |
| `Error` | `2` | 构造函数处理错误响应。 |

### 属性

| 属性 | 类型 | 描述 |
|---|---|---|
| `method` | `str` | 构造函数绑定的 JSON-RPC 方法名称。 |
| `when` | `_When` | 此构造函数的结果选择器。 |
