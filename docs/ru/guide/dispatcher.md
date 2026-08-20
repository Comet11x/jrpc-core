# API диспетчера

Слой диспетчера находится в модуле `jrpc_core.dispatcher`.

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

Оборачивает вызываемый объект как метод JSON-RPC с необязательными валидаторами параметров.

### Конструктор

```python
JsonRpcMethodWrapper(
    *,
    name: str,
    method: Callable[..., Any],
    validators: list[Callable[..., Option[JsonRpcError]]] | None = None,
)
```

| Параметр | Тип | По умолчанию | Описание |
|---|---|---|---|
| `name` | `str` | *(обязательный)* | Имя метода JSON-RPC. |
| `method` | `Callable[..., Any]` | *(обязательный)* | Вызываемый объект, который выполняется при диспетчеризации этого метода. |
| `validators` | `list[Callable[..., Option[JsonRpcError]]] \| None` | `None` | Необязательный список вызываемых объектов, которые получают распарсенные `params` и возвращают сигнал отклонения. |

### Протокол валидатора

Каждый валидатор получает распарсенные `params` и может вернуть:

| Возвращаемое значение | Поведение |
|---|---|
| `Some(JsonRpcError)` или `Some(Exception)` | Отклоняет с ошибкой, обёрнутой в `InvalidParams` |
| `False` | Отклоняет с общей ошибкой `InvalidParams` |
| `Exception` или `JsonRpcError` | Отклоняет с этой ошибкой напрямую |
| `True`, `None` или любое другое истинное значение | Принимает — переходит к следующему валидатору или вызову метода |

### Атрибуты

| Атрибут | Тип | Описание |
|---|---|---|
| `name` | `str` | Имя метода JSON-RPC, под которым зарегистрирована эта обёртка. |

### Методы

#### `__hash__() -> int`

Возвращает хеш, основанный на имени метода. Две обёртки с одинаковым именем имеют одинаковый хеш.

#### `__eq__(other) -> bool`

Сравнивает две обёртки по имени метода.

#### `__call__(args: Option[Any]) -> Result[Any, JsonRpcError]`

Выполняет оборачиваемый метод с необязательными параметрами. Валидаторы запускаются перед методом. Если любой валидатор отклоняет параметры, вызов прерывается с `Err`.

| Параметр | Тип | Описание |
|---|---|---|
| `args` | `Option[Any]` | `Option`, содержащий параметры метода. `Some` означает, что параметры были предоставлены; `None` означает их отсутствие. |

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
JsonRpcDispatcher()
```

Инициализирует диспетчер с пустыми реестрами обработчиков.

### Атрибуты

| Атрибут | Тип | Описание |
|---|---|---|
| `request_handler_registry` | `JsonRpcHandlerCollection` | Реестр обработчиков запросов. |
| `notification_handler_registry` | `JsonRpcHandlerCollection` | Реестр обработчиков уведомлений. |

### Методы

#### `__call__(data: str | JsonRpcRequest | JsonRpcNotification) -> Option[Result[JsonRpcResponse, JsonRpcError]]`

Диспетчеризирует сообщение JSON-RPC.

| Параметр | Тип | Описание |
|---|---|---|
| `data` | `str \| JsonRpcRequest \| JsonRpcNotification` | JSON-строка, `JsonRpcRequest` или `JsonRpcNotification`. |

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

#### `try_parse(data: str) -> Result[JsonRpcRequest | JsonRpcNotification, JsonRpcError]` *(classmethod)*

Пытается распарсить JSON-строку как запрос или уведомление. Сначала пробует `JsonRpcRequest`; при неудаче переходит к `JsonRpcNotification`.

| Параметр | Тип | Описание |
|---|---|---|
| `data` | `str` | JSON-строка. |

**Возвращает:** `Ok(request | notification)` при успехе или `Err(JsonRpcError)` при ошибке парсинга.
