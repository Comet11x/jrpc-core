# 디스패처 API

디스패처 레이어는 `jrpc_core.dispatcher` 모듈에 있습니다.

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

호출 가능 객체를 선택적 매개변수 검증기가 있는 JSON-RPC 메서드로 래핑합니다.

### 생성자

```python
JsonRpcMethodWrapper(
    *,
    name: str,
    method: Callable[..., Any],
    validators: list[Callable[..., Option[JsonRpcError]]] | None = None,
)
```

| 매개변수 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `name` | `str` | *(필수)* | JSON-RPC 메서드 이름. |
| `method` | `Callable[..., Any]` | *(필수)* | 이 메서드가 디스패치될 때 호출되는 호출 가능 객체. |
| `validators` | `list[Callable[..., Option[JsonRpcError]]] \| None` | `None` | 파싱된 `params`를 수신하고 거부 신호를 반환하는 선택적 호출 가능 객체 목록. |

### 검증기 프로토콜

각 검증기는 파싱된 `params`를 수신하고 다음을 반환할 수 있습니다:

| 반환 값 | 동작 |
|---|---|
| `Some(JsonRpcError)` 또는 `Some(Exception)` | 해당 오류가 `InvalidParams`로 래핑되어 거부 |
| `False` | 일반적인 `InvalidParams` 오류로 거부 |
| `Exception` 또는 `JsonRpcError` | 해당 오류로 직접 거부 |
| `True`, `None`, 또는 기타Truthy 값 | 수락 — 다음 검증기 또는 메서드 호출로 계속 |

### 속성

| 속성 | 타입 | 설명 |
|---|---|---|
| `name` | `str` | 이 래퍼가 등록된 JSON-RPC 메서드 이름. |

### 메서드

#### `__hash__() -> int`

메서드 이름을 기반으로 한 해시를 반환합니다. 같은 이름을 가진 두 래퍼는 같은 해시를 가집니다.

#### `__eq__(other) -> bool`

메서드 이름으로 두 래퍼를 비교합니다.

#### `__call__(args: Option[Any]) -> Result[Any, JsonRpcError]`

선택적 매개변수로 래핑된 메서드를 실행합니다. 검증기는 메서드 전에 실행됩니다. 검증기 중 하나가 매개변수를 거부하면 호출은 `Err`로 단축됩니다.

| 매개변수 | 타입 | 설명 |
|---|---|---|
| `args` | `Option[Any]` | 메서드 매개변수를 포함하는 `Option`. `Some`은 매개변수가 제공됨을 의미하고, `None`은 없음을 의미합니다. |

**반환값:** 성공 시 `Ok(result)`, 실패 시 `Err(JsonRpcError)`.

```python
>>> from pyfplib import Some, Nothing, Result
>>> wrapper = JsonRpcMethodWrapper(name="add", method=lambda a: a[0] + a[1])
>>> wrapper(Some([1, 2]))
Result.ok(3)
>>> wrapper(Nothing())
Result.ok(...)  # 인수 없이 메서드를 호출합니다
```

---

## `JsonRpcHandlerCollection`

```python
class JsonRpcHandlerCollection
```

메서드 이름을 키로 하는 `JsonRpcMethodWrapper` 인스턴스의 레지스트리입니다.

### 생성자

```python
JsonRpcHandlerCollection()
```

빈 핸들러 컬렉션을 초기화합니다.

### 메서드

#### `add(method: JsonRpcMethodWrapper) -> bool`

메서드 래퍼를 등록합니다. 같은 이름의 메서드가 이미 있으면 호출은 작업이 없습니다.

| 매개변수 | 타입 | 설명 |
|---|---|---|
| `method` | `JsonRpcMethodWrapper` | 등록할 래퍼. |

**반환값:** 메서드가 새로 등록된 경우 `True`, 이미 존재하는 경우 `False`.

```python
>>> collection = JsonRpcHandlerCollection()
>>> wrapper = JsonRpcMethodWrapper(name="add", method=lambda a: a)
>>> collection.add(wrapper)
True
>>> collection.add(wrapper)  # 중복
False
```

#### `try_get(name: str) -> Option[JsonRpcMethodWrapper]`

이름으로 메서드를 조회합니다.

| 매개변수 | 타입 | 설명 |
|---|---|---|
| `name` | `str` | JSON-RPC 메서드 이름. |

**반환값:** 찾은 경우 `Some(wrapper)`, 그렇지 않으면 `Nothing`.

#### `exists(name: str) -> bool`

메서드가 등록되어 있는지 확인합니다.

| 매개변수 | 타입 | 설명 |
|---|---|---|
| `name` | `str` | JSON-RPC 메서드 이름. |

**반환값:** 해당 이름의 래퍼가 존재하면 `True`.

#### `remove_by_name(name: str) -> bool`

이름으로 메서드를 제거합니다.

| 매개변수 | 타입 | 설명 |
|---|---|---|
| `name` | `str` | 제거할 JSON-RPC 메서드 이름. |

**반환값:** 메서드가 존재하고 제거된 경우 `True`, 그렇지 않으면 `False`.

#### `remove(method: str | JsonRpcMethodWrapper) -> bool`

이름 또는 래퍼 인스턴스로 메서드를 제거합니다.

| 매개변수 | 타입 | 설명 |
|---|---|---|
| `method` | `str \| JsonRpcMethodWrapper` | 메서드 이름 문자열 또는 `JsonRpcMethodWrapper`. |

**반환값:** 메서드가 존재하고 제거된 경우 `True`, 그렇지 않으면 `False`.

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

들어오는 JSON-RPC 메시지를 등록된 핸들러로 라우팅합니다. 응답을 기다리는 요청과 전송 후 잊어버리는 알림의 별도 레지스트리를 유지합니다.

### 생성자

```python
JsonRpcDispatcher()
```

빈 핸들러 레지스트리로 디스패처를 초기화합니다.

### 속성

| 속성 | 타입 | 설명 |
|---|---|---|
| `request_handler_registry` | `JsonRpcHandlerCollection` | 요청 핸들러 레지스트리. |
| `notification_handler_registry` | `JsonRpcHandlerCollection` | 알림 핸들러 레지스트리. |

### 메서드

#### `__call__(data: str | JsonRpcRequest | JsonRpcNotification) -> Option[Result[JsonRpcResponse, JsonRpcError]]`

JSON-RPC 메시지를 디스패치합니다.

| 매개변수 | 타입 | 설명 |
|---|---|---|
| `data` | `str \| JsonRpcRequest \| JsonRpcNotification` | JSON 문자열, `JsonRpcRequest`, 또는 `JsonRpcNotification`. |

**반환값:**

| 입력 | 핸들러 찾음 | 핸들러를 찾을 수 없음 |
|---|---|---|
| `str` (파싱 성공) | 요청/알림 처리에 위임 | — |
| `str` (파싱 실패) | `Some(Err(ParseError))` | — |
| `JsonRpcRequest` | `Some(Ok(response))` | 응답을 통한 `Some(Err(MethodNotFound))` |
| `JsonRpcNotification` | `Nothing` (성공) | `Some(Err(MethodNotFound))` |
| 알 수 없는 타입 | `Some(Err(InternalError))` | — |

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

#### `try_parse(data: str) -> Result[JsonRpcRequest | JsonRpcNotification, JsonRpcError]` *(클래스 메서드)*

JSON 문자열을 요청 또는 알림으로 파싱하려고 시도합니다. 먼저 `JsonRpcRequest`를 시도하고, 실패하면 `JsonRpcNotification`으로 대체합니다.

| 매개변수 | 타입 | 설명 |
|---|---|---|
| `data` | `str` | JSON 인코딩 문자열. |

**반환값:** 성공 시 `Ok(request | notification)`, 파싱 실패 시 `Err(JsonRpcError)`.
