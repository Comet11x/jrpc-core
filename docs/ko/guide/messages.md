# 메시지 API

모든 메시지 프리미티브는 `jrpc_core.messages` 모듈에 있습니다.

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

## 타입 별칭

### `JsonRpcId`

```python
JsonRpcId = str | int | float | None
```

JSON-RPC 메시지 식별자의 타입 별칭입니다. 유효한 식별자는 `str`, `int`, `float`, 또는 `None`입니다. `None` 변형은 알림에서만 허용됩니다.

### `JsonRpcParams`

```python
JsonRpcParams = dict[str, Any] | list[Any] | None
```

JSON-RPC `params` 값의 타입 별칭입니다. 매개변수는 이름이 지정된 매핑(`dict`), 위치 목록(`list`), 또는 생략된 경우 `None`일 수 있습니다.

---

## `JsonRpcErrorCode`

```python
class JsonRpcErrorCode(Enum)
```

표준 JSON-RPC 2.0 오류 코드의 열거형입니다. 각 멤버는 사양이나 일반 확장에서 정의된 정수 코드에 매핑됩니다(`-32xxx` 예약, `-320xx` 서버 정의).

### 멤버

| 멤버 | 값 | 설명 |
|---|---|---|
| `ParseError` | `-32700` | 서버가 잘못된 JSON을 수신했습니다. |
| `InternalError` | `-32603` | 내부 JSON-RPC 오류가 발생했습니다. |
| `InvalidParams` | `-32602` | 메서드와 함께 전송된 매개변수가 잘못되었습니다. |
| `MethodNotFound` | `-32601` | 메서드가 존재하지 않거나 사용할 수 없습니다. |
| `InvalidRequest` | `-32600` | 전송된 JSON이 유효한 요청 객체가 아닙니다. |
| `ExecutionError` | `-32000` | 서버 정의 실행 오류가 발생했습니다. |

### 메서드

#### `__int__() -> int`

이 오류 코드의 정수 값을 반환합니다.

```python
>>> int(JsonRpcErrorCode.ParseError)
-32700
```

#### `description() -> str`

이 오류 코드의 사람이 읽을 수 있는 설명을 반환합니다.

```python
>>> JsonRpcErrorCode.ParseError.description()
'Parse error'
```

#### `default() -> JsonRpcErrorCode` *(정적)*

다른 코드가 적합하지 않을 때 사용되는 기본 오류 코드를 반환합니다. `InternalError`를 반환합니다.

```python
>>> JsonRpcErrorCode.default()
<JsonRpcErrorCode.InternalError: -32603>
```

#### `into(data: Any = None) -> JsonRpcError`

이 코드에서 `JsonRpcError`를 생성합니다.

| 매개변수 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `data` | `Any` | `None` | 오류에 첨부되는 선택적 추가 페이로드. |

**반환값:** 이 코드와 설명이 포함된 새로운 `JsonRpcError`.

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

지원되는 JSON-RPC 프로토콜 버전입니다.

| 멤버 | 값 |
|---|---|
| `Version1` | `"1.0"` |
| `Version2` | `"2.0"` |

---

## `JsonRpcError`

```python
class JsonRpcError(BaseModel)
```

JSON-RPC 2.0 오류 객체입니다.

### 속성

| 속성 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `code` | `JsonRpcErrorCode \| int` | `JsonRpcErrorCode.InternalError` | 정수 오류 코드. |
| `message` | `str` | `"Something went wrong"` | 짧은 사람이 읽을 수 있는 설명. |
| `data` | `Any \| None` | `None` | 오류에 대한 선택적 추가 정보. |

### 메서드

#### `default() -> JsonRpcError` *(정적)*

`JsonRpcErrorCode.InternalError`를 가진 기본 오류를 반환합니다.

```python
>>> JsonRpcError.default()
JsonRpcError(code=<JsonRpcErrorCode.InternalError: -32603>, message='Something went wrong', data=None)
```

#### `from_error(error: JsonRpcError | Any) -> JsonRpcError` *(정적)*

임의의 값을 `JsonRpcError`로 변환합니다. *error*가 이미 `JsonRpcError`인 경우 그대로 반환됩니다. 그렇지 않으면 함수는 `code` 속성을 추출하려고 시도하고 그 주변에 오류를 구성하며, `JsonRpcErrorCode.InternalError`로 대체합니다.

| 매개변수 | 타입 | 설명 |
|---|---|---|
| `error` | `JsonRpcError \| Any` | 변환할 값. |

**반환값:** `JsonRpcError` 인스턴스.

```python
>>> JsonRpcError.from_error(RuntimeError("oops"))
JsonRpcError(code=<JsonRpcErrorCode.InternalError: -32603>, message='Internal error', data=RuntimeError('oops'))
```

#### `try_from(value: Option[JsonRpcError | Any]) -> Option[JsonRpcError]` *(정적)*

`Option`을 오류로 변환하려고 시도합니다.

| 매개변수 | 타입 | 설명 |
|---|---|---|
| `value` | `Option[JsonRpcError \| Any]` | 변환할 값을 포함할 수 있는 `Option`. |

**반환값:** *value*가 `Some`이면 `Some(JsonRpcError)`, 그렇지 않으면 `Nothing`.

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

JSON-RPC 2.0 요청 객체입니다. `method` 이름, 선택적 `params` 페이로드, 그리고 클라이언트가 응답을 연결하는 데 사용하는 `id`를 포함합니다.

### 속성

| 속성 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `method` | `str` | *(필수)* | 호출할 원격 절차의 이름. 비어 있지 않은 문자열이어야 합니다. |
| `id` | `JsonRpcId` | `str(uuid4())` | 이 요청의 고유 식별자 (기본적으로 자동 생성 UUID). |
| `params` | `JsonRpcParams` | `None` | 메서드에 대한 선택적 위치 또는 이름이 지정된 인수. |
| `jsonrpc` | `JsonRpcVersion` | `Version2` | 프로토콜 버전. |

### 메서드

#### `try_from_dict(data: dict) -> Result[JsonRpcRequest, Exception]` *(클래스 메서드)*

일반 딕셔너리에서 요청을 생성하려고 시도합니다.

| 매개변수 | 타입 | 설명 |
|---|---|---|
| `data` | `dict[str, Any]` | JSON-RPC 요청 필드를 포함하는 딕셔너리. |

**반환값:** 성공 시 `Ok(request)`, 검증 실패 시 `Err(exception)`.

```python
>>> JsonRpcRequest.try_from_dict({"method": "add", "id": 1}).is_ok()
True
```

#### `try_from_json(data: str) -> Result[JsonRpcRequest, Exception]` *(클래스 메서드)*

JSON 문자열에서 요청을 생성하려고 시도합니다.

| 매개변수 | 타입 | 설명 |
|---|---|---|
| `data` | `str` | 요청을 나타내는 JSON 인코딩 문자열. |

**반환값:** 성공 시 `Ok(request)`, 파싱/검증 실패 시 `Err(exception)`.

```python
>>> JsonRpcRequest.try_from_json('{"method":"add","id":1}').is_ok()
True
```

#### `to_dict() -> dict[str, Any]`

요청을 일반 딕셔너리로 직렬화합니다. `params`가 `None`인 경우 `params` 키는 생략됩니다.

**반환값:** JSON 직렬화에 적합한 딕셔너리.

```python
>>> JsonRpcRequest(method="add", params=[1, 2]).to_dict()
{'method': 'add', 'id': '<uuid>', 'params': [1, 2], 'jsonrpc': '2.0'}
```

#### `to_json() -> str`

요청을 JSON 문자열로 직렬화합니다.

**반환값:** 이 요청의 축약된 JSON 표현.

#### `into(result: Result[Any, JsonRpcError]) -> JsonRpcResponse`

핸들러 결과에서 `JsonRpcResponse`를 생성합니다. `Result`, `JsonRpcError`, 또는 원시 값을 허용합니다.

| 매개변수 | 타입 | 설명 |
|---|---|---|
| `result` | `Result[Any, JsonRpcError]` | 이 요청 처리의 결과. |

**반환값:** 언래핑된 결과 또는 오류를 포함하는 응답.

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

JSON-RPC 2.0 알림 객체입니다. 요청과 동일하지만 `id` 필드를 생략하여 서버로부터 응답이 예상되지 않음을 나타냅니다.

### 속성

| 속성 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `method` | `str` | *(필수)* | 발표 중인 이벤트 또는 절차의 이름. 비어 있지 않은 문자열이어야 합니다. |
| `params` | `JsonRpcParams` | `None` | 선택적 위치 또는 이름이 지정된 인수. |
| `jsonrpc` | `JsonRpcVersion` | `Version2` | 프로토콜 버전. |

::: warning
알림에는 `id` 필드가 **포함되어서는 안 됩니다**. `id`와 함께 생성하려고 시도하면 검증 오류가 발생합니다.
:::

### 메서드

#### `try_from_dict(data: dict) -> Result[JsonRpcNotification, Exception]` *(클래스 메서드)*

일반 딕셔너리에서 알림을 생성하려고 시도합니다.

| 매개변수 | 타입 | 설명 |
|---|---|---|
| `data` | `dict[str, Any]` | JSON-RPC 알림 필드를 포함하는 딕셔너리. |

**반환값:** 성공 시 `Ok(notification)`, 검증 실패 시 `Err(exception)`.

#### `try_from_json(data: str) -> Result[JsonRpcNotification, Exception]` *(클래스 메서드)*

JSON 문자열에서 알림을 생성하려고 시도합니다.

| 매개변수 | 타입 | 설명 |
|---|---|---|
| `data` | `str` | 알림을 나타내는 JSON 인코딩 문자열. |

**반환값:** 성공 시 `Ok(notification)`, 파싱/검증 실패 시 `Err(exception)`.

#### `to_dict() -> dict[str, Any]`

알림을 일반 딕셔너리로 직렬화합니다. `params`가 `None`인 경우 `params` 키는 생략됩니다.

**반환값:** JSON 직렬화에 적합한 딕셔너리.

#### `to_json() -> str`

알림을 JSON 문자열로 직렬화합니다.

**반환값:** 이 알림의 축약된 JSON 표현.

---

## `JsonRpcResponse`

```python
class JsonRpcResponse(BaseModel)
```

JSON-RPC 2.0 응답 객체입니다. `result` 또는 `error` 중 정확히 하나만 설정되어야 합니다. `id`는 기존 요청의 `id`와 일치합니다.

### 속성

| 속성 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `id` | `JsonRpcId` | *(필수)* | 이 응답이 대응하는 요청의 식별자. |
| `result` | `Any` | `None` | 메서드가 성공적으로 실행되었을 때의 반환 값. |
| `error` | `JsonRpcError \| None` | `None` | 메서드가 실패했을 때의 `JsonRpcError`. |
| `jsonrpc` | `JsonRpcVersion` | `Version2` | 프로토콜 버전. |

::: warning
응답에는 `result` **또는** `error`가 있어야 하며, 둘 다 있어서는 안 됩니다. 둘 다 설정하려고 시도하면 검증 오류가 발생합니다.
:::

### 메서드

#### `from_result(id, result) -> JsonRpcResponse` *(정적)*

`Result`에서 응답을 생성합니다.

| 매개변수 | 타입 | 설명 |
|---|---|---|
| `id` | `JsonRpcId` | 에코할 요청 식별자. |
| `result` | `Result[Any, JsonRpcError]` | 핸들러의 결과. |

**반환값:** 완전히 구성된 `JsonRpcResponse`.

```python
>>> from pyfplib import Result
>>> JsonRpcResponse.from_result(1, Result.ok("data"))
JsonRpcResponse(id=1, result='data', error=None, ...)
>>> JsonRpcResponse.from_result(2, Result.err(JsonRpcError(code=JsonRpcErrorCode.InternalError)))
JsonRpcResponse(id=2, result=None, error=JsonRpcError(...), ...)
```

#### `from_jrpc_error(id, error) -> JsonRpcResponse` *(정적)*

오류 응답을 생성합니다.

| 매개변수 | 타입 | 설명 |
|---|---|---|
| `id` | `JsonRpcId` | 에코할 요청 식별자. |
| `error` | `JsonRpcError` | 포함할 오류. |

**반환값:** `error`만 설정된 `JsonRpcResponse`.

#### `from_jrpc_result(id, result) -> JsonRpcResponse` *(정적)*

성공적인 응답을 생성합니다.

| 매개변수 | 타입 | 설명 |
|---|---|---|
| `id` | `JsonRpcId` | 에코할 요청 식별자. |
| `result` | `Any` | 메서드의 반환 값. |

**반환값:** `result`만 설정된 `JsonRpcResponse`.

#### `try_from_dict(data: dict) -> Result[JsonRpcResponse, Exception]` *(정적)*

일반 딕셔너리에서 응답을 생성하려고 시도합니다.

| 매개변수 | 타입 | 설명 |
|---|---|---|
| `data` | `dict[str, Any]` | JSON-RPC 응답 필드를 포함하는 딕셔너리. |

**반환값:** 성공 시 `Ok(response)`, 검증 실패 시 `Err(exception)`.

#### `try_from_json(data: str) -> Result[JsonRpcResponse, Exception]` *(정적)*

JSON 문자열에서 응답을 생성하려고 시도합니다.

| 매개변수 | 타입 | 설명 |
|---|---|---|
| `data` | `str` | 응답을 나타내는 JSON 인코딩 문자열. |

**반환값:** 성공 시 `Ok(response)`, 파싱/검증 실패 시 `Err(exception)`.

#### `to_dict() -> dict[str, Any]`

응답을 일반 딕셔너리로 직렬화합니다. `error`가 있으면 `result` 키가 제거되고 오류 코드는 `int`로 강제 변환됩니다. `result`가 있으면 `error` 키가 제거됩니다.

**반환값:** JSON 직렬화에 적합한 딕셔너리.

#### `to_json() -> str`

응답을 JSON 문자열로 직렬화합니다.

**반환값:** 이 응답의 축약된 JSON 표현.

---

## `try_parse()`

```python
def try_parse(data: str) -> Result[JsonRpcRequest | JsonRpcNotification, JsonRpcError]
```

JSON 문자열을 JSON-RPC 메시지로 파싱하려고 시도합니다. 함수는 먼저 `JsonRpcRequest`로 파싱을 시도하고, 실패하면 `JsonRpcNotification`으로 대체합니다. 둘 다 실패하면 요청 시도의 파싱 오류가 반환됩니다.

| 매개변수 | 타입 | 설명 |
|---|---|---|
| `data` | `str` | JSON 인코딩 문자열. |

**반환값:** 성공 시 `Ok(request | notification)`, 파싱 실패를 포함하는 `Err(JsonRpcError)`.

::: warning
`JsonRpcRequest`가 `uuid4()`를 통해 `id`를 기본값으로 설정하므로, 알림 페이로드 ( `id` 없음)은 요청으로 성공합니다. 알림 형식을 강제화해야 할 때는 `JsonRpcNotification.try_from_json`을 직접 사용하세요.
:::

```python
>>> try_parse('{"jsonrpc":"2.0","method":"add","id":1}')
Result.ok(JsonRpcRequest(method='add', id=1, ...))
```
