# API диспетчера

Слой диспетчера находится в модуле `jrpc_core.dispatcher`.

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

Оборачивает вызываемый объект как метод JSON-RPC с необязательными валидаторами и конвертерами параметров.

### Конструктор

```python
JsonRpcMethodWrapper(
    *,
    name: str,
    method: Callable[..., Any],
    validator: Callable[..., Option[JsonRpcError] | bool] | None = None,
    converter: Callable[..., Option[Any] | Result[Any, Exception | JsonRpcError] | Any] | None = None,
)
```

| Параметр | Тип | По умолчанию | Описание |
|---|---|---|---|
| `name` | `str` | *(обязательный)* | Имя метода JSON-RPC. |
| `method` | `Callable[..., Any]` | *(обязательный)* | Вызываемый объект, который выполняется при диспетчеризации этого метода. |
| `validator` | `Callable[..., Option[JsonRpcError] \| bool] \| None` | `None` | Необязательный вызываемый объект, который получает распарсенные `params` и возвращает сигнал отклонения. |
| `converter` | `Callable[..., Option[Any] \| Result[Any, Exception \| JsonRpcError] \| Any] \| None` | `None` | Необязательный вызываемый объект, который преобразует распарсенные `params` перед вызовом метода. |

### Протокол валидатора

Каждый валидатор получает распарсенные `params` и может вернуть:

| Возвращаемое значение | Поведение |
|---|---|
| `Some(JsonRpcError)` | Отклоняет с этой ошибкой |
| `Some(Exception)` | Отклоняет с ошибкой, обёрнутой в `InvalidParams` |
| `False` | Отклоняет с общей ошибкой `InvalidParams` |
| `Exception` или `JsonRpcError` | Отклоняет с этой ошибкой напрямую |
| `True`, `None` или любое другое истинное значение | Принимает — переходит к конвертеру или вызову метода |

### Протокол конвертера

Конвертер получает исходные `params` и может вернуть:

| Возвращаемое значение | Поведение |
|---|---|
| `Some(value)` | Использует `value` как аргумент метода |
| `Nothing()` | Отклоняет с `ConversionError` |
| `Ok(value)` | Использует `value` как аргумент метода |
| `Err(reason)` | Отклоняет с `ConversionError`, прикрепляя `reason` к `data` |
| Любое другое значение | Использует значение напрямую как аргумент метода |
| Выбрасывает `Exception` | Отклоняет с `ConversionError`, прикрепляя исключение к `data` |

### Атрибуты

| Атрибут | Тип | Описание |
|---|---|---|
| `name` | `str` | Имя метода JSON-RPC, под которым зарегистрирована эта обёртка. |

### Методы

#### `__hash__() -> int`

Возвращает хеш, основанный на имени метода. Две обёртки с одинаковым именем имеют одинаковый хеш.

#### `__eq__(other) -> bool`

Сравнивает две обёртки по имени метода.

#### `__call__(params: Option[Any]) -> Result[Any, JsonRpcError]`

Выполняет оборачиваемый метод с необязательными параметрами. Валидация запускается первой, затем конвертация; если любой шаг отклоняет параметры, вызов прерывается с `Err`.

| Параметр | Тип | Описание |
|---|---|---|
| `params` | `Option[Any]` | `Option`, содержащий параметры метода. `Some` означает, что параметры были предоставлены; `None` означает их отсутствие. |

**Возвращает:** `Ok(result)` при успехе или `Err(JsonRpcError)` при сбое.

```python
>>> from pyfplib import Some, Nothing, Result
>>> wrapper = JsonRpcMethodWrapper(name="add", method=lambda a: a[0] + a[1])
>>> wrapper(Some([1, 2]))
Result.ok(3)
>>> wrapper(Nothing())
Result.ok(...)  # вызывает метод без аргументов
```

---

## `JsonRpcHandlerCollection`

```python
class JsonRpcHandlerCollection
```

Реестр экземпляров `JsonRpcMethodWrapper`, ключированных по имени метода.

### Конструктор

```python
JsonRpcHandlerCollection()
```

Инициализирует пустую коллекцию обработчиков.

### Методы

#### `add(method: JsonRpcMethodWrapper) -> bool`

Регистрирует обёртку метода. Если метод с таким именем уже существует, вызов ничего не делает.

| Параметр | Тип | Описание |
|---|---|---|
| `method` | `JsonRpcMethodWrapper` | Обёртка для регистрации. |

**Возвращает:** `True`, если метод был зарегистрирован впервые, `False`, если он уже существовал.

```python
>>> collection = JsonRpcHandlerCollection()
>>> wrapper = JsonRpcMethodWrapper(name="add", method=lambda a: a)
>>> collection.add(wrapper)
True
>>> collection.add(wrapper)  # дубликат
False
```

#### `try_get(name: str) -> Option[JsonRpcMethodWrapper]`

Ищет метод по имени.

| Параметр | Тип | Описание |
|---|---|---|
| `name` | `str` | Имя метода JSON-RPC. |

**Возвращает:** `Some(wrapper)`, если найден, иначе `Nothing`.

#### `exists(name: str) -> bool`

Проверяет, зарегистрирован ли метод.

| Параметр | Тип | Описание |
|---|---|---|
| `name` | `str` | Имя метода JSON-RPC. |

**Возвращает:** `True`, если обёртка с таким именем существует.

#### `remove_by_name(name: str) -> bool`

Удаляет метод по имени.

| Параметр | Тип | Описание |
|---|---|---|
| `name` | `str` | Имя метода JSON-RPC для удаления. |

**Возвращает:** `True`, если метод существовал и был удалён, `False` в противном случае.

#### `remove(method: str | JsonRpcMethodWrapper) -> bool`

Удаляет метод по имени или экземпляру обёртки.

| Параметр | Тип | Описание |
|---|---|---|
| `method` | `str \| JsonRpcMethodWrapper` | Строка с именем метода или `JsonRpcMethodWrapper`. |

**Возвращает:** `True`, если метод существовал и был удалён, `False` в противном случае.

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

Маршрутизирует входящие сообщения JSON-RPC на зарегистрированные обработчики. Поддерживает отдельные реестры для запросов (ожидающих ответа) и уведомлений (одноразовых).

### Конструктор

```python
JsonRpcDispatcher(
    response_handler: Callable[[JsonRpcResponse], None] | None = None,
)
```

| Параметр | Тип | По умолчанию | Описание |
|---|---|---|---|
| `response_handler` | `Callable[[JsonRpcResponse], None] \| None` | `None` | Необязательный обратный вызов, вызываемый при прямой диспетчеризации `JsonRpcResponse`. |

### Атрибуты класса

| Атрибут | Тип | Описание |
|---|---|---|
| `ERROR_CASE` | `JsonRpcResponseCtorWrapper.State` | Селектор результата для ответов с ошибками. |
| `RESULT_CASE` | `JsonRpcResponseCtorWrapper.State` | Селектор результата для успешных ответов. |
| `BOTH_CASES` | `JsonRpcResponseCtorWrapper._When` | Селектор результата, совпадающий с обоими исходами. |

### Атрибуты

| Атрибут | Тип | Описание |
|---|---|---|
| `request_handler_registry` | `JsonRpcHandlerCollection` | Реестр обработчиков запросов. |
| `notification_handler_registry` | `JsonRpcHandlerCollection` | Реестр обработчиков уведомлений. |

### Методы

#### `emplace_request_handler(*, name, method, validator=None, converter=None) -> bool`

Регистрирует обработчик запросов за один вызов. Удобная замена `request_handler_registry.add(JsonRpcMethodWrapper(...))`.

| Параметр | Тип | По умолчанию | Описание |
|---|---|---|---|
| `name` | `str` | *(обязательный)* | Имя метода JSON-RPC. |
| `method` | `Callable[..., Any]` | *(обязательный)* | Вызываемый объект, который выполняется при диспетчеризации. |
| `validator` | `Callable[..., Option[JsonRpcError] \| bool] \| None` | `None` | Необязательный валидатор параметров. |
| `converter` | `Callable[..., Option[Any] \| Result[Any, Exception \| JsonRpcError] \| Any] \| None` | `None` | Необязательный конвертер параметров. |

**Возвращает:** `True`, если метод был зарегистрирован впервые, `False`, если имя уже существовало.

#### `emplace_notification_handler(*, name, method, validator=None, converter=None) -> bool`

Регистрирует обработчик уведомлений за один вызов. Удобная замена `notification_handler_registry.add(JsonRpcMethodWrapper(...))`.

| Параметр | Тип | По умолчанию | Описание |
|---|---|---|---|
| `name` | `str` | *(обязательный)* | Имя метода JSON-RPC. |
| `method` | `Callable[..., Any]` | *(обязательный)* | Вызываемый объект, который выполняется при диспетчеризации. |
| `validator` | `Callable[..., Option[JsonRpcError] \| bool] \| None` | `None` | Необязательный валидатор параметров. |
| `converter` | `Callable[..., Option[Any] \| Result[Any, Exception \| JsonRpcError] \| Any] \| None` | `None` | Необязательный конвертер параметров. |

**Возвращает:** `True`, если метод был зарегистрирован впервые, `False`, если имя уже существовало.

#### `emplace_custom_response_ctor(method, ctor, *states)`

Регистрирует пользовательский конструктор ответа для *method*.

| Параметр | Тип | Описание |
|---|---|---|
| `method` | `str` | Имя метода JSON-RPC, к которому применяется конструктор. |
| `ctor` | `Callable[..., JsonRpcResponse]` | Вызываемый объект, создающий `JsonRpcResponse`. |
| `*states` | `JsonRpcResponseCtorWrapper.State` | Необязательные члены State, ограничивающие применение *ctor*. |

#### `add_custom_response_ctor(ctor: JsonRpcResponseCtorWrapper)`

Регистрирует готовый пользовательский конструктор ответа. Заменяет любой ранее зарегистрированный конструктор для того же метода.

| Параметр | Тип | Описание |
|---|---|---|
| `ctor` | `JsonRpcResponseCtorWrapper` | Обёртка, привязывающая конструктор к имени метода. |

#### `__call__(data: str | JsonRpcRequest | JsonRpcNotification | JsonRpcResponse | Result[...]) -> Option[Result[JsonRpcResponse, JsonRpcError]]`

Диспетчеризирует сообщение JSON-RPC.

| Параметр | Тип | Описание |
|---|---|---|
| `data` | `str \| JsonRpcRequest \| JsonRpcNotification \| JsonRpcResponse \| Result[...]` | JSON-строка, `JsonRpcRequest`, `JsonRpcNotification`, `JsonRpcResponse` или `Result`. |

**Возвращает:**

| Входные данные | Обработчик найден | Обработчик не найден |
|---|---|---|
| `str` (парсинг успешен) | Делегирует обработку запросу/уведомлению | — |
| `str` (парсинг не удался) | `Some(Err(ParseError))` | — |
| `JsonRpcRequest` | `Some(Ok(response))` | `Some(Err(MethodNotFound))` через ответ |
| `JsonRpcNotification` | `Nothing` (успех) | `Some(Err(MethodNotFound))` |
| Неизвестный тип | `Some(Err(InternalError))` | — |

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

Пытается распарсить JSON-строку как ответ, запрос или уведомление. Сначала пробует `JsonRpcResponse`; при неудаче переходит к `JsonRpcNotification`; при неудаче переходит к `JsonRpcRequest`.

| Параметр | Тип | Описание |
|---|---|---|
| `data` | `str` | JSON-строка. |

**Возвращает:** `Ok(response | notification | request)` при успехе или `Err(JsonRpcError)` при ошибке парсинга.

---

## `JsonRpcResponseCtorWrapper`

```python
class JsonRpcResponseCtorWrapper
```

Привязывает пользовательский конструктор `JsonRpcResponse` к имени метода. Обёртка записывает, *когда* применяется конструктор — успешные результаты, ошибки или оба варианта — чтобы диспетчер мог выбрать правильный тип ответа для каждого исхода.

### Конструктор

```python
JsonRpcResponseCtorWrapper(
    method: str,
    ctor: Callable[..., JsonRpcResponse],
    *states: JsonRpcResponseCtorWrapper.State,
)
```

| Параметр | Тип | По умолчанию | Описание |
|---|---|---|---|
| `method` | `str` | *(обязательный)* | Имя метода JSON-RPC, к которому применяется этот конструктор. |
| `ctor` | `Callable[..., JsonRpcResponse]` | *(обязательный)* | Вызываемый объект, принимающий ключевые аргументы (`id`, `result` или `error`, и `jsonrpc`) и возвращающий `JsonRpcResponse`. |
| `*states` | `State` | Оба исхода | Необязательные члены `State`, ограничивающие применение *ctor*. |

### Внутренний класс: `State`

```python
class State(Enum)
```

Селектор результата, определяющий, когда применяется конструктор.

| Член | Значение | Описание |
|---|---|---|
| `Result` | `1` | Конструктор обрабатывает успешные результаты. |
| `Error` | `2` | Конструктор обрабатывает ответы с ошибками. |

### Атрибуты

| Атрибут | Тип | Описание |
|---|---|---|
| `method` | `str` | Имя метода JSON-RPC, к которому привязан этот конструктор. |
| `when` | `_When` | Селектор результата для этого конструктора. |
