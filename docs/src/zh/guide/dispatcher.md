# 调度器 API

调度器层位于 `jrpc_core.dispatcher` 模块中。

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

将可调用对象包装为带有可选参数验证器的 JSON-RPC 方法。

### 构造函数

```python
JsonRpcMethodWrapper(
    *,
    name: str,
    method: Callable[..., Any],
    validators: list[Callable[..., Option[JsonRpcError]]] | None = None,
)
```

| 参数 | 类型 | 默认值 | 描述 |
|---|---|---|---|
| `name` | `str` | *（必填）* | JSON-RPC 方法名称。 |
| `method` | `Callable[..., Any]` | *（必填）* | 此方法被调度时调用的可调用对象。 |
| `validators` | `list[Callable[..., Option[JsonRpcError]]] \| None` | `None` | 可选的可调用对象列表，接收已解析的 `params` 并返回拒绝信号。 |

### 验证器协议

每个验证器接收已解析的 `params`，可以返回：

| 返回值 | 行为 |
|---|---|
| `Some(JsonRpcError)` 或 `Some(Exception)` | 以包装在 `InvalidParams` 中的该错误拒绝 |
| `False` | 以通用 `InvalidParams` 错误拒绝 |
| `Exception` 或 `JsonRpcError` | 直接以该错误拒绝 |
| `True`、`None` 或任何其他真值 | 接受 — 继续到下一个验证器或方法调用 |

### 属性

| 属性 | 类型 | 描述 |
|---|---|---|
| `name` | `str` | 此包装器注册的 JSON-RPC 方法名称。 |

### 方法

#### `__hash__() -> int`

返回基于方法名称的哈希值。同名的两个包装器具有相同的哈希值。

#### `__eq__(other) -> bool`

通过方法名称比较两个包装器。

#### `__call__(args: Option[Any]) -> Result[Any, JsonRpcError]`

使用可选参数执行被包装的方法。验证器在方法之前运行。如果任何验证器拒绝参数，调用将以 `Err` 短路返回。

| 参数 | 类型 | 描述 |
|---|---|---|
| `args` | `Option[Any]` | 包含方法参数的 `Option`。`Some` 表示提供了参数；`None` 表示没有参数。 |

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
JsonRpcDispatcher()
```

使用空的处理程序注册表初始化调度器。

### 属性

| 属性 | 类型 | 描述 |
|---|---|---|
| `request_handler_registry` | `JsonRpcHandlerCollection` | 请求处理程序注册表。 |
| `notification_handler_registry` | `JsonRpcHandlerCollection` | 通知处理程序注册表。 |

### 方法

#### `__call__(data: str | JsonRpcRequest | JsonRpcNotification) -> Option[Result[JsonRpcResponse, JsonRpcError]]`

调度 JSON-RPC 消息。

| 参数 | 类型 | 描述 |
|---|---|---|
| `data` | `str \| JsonRpcRequest \| JsonRpcNotification` | JSON 字符串、`JsonRpcRequest` 或 `JsonRpcNotification`。 |

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

#### `try_parse(data: str) -> Result[JsonRpcRequest | JsonRpcNotification, JsonRpcError]` *(classmethod)*

尝试将 JSON 字符串解析为请求或通知。首先尝试 `JsonRpcRequest`；失败时回退到 `JsonRpcNotification`。

| 参数 | 类型 | 描述 |
|---|---|---|
| `data` | `str` | JSON 编码字符串。 |

**返回值：** 成功时返回 `Ok(request | notification)`，解析失败时返回 `Err(JsonRpcError)`。
