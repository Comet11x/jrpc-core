# API сообщений

Все примитивы сообщений находятся в модуле `jrpc_core.messages`.

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

## Типовые алиасы

### `JsonRpcId`

```python
JsonRpcId = str | int | float | None
```

Типовый алиас для идентификатора сообщения JSON-RPC. Допустимый идентификатор — это `str`, `int`, `float` или `None`. Вариант `None` допускается только в уведомлениях.

### `JsonRpcParams`

```python
JsonRpcParams = dict[str, Any] | list[Any] | None
```

Типовый алиас для значений `params` JSON-RPC. Параметры могут быть именованным отображением (`dict`), позиционным списком (`list`) или `None`, если они опущены.

---

## `JsonRpcErrorCode`

```python
class JsonRpcErrorCode(Enum)
```

Перечисление стандартных кодов ошибок JSON-RPC 2.0. Каждый элемент соответствует целочисленному коду, определённому спецификацией или распространёнными расширениями (`-32xxx` — зарезервировано, `-320xx` — определяется сервером).

### Элементы

| Член | Значение | Описание |
|---|---|---|
| `ParseError` | `-32700` | Сервер получил некорректный JSON. |
| `InternalError` | `-32603` | Произошла внутренняя ошибка JSON-RPC. |
| `InvalidParams` | `-32602` | Параметры, переданные с методом, невалидны. |
| `MethodNotFound` | `-32601` | Метод не существует или недоступен. |
| `InvalidRequest` | `-32600` | Отправленный JSON не является валидным объектом запроса. |
| `ExecutionError` | `-32000` | Произошла ошибка выполнения, определённая сервером. |

### Методы

#### `__int__() -> int`

Возвращает целочисленное значение этого кода ошибки.

```python
>>> int(JsonRpcErrorCode.ParseError)
-32700
```

#### `description() -> str`

Возвращает описание этого кода ошибки в человекочитаемом виде.

```python
>>> JsonRpcErrorCode.ParseError.description()
'Parse error'
```

#### `default() -> JsonRpcErrorCode` *(статический)*

Возвращает код ошибки по умолчанию, используемый когда ни один другой код не подходит. Возвращает `InternalError`.

```python
>>> JsonRpcErrorCode.default()
<JsonRpcErrorCode.InternalError: -32603>
```

#### `into(data: Any = None) -> JsonRpcError`

Создаёт `JsonRpcError` из этого кода.

| Параметр | Тип | По умолчанию | Описание |
|---|---|---|---|
| `data` | `Any` | `None` | Необязательные дополнительные данные, привязанные к ошибке. |

**Возвращает:** Новый `JsonRpcError` с этим кодом и его описанием.

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

Поддерживаемые версии протокола JSON-RPC.

| Член | Значение |
|---|---|
| `Version1` | `"1.0"` |
| `Version2` | `"2.0"` |

---

## `JsonRpcError`

```python
class JsonRpcError(BaseModel)
```

Объект ошибки JSON-RPC 2.0.

### Атрибуты

| Атрибут | Тип | По умолчанию | Описание |
|---|---|---|---|
| `code` | `JsonRpcErrorCode \| int` | `JsonRpcErrorCode.InternalError` | Целочисленный код ошибки. |
| `message` | `str` | `"Something went wrong"` | Краткое описание в человекочитаемом виде. |
| `data` | `Any \| None` | `None` | Необязательная дополнительная информация об ошибке. |

### Методы

#### `default() -> JsonRpcError` *(статический)*

Возвращает ошибку по умолчанию с `JsonRpcErrorCode.InternalError`.

```python
>>> JsonRpcError.default()
JsonRpcError(code=<JsonRpcErrorCode.InternalError: -32603>, message='Something went wrong', data=None)
```

#### `from_error(error: JsonRpcError | Any) -> JsonRpcError` *(статический)*

Преобразует произвольное значение в `JsonRpcError`. Если *error* уже является `JsonRpcError`, возвращается как есть. В противном случае функция пытается извлечь атрибут `code` и формирует ошибку вокруг него, используя `JsonRpcErrorCode.InternalError` как запасной вариант.

| Параметр | Тип | Описание |
|---|---|---|
| `error` | `JsonRpcError \| Any` | Значение для преобразования. |

**Возвращает:** Экземпляр `JsonRpcError`.

```python
>>> JsonRpcError.from_error(RuntimeError("oops"))
JsonRpcError(code=<JsonRpcErrorCode.InternalError: -32603>, message='Internal error', data=RuntimeError('oops'))
```

#### `try_from(value: Option[JsonRpcError | Any]) -> Option[JsonRpcError]` *(статический)*

Пытается преобразовать `Option` в ошибку.

| Параметр | Тип | Описание |
|---|---|---|
| `value` | `Option[JsonRpcError \| Any]` | `Option`, который может содержать значение для преобразования. |

**Возвращает:** `Some(JsonRpcError)`, если *value* был `Some`, иначе `Nothing`.

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

Объект запроса JSON-RPC 2.0. Содержит имя `method`, необязательные параметры `params` и `id`, который клиент использует для сопоставления с ответом.

### Атрибуты

| Атрибут | Тип | По умолчанию | Описание |
|---|---|---|---|
| `method` | `str` | *(обязательный)* | Имя вызываемой удалённой процедуры. Должна быть непустой строкой. |
| `id` | `JsonRpcId` | `str(uuid4())` | Уникальный идентификатор этого запроса (по умолчанию — автоматически сгенерированный UUID). |
| `params` | `JsonRpcParams` | `None` | Необязательные позиционные или именованные аргументы метода. |
| `jsonrpc` | `JsonRpcVersion` | `Version2` | Версия протокола. |

### Методы

#### `try_from_dict(data: dict) -> Result[JsonRpcRequest, Exception]` *(classmethod)*

Пытается создать запрос из простого словаря.

| Параметр | Тип | Описание |
|---|---|---|
| `data` | `dict[str, Any]` | Словарь с полями запроса JSON-RPC. |

**Возвращает:** `Ok(request)` при успехе или `Err(exception)` при ошибке валидации.

```python
>>> JsonRpcRequest.try_from_dict({"method": "add", "id": 1}).is_ok()
True
```

#### `try_from_json(data: str) -> Result[JsonRpcRequest, Exception]` *(classmethod)*

Пытается создать запрос из JSON-строки.

| Параметр | Тип | Описание |
|---|---|---|
| `data` | `str` | JSON-строка, представляющая запрос. |

**Возвращает:** `Ok(request)` при успехе или `Err(exception)` при ошибке парсинга/валидации.

```python
>>> JsonRpcRequest.try_from_json('{"method":"add","id":1}').is_ok()
True
```

#### `to_dict() -> dict[str, Any]`

Сериализует запрос в простой словарь. Ключ `params` опускается, если значение — `None`.

**Возвращает:** Словарь, пригодный для JSON-сериализации.

```python
>>> JsonRpcRequest(method="add", params=[1, 2]).to_dict()
{'method': 'add', 'id': '<uuid>', 'params': [1, 2], 'jsonrpc': '2.0'}
```

#### `to_json() -> str`

Сериализует запрос в JSON-строку.

**Возвращает:** Компактное JSON-представление этого запроса.

#### `into(result: Result[Any, JsonRpcError]) -> JsonRpcResponse`

Создаёт `JsonRpcResponse` из результата обработчика. Принимает `Result`, `JsonRpcError` или сырое значение.

| Параметр | Тип | Описание |
|---|---|---|
| `result` | `Result[Any, JsonRpcError]` | Результат обработки этого запроса. |

**Возвращает:** Ответ, содержащий либо распакованный результат, либо ошибку.

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

Объект уведомления JSON-RPC 2.0. Идентичен запросу, но не содержит поля `id`, что указывает на то, что ответ от сервера не ожидается.

### Атрибуты

| Атрибут | Тип | По умолчанию | Описание |
|---|---|---|---|
| `method` | `str` | *(обязательный)* | Имя объявляемого события или процедуры. Должна быть непустой строкой. |
| `params` | `JsonRpcParams` | `None` | Необязательные позиционные или именованные аргументы. |
| `jsonrpc` | `JsonRpcVersion` | `Version2` | Версия протокола. |

::: warning
Уведомление **не** должно содержать поле `id`. Попытка создать уведомление с `id` вызывает ошибку валидации.
:::

### Методы

#### `try_from_dict(data: dict) -> Result[JsonRpcNotification, Exception]` *(classmethod)*

Пытается создать уведомление из простого словаря.

| Параметр | Тип | Описание |
|---|---|---|
| `data` | `dict[str, Any]` | Словарь с полями уведомления JSON-RPC. |

**Возвращает:** `Ok(notification)` при успехе или `Err(exception)` при ошибке валидации.

#### `try_from_json(data: str) -> Result[JsonRpcNotification, Exception]` *(classmethod)*

Пытается создать уведомление из JSON-строки.

| Параметр | Тип | Описание |
|---|---|---|
| `data` | `str` | JSON-строка, представляющая уведомление. |

**Возвращает:** `Ok(notification)` при успехе или `Err(exception)` при ошибке парсинга/валидации.

#### `to_dict() -> dict[str, Any]`

Сериализует уведомление в простой словарь. Ключ `params` опускается, если значение — `None`.

**Возвращает:** Словарь, пригодный для JSON-сериализации.

#### `to_json() -> str`

Сериализует уведомление в JSON-строку.

**Возвращает:** Компактное JSON-представление этого уведомления.

---

## `JsonRpcResponse`

```python
class JsonRpcResponse(BaseModel)
```

Объект ответа JSON-RPC 2.0. Ровно одно из полей `result` или `error` должно быть установлено. Поле `id` соответствует `id` исходного запроса.

### Атрибуты

| Атрибут | Тип | По умолчанию | Описание |
|---|---|---|---|
| `id` | `JsonRpcId` | *(обязательный)* | Идентификатор запроса, которому соответствует этот ответ. |
| `result` | `Any` | `None` | Возвращаемое значение при успешном выполнении метода. |
| `error` | `JsonRpcError \| None` | `None` | `JsonRpcError` при сбое метода. |
| `jsonrpc` | `JsonRpcVersion` | `Version2` | Версия протокола. |

::: warning
Ответ должен содержать **либо** `result`, **либо** `error`, но не оба. Попытка установить оба поля вызывает ошибку валидации.
:::

### Методы

#### `from_result(id, result) -> JsonRpcResponse` *(статический)*

Создаёт ответ из `Result`.

| Параметр | Тип | Описание |
|---|---|---|
| `id` | `JsonRpcId` | Идентификатор запроса для возврата. |
| `result` | `Result[Any, JsonRpcError]` | Результат обработчика. |

**Возвращает:** Полностью сформированный `JsonRpcResponse`.

```python
>>> from pyfplib import Result
>>> JsonRpcResponse.from_result(1, Result.ok("data"))
JsonRpcResponse(id=1, result='data', error=None, ...)
>>> JsonRpcResponse.from_result(2, Result.err(JsonRpcError(code=JsonRpcErrorCode.InternalError)))
JsonRpcResponse(id=2, result=None, error=JsonRpcError(...), ...)
```

#### `from_jrpc_error(id, error) -> JsonRpcResponse` *(статический)*

Создаёт ответ с ошибкой.

| Параметр | Тип | Описание |
|---|---|---|
| `id` | `JsonRpcId` | Идентификатор запроса для возврата. |
| `error` | `JsonRpcError` | Ошибка для включения в ответ. |

**Возвращает:** `JsonRpcResponse` с установленным только полем `error`.

#### `from_jrpc_result(id, result) -> JsonRpcResponse` *(статический)*

Создаёт успешный ответ.

| Параметр | Тип | Описание |
|---|---|---|
| `id` | `JsonRpcId` | Идентификатор запроса для возврата. |
| `result` | `Any` | Возвращаемое значение метода. |

**Возвращает:** `JsonRpcResponse` с установленным только полем `result`.

#### `try_from_dict(data: dict) -> Result[JsonRpcResponse, Exception]` *(статический)*

Пытается создать ответ из простого словаря.

| Параметр | Тип | Описание |
|---|---|---|
| `data` | `dict[str, Any]` | Словарь с полями ответа JSON-RPC. |

**Возвращает:** `Ok(response)` при успехе или `Err(exception)` при ошибке валидации.

#### `try_from_json(data: str) -> Result[JsonRpcResponse, Exception]` *(статический)*

Пытается создать ответ из JSON-строки.

| Параметр | Тип | Описание |
|---|---|---|
| `data` | `str` | JSON-строка, представляющая ответ. |

**Возвращает:** `Ok(response)` при успехе или `Err(exception)` при ошибке парсинга/валидации.

#### `to_dict() -> dict[str, Any]`

Сериализует ответ в простой словарь. Если присутствует `error`, ключ `result` удаляется, а код ошибки приводится к `int`. Если присутствует `result`, ключ `error` удаляется.

**Возвращает:** Словарь, пригодный для JSON-сериализации.

#### `to_json() -> str`

Сериализует ответ в JSON-строку.

**Возвращает:** Компактное JSON-представление этого ответа.

---

## `try_parse()`

```python
def try_parse(data: str) -> Result[JsonRpcRequest | JsonRpcNotification, JsonRpcError]
```

Пытается распарсить JSON-строку как сообщение JSON-RPC. Функция сначала пытается распарсить как `JsonRpcRequest`; при неудаче переходит к `JsonRpcNotification`. Если обе попытки не удаются, возвращается ошибка парсинга от попытки разбора запроса.

| Параметр | Тип | Описание |
|---|---|---|
| `data` | `str` | JSON-строка. |

**Возвращает:** `Ok(request | notification)` при успехе или `Err(JsonRpcError)` с ошибкой парсинга.

::: warning
Поскольку `JsonRpcRequest` использует `uuid4()` для генерации значения `id` по умолчанию, payload уведомления (без `id`) будет успешно распарсен как запрос. Используйте `JsonRpcNotification.try_from_json` напрямую, когда необходимо гарантировать форму уведомления.
:::

```python
>>> try_parse('{"jsonrpc":"2.0","method":"add","id":1}')
Result.ok(JsonRpcRequest(method='add', id=1, ...))
```
