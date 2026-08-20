# 消息 API

所有消息原语都位于 `jrpc_core.messages` 模块中。

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

## 类型别名

### `JsonRpcId`

```python
JsonRpcId = str | int | float | None
```

JSON-RPC 消息标识符的类型别名。有效的标识符为 `str`、`int`、`float` 或 `None`。`None` 变体仅在通知中允许使用。

### `JsonRpcParams`

```python
JsonRpcParams = dict[str, Any] | list[Any] | None
```

JSON-RPC `params` 值的类型别名。参数可以是命名映射（`dict`）、位置列表（`list`）或省略时的 `None`。

---

## `JsonRpcErrorCode`

```python
class JsonRpcErrorCode(Enum)
```

标准 JSON-RPC 2.0 错误码的枚举。每个成员映射到规范或常见扩展中定义的整数代码（`-32xxx` 保留，`-320xx` 服务器自定义）。

### 成员

| 成员 | 值 | 描述 |
|---|---|---|
| `ParseError` | `-32700` | 服务器接收到无效的 JSON。 |
| `InternalError` | `-32603` | 发生内部 JSON-RPC 错误。 |
| `InvalidParams` | `-32602` | 随方法发送的参数无效。 |
| `MethodNotFound` | `-32601` | 方法不存在或不可用。 |
| `InvalidRequest` | `-32600` | 发送的 JSON 不是有效的请求对象。 |
| `ExecutionError` | `-32000` | 发生服务器定义的执行错误。 |

### 方法

#### `__int__() -> int`

返回此错误码的整数值。

```python
>>> int(JsonRpcErrorCode.ParseError)
-32700
```

#### `description() -> str`

返回此错误码的人类可读描述。

```python
>>> JsonRpcErrorCode.ParseError.description()
'Parse error'
```

#### `default() -> JsonRpcErrorCode` *(static)*

返回没有其他代码适用时使用的默认错误码。返回 `InternalError`。

```python
>>> JsonRpcErrorCode.default()
<JsonRpcErrorCode.InternalError: -32603>
```

#### `into(data: Any = None) -> JsonRpcError`

从此代码创建一个 `JsonRpcError`。

| 参数 | 类型 | 默认值 | 描述 |
|---|---|---|---|
| `data` | `Any` | `None` | 附加到错误的可选额外载荷。 |

**返回值：** 一个包含此代码及其描述的新 `JsonRpcError`。

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

支持的 JSON-RPC 协议版本。

| 成员 | 值 |
|---|---|
| `Version1` | `"1.0"` |
| `Version2` | `"2.0"` |

---

## `JsonRpcError`

```python
class JsonRpcError(BaseModel)
```

JSON-RPC 2.0 错误对象。

### 属性

| 属性 | 类型 | 默认值 | 描述 |
|---|---|---|---|
| `code` | `JsonRpcErrorCode \| int` | `JsonRpcErrorCode.InternalError` | 整数错误码。 |
| `message` | `str` | `"Something went wrong"` | 简短的人类可读描述。 |
| `data` | `Any \| None` | `None` | 关于错误的可选额外信息。 |

### 方法

#### `default() -> JsonRpcError` *(static)*

返回一个包含 `JsonRpcErrorCode.InternalError` 的默认错误。

```python
>>> JsonRpcError.default()
JsonRpcError(code=<JsonRpcErrorCode.InternalError: -32603>, message='Something went wrong', data=None)
```

#### `from_error(error: JsonRpcError | Any) -> JsonRpcError` *(static)*

将任意值转换为 `JsonRpcError`。如果 *error* 已经是 `JsonRpcError`，则原样返回。否则，函数尝试提取 `code` 属性并围绕它构建错误，回退到 `JsonRpcErrorCode.InternalError`。

| 参数 | 类型 | 描述 |
|---|---|---|
| `error` | `JsonRpcError \| Any` | 要转换的值。 |

**返回值：** 一个 `JsonRpcError` 实例。

```python
>>> JsonRpcError.from_error(RuntimeError("oops"))
JsonRpcError(code=<JsonRpcErrorCode.InternalError: -32603>, message='Internal error', data=RuntimeError('oops'))
```

#### `try_from(value: Option[JsonRpcError | Any]) -> Option[JsonRpcError]` *(static)*

尝试将 `Option` 转换为错误。

| 参数 | 类型 | 描述 |
|---|---|---|
| `value` | `Option[JsonRpcError \| Any]` | 一个可能包含要转换值的 `Option`。 |

**返回值：** 如果 *value* 是 `Some`，则返回 `Some(JsonRpcError)`，否则返回 `Nothing`。

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

JSON-RPC 2.0 请求对象。包含一个 `method` 名称、一个可选的 `params` 载荷，以及客户端用于关联响应的 `id`。

### 属性

| 属性 | 类型 | 默认值 | 描述 |
|---|---|---|---|
| `method` | `str` | *（必填）* | 要调用的远程过程名称。必须是非空字符串。 |
| `id` | `JsonRpcId` | `str(uuid4())` | 此请求的唯一标识符（默认为自动生成的 UUID）。 |
| `params` | `JsonRpcParams` | `None` | 方法的可选位置参数或命名参数。 |
| `jsonrpc` | `JsonRpcVersion` | `Version2` | 协议版本。 |

### 方法

#### `try_from_dict(data: dict) -> Result[JsonRpcRequest, Exception]` *(classmethod)*

尝试从普通字典构建请求。

| 参数 | 类型 | 描述 |
|---|---|---|
| `data` | `dict[str, Any]` | 包含 JSON-RPC 请求字段的字典。 |

**返回值：** 成功时返回 `Ok(request)`，验证失败时返回 `Err(exception)`。

```python
>>> JsonRpcRequest.try_from_dict({"method": "add", "id": 1}).is_ok()
True
```

#### `try_from_json(data: str) -> Result[JsonRpcRequest, Exception]` *(classmethod)*

尝试从 JSON 字符串构建请求。

| 参数 | 类型 | 描述 |
|---|---|---|
| `data` | `str` | 表示请求的 JSON 编码字符串。 |

**返回值：** 成功时返回 `Ok(request)`，解析/验证失败时返回 `Err(exception)`。

```python
>>> JsonRpcRequest.try_from_json('{"method":"add","id":1}').is_ok()
True
```

#### `to_dict() -> dict[str, Any]`

将请求序列化为普通字典。当 `params` 为 `None` 时省略 `params` 键。

**返回值：** 适合 JSON 序列化的字典。

```python
>>> JsonRpcRequest(method="add", params=[1, 2]).to_dict()
{'method': 'add', 'id': '<uuid>', 'params': [1, 2], 'jsonrpc': '2.0'}
```

#### `to_json() -> str`

将请求序列化为 JSON 字符串。

**返回值：** 此请求的紧凑 JSON 表示。

#### `into(result: Result[Any, JsonRpcError]) -> JsonRpcResponse`

从处理程序结果创建 `JsonRpcResponse`。接受 `Result`、`JsonRpcError` 或原始值。

| 参数 | 类型 | 描述 |
|---|---|---|
| `result` | `Result[Any, JsonRpcError]` | 处理此请求的结果。 |

**返回值：** 一个携带解包结果或错误的响应。

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

JSON-RPC 2.0 通知对象。与请求相同，但省略 `id` 字段，表示不期望服务器响应。

### 属性

| 属性 | 类型 | 默认值 | 描述 |
|---|---|---|---|
| `method` | `str` | *（必填）* | 被通知的事件或过程名称。必须是非空字符串。 |
| `params` | `JsonRpcParams` | `None` | 可选的位置参数或命名参数。 |
| `jsonrpc` | `JsonRpcVersion` | `Version2` | 协议版本。 |

::: warning
通知**不能**包含 `id` 字段。尝试使用 `id` 构造通知会引发验证错误。
:::

### 方法

#### `try_from_dict(data: dict) -> Result[JsonRpcNotification, Exception]` *(classmethod)*

尝试从普通字典构建通知。

| 参数 | 类型 | 描述 |
|---|---|---|
| `data` | `dict[str, Any]` | 包含 JSON-RPC 通知字段的字典。 |

**返回值：** 成功时返回 `Ok(notification)`，验证失败时返回 `Err(exception)`。

#### `try_from_json(data: str) -> Result[JsonRpcNotification, Exception]` *(classmethod)*

尝试从 JSON 字符串构建通知。

| 参数 | 类型 | 描述 |
|---|---|---|
| `data` | `str` | 表示通知的 JSON 编码字符串。 |

**返回值：** 成功时返回 `Ok(notification)`，解析/验证失败时返回 `Err(exception)`。

#### `to_dict() -> dict[str, Any]`

将通知序列化为普通字典。当 `params` 为 `None` 时省略 `params` 键。

**返回值：** 适合 JSON 序列化的字典。

#### `to_json() -> str`

将通知序列化为 JSON 字符串。

**返回值：** 此通知的紧凑 JSON 表示。

---

## `JsonRpcResponse`

```python
class JsonRpcResponse(BaseModel)
```

JSON-RPC 2.0 响应对象。`result` 和 `error` 必须恰好设置其中一个。`id` 与原始请求的 `id` 匹配。

### 属性

| 属性 | 类型 | 默认值 | 描述 |
|---|---|---|---|
| `id` | `JsonRpcId` | *（必填）* | 此响应对应的请求标识符。 |
| `result` | `Any` | `None` | 方法成功执行时的返回值。 |
| `error` | `JsonRpcError \| None` | `None` | 方法失败时的 `JsonRpcError`。 |
| `jsonrpc` | `JsonRpcVersion` | `Version2` | 协议版本。 |

::: warning
响应必须**要么**有 `result` **要么**有 `error`，不能同时有两者。尝试同时设置两者会引发验证错误。
:::

### 方法

#### `from_result(id, result) -> JsonRpcResponse` *(static)*

从 `Result` 构建响应。

| 参数 | 类型 | 描述 |
|---|---|---|
| `id` | `JsonRpcId` | 要回传的请求标识符。 |
| `result` | `Result[Any, JsonRpcError]` | 处理程序的结果。 |

**返回值：** 一个完整构造的 `JsonRpcResponse`。

```python
>>> from pyfplib import Result
>>> JsonRpcResponse.from_result(1, Result.ok("data"))
JsonRpcResponse(id=1, result='data', error=None, ...)
>>> JsonRpcResponse.from_result(2, Result.err(JsonRpcError(code=JsonRpcErrorCode.InternalError)))
JsonRpcResponse(id=2, result=None, error=JsonRpcError(...), ...)
```

#### `from_jrpc_error(id, error) -> JsonRpcResponse` *(static)*

构建错误响应。

| 参数 | 类型 | 描述 |
|---|---|---|
| `id` | `JsonRpcId` | 要回传的请求标识符。 |
| `error` | `JsonRpcError` | 要包含的错误。 |

**返回值：** 仅设置了 `error` 的 `JsonRpcResponse`。

#### `from_jrpc_result(id, result) -> JsonRpcResponse` *(static)*

构建成功响应。

| 参数 | 类型 | 描述 |
|---|---|---|
| `id` | `JsonRpcId` | 要回传的请求标识符。 |
| `result` | `Any` | 方法的返回值。 |

**返回值：** 仅设置了 `result` 的 `JsonRpcResponse`。

#### `try_from_dict(data: dict) -> Result[JsonRpcResponse, Exception]` *(static)*

尝试从普通字典构建响应。

| 参数 | 类型 | 描述 |
|---|---|---|
| `data` | `dict[str, Any]` | 包含 JSON-RPC 响应字段的字典。 |

**返回值：** 成功时返回 `Ok(response)`，验证失败时返回 `Err(exception)`。

#### `try_from_json(data: str) -> Result[JsonRpcResponse, Exception]` *(static)*

尝试从 JSON 字符串构建响应。

| 参数 | 类型 | 描述 |
|---|---|---|
| `data` | `str` | 表示响应的 JSON 编码字符串。 |

**返回值：** 成功时返回 `Ok(response)`，解析/验证失败时返回 `Err(exception)`。

#### `to_dict() -> dict[str, Any]`

将响应序列化为普通字典。当存在 `error` 时，`result` 键被移除且错误码被强制转换为 `int`。当存在 `result` 时，`error` 键被移除。

**返回值：** 适合 JSON 序列化的字典。

#### `to_json() -> str`

将响应序列化为 JSON 字符串。

**返回值：** 此响应的紧凑 JSON 表示。

---

## `try_parse()`

```python
def try_parse(data: str) -> Result[JsonRpcRequest | JsonRpcNotification, JsonRpcError]
```

尝试将 JSON 字符串解析为 JSON-RPC 消息。函数首先尝试解析为 `JsonRpcRequest`；如果失败则回退到 `JsonRpcNotification`。如果两者都失败，则返回请求尝试时的解析错误。

| 参数 | 类型 | 描述 |
|---|---|---|
| `data` | `str` | JSON 编码字符串。 |

**返回值：** 成功时返回 `Ok(request | notification)`，包含解析失败信息的 `Err(JsonRpcError)`。

::: warning
因为 `JsonRpcRequest` 通过 `uuid4()` 为 `id` 提供默认值，所以通知载荷（无 `id`）作为请求会成功。当需要强制通知形式时，请直接使用 `JsonRpcNotification.try_from_json`。
:::

```python
>>> try_parse('{"jsonrpc":"2.0","method":"add","id":1}')
Result.ok(JsonRpcRequest(method='add', id=1, ...))
```
