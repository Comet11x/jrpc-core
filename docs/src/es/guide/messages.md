# API de Mensajes

Todos los primitivos de mensaje viven en el módulo `jrpc_core.messages`.

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

## Alias de Tipo

### `JsonRpcId`

```python
JsonRpcId = str | int | float | None
```

Alias de tipo para un identificador de mensaje JSON-RPC. Un identificador válido es un `str`, `int`, `float` o `None`. La variante `None` solo está permitida en notificaciones.

### `JsonRpcParams`

```python
JsonRpcParams = dict[str, Any] | list[Any] | None
```

Alias de tipo para valores de `params` de JSON-RPC. Los parámetros pueden ser un mapeo con nombre (`dict`), una lista posicional (`list`), o `None` cuando se omiten.

---

## `JsonRpcErrorCode`

```python
class JsonRpcErrorCode(Enum)
```

Enumeración de códigos de error estándar de JSON-RPC 2.0. Cada miembro corresponde al código entero definido por la especificación o extensiones comunes (`-32xxx` reservado, `-320xx` definido por el servidor).

### Miembros

| Miembro | Valor | Descripción |
|---|---|---|
| `ParseError` | `-32700` | El servidor recibió JSON inválido. |
| `InternalError` | `-32603` | Ocurrió un error interno de JSON-RPC. |
| `InvalidParams` | `-32602` | Los parámetros enviados con el método son inválidos. |
| `MethodNotFound` | `-32601` | El método no existe o no está disponible. |
| `InvalidRequest` | `-32600` | El JSON enviado no es un objeto de solicitud válido. |
| `ExecutionError` | `-32000` | Ocurrió un error de ejecución definido por el servidor. |
| `ConversionError` | `-32001` | Ocurrió un error de conversión definido por el servidor. |

### Métodos

#### `__int__() -> int`

Retorna el valor entero de este código de error.

```python
>>> int(JsonRpcErrorCode.ParseError)
-32700
```

#### `description() -> str`

Retorna una descripción legible para humanos de este código de error.

```python
>>> JsonRpcErrorCode.ParseError.description()
'Parse error'
```

#### `default() -> JsonRpcErrorCode` *(estático)*

Retorna el código de error predeterminado cuando ningún otro código es apropiado. Retorna `InternalError`.

```python
>>> JsonRpcErrorCode.default()
<JsonRpcErrorCode.InternalError: -32603>
```

#### `into(data: Any = None) -> JsonRpcError`

Crea un `JsonRpcError` a partir de este código.

| Parámetro | Tipo | Predeterminado | Descripción |
|---|---|---|---|
| `data` | `Any` | `None` | Carga adicional opcional adjunta al error. |

**Retorna:** Un nuevo `JsonRpcError` con este código y su descripción.

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

Versiones del protocolo JSON-RPC soportadas.

| Miembro | Valor |
|---|---|
| `Version1` | `"1.0"` |
| `Version2` | `"2.0"` |

---

## `JsonRpcError`

```python
class JsonRpcError(BaseModel)
```

Un objeto de error de JSON-RPC 2.0.

### Atributos

| Atributo | Tipo | Predeterminado | Descripción |
|---|---|---|---|
| `code` | `JsonRpcErrorCode \| int` | `JsonRpcErrorCode.InternalError` | Un código de error entero. |
| `message` | `str` | `"Something went wrong"` | Una descripción corta legible para humanos. |
| `data` | `Any \| None` | `None` | Información adicional opcional sobre el error. |

### Métodos

#### `default() -> JsonRpcError` *(estático)*

Retorna un error predeterminado con `JsonRpcErrorCode.InternalError`.

```python
>>> JsonRpcError.default()
JsonRpcError(code=<JsonRpcErrorCode.InternalError: -32603>, message='Something went wrong', data=None)
```

#### `from_data(*, data: Any, code: JsonRpcErrorCode = InternalError, message: str = ...) -> JsonRpcError` *(estático)*

Crea un `JsonRpcError` a partir de datos arbitrarios con código y mensaje explícitos.

| Parámetro | Tipo | Predeterminado | Descripción |
|---|---|---|---|
| `data` | `Any` | *(requerido)* | Carga adicional adjunta al error. |
| `code` | `JsonRpcErrorCode` | `InternalError` | El código de error. |
| `message` | `str` | `InternalError.description()` | Una descripción corta legible para humanos. |

**Retorna:** Una nueva instancia de `JsonRpcError`.

```python
>>> JsonRpcError.from_data(data={"detail": "oops"})
JsonRpcError(code=<JsonRpcErrorCode.InternalError: -32603>, message='Internal error', data={'detail': 'oops'})
>>> JsonRpcError.from_data(data="bad", code=JsonRpcErrorCode.InvalidParams, message="invalid")
JsonRpcError(code=<JsonRpcErrorCode.InvalidParams: -32602>, message='invalid', data='bad')
```

#### `from_error(error: JsonRpcError | Any) -> JsonRpcError` *(estático)*

Convierte un valor arbitrario en un `JsonRpcError`. Si *error* ya es un `JsonRpcError` se retorna tal cual. De lo contrario, la función intenta extraer un atributo `code` y construye un error alrededor de él, usando `JsonRpcErrorCode.InternalError` como respaldo.

| Parámetro | Tipo | Descripción |
|---|---|---|
| `error` | `JsonRpcError \| Any` | El valor a convertir. |

**Retorna:** Una instancia de `JsonRpcError`.

```python
>>> JsonRpcError.from_error(RuntimeError("oops"))
JsonRpcError(code=<JsonRpcErrorCode.InternalError: -32603>, message='Internal error', data=RuntimeError('oops'))
```

#### `try_from(value: Option[JsonRpcError | Any]) -> Option[JsonRpcError]` *(estático)*

Intenta convertir un `Option` en un error.

| Parámetro | Tipo | Descripción |
|---|---|---|
| `value` | `Option[JsonRpcError \| Any]` | Un `Option` que puede contener un valor a convertir. |

**Retorna:** `Some(JsonRpcError)` si *value* era `Some`, de lo contrario `Nothing`.

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

Un objeto de solicitud de JSON-RPC 2.0. Contiene un nombre de `method`, una carga `params` opcional, y un `id` que el cliente usa para correlacionar la respuesta.

### Atributos

| Atributo | Tipo | Predeterminado | Descripción |
|---|---|---|---|
| `method` | `str` | *(requerido)* | El nombre del procedimiento remoto a invocar. Debe ser una cadena no vacía. |
| `id` | `JsonRpcId` | `str(uuid4())` | Un identificador único para esta solicitud (UUID auto-generado por defecto). |
| `params` | `JsonRpcParams` | `None` | Argumentos posicionales o con nombre opcionales para el método. |
| `jsonrpc` | `JsonRpcVersion` | `Version2` | La versión del protocolo. |

### Métodos

#### `try_from_dict(data: dict) -> Result[JsonRpcRequest, Exception]` *(classmethod)*

Intenta construir una solicitud a partir de un diccionario plano.

| Parámetro | Tipo | Descripción |
|---|---|---|
| `data` | `dict[str, Any]` | Un diccionario con campos de solicitud JSON-RPC. |

**Retorna:** `Ok(solicitud)` en éxito, o `Err(excepción)` en fallo de validación.

```python
>>> JsonRpcRequest.try_from_dict({"method": "add", "id": 1}).is_ok()
True
```

#### `try_from_json(data: str) -> Result[JsonRpcRequest, Exception]` *(classmethod)*

Intenta construir una solicitud a partir de una cadena JSON.

| Parámetro | Tipo | Descripción |
|---|---|---|
| `data` | `str` | Una cadena codificada en JSON que representa una solicitud. |

**Retorna:** `Ok(solicitud)` en éxito, o `Err(excepción)` en fallo de parseo/validación.

```python
>>> JsonRpcRequest.try_from_json('{"method":"add","id":1}').is_ok()
True
```

#### `to_dict() -> dict[str, Any]`

Serializa la solicitud a un diccionario plano. La clave `params` se omite cuando es `None`.

**Retorna:** Un diccionario adecuado para serialización JSON.

```python
>>> JsonRpcRequest(method="add", params=[1, 2]).to_dict()
{'method': 'add', 'id': '<uuid>', 'params': [1, 2], 'jsonrpc': '2.0'}
```

#### `to_json() -> str`

Serializa la solicitud a una cadena JSON.

**Retorna:** Una representación JSON compacta de esta solicitud.

#### `serialize() -> str`

Serializa la solicitud a una cadena JSON. Alias de `to_json()`.

**Retorna:** Una representación JSON compacta de esta solicitud.

#### `into(result: Result[Any, JsonRpcError]) -> JsonRpcResponse`

Crea un `JsonRpcResponse` a partir del resultado de un handler. Acepta un `Result`, un `JsonRpcError`, o un valor crudo.

| Parámetro | Tipo | Descripción |
|---|---|---|
| `result` | `Result[Any, JsonRpcError]` | El resultado del procesamiento de esta solicitud. |

**Retorna:** Una respuesta con el resultado desempaquetado o el error.

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

Un objeto de notificación de JSON-RPC 2.0. Idéntico a una solicitud pero omite el campo `id`, indicando que no se espera respuesta del servidor.

### Atributos

| Atributo | Tipo | Predeterminado | Descripción |
|---|---|---|---|
| `method` | `str` | *(requerido)* | El nombre del evento o procedimiento que se anuncia. Debe ser una cadena no vacía. |
| `params` | `JsonRpcParams` | `None` | Argumentos posicionales o con nombre opcionales. |
| `jsonrpc` | `JsonRpcVersion` | `Version2` | La versión del protocolo. |

::: warning
Una notificación **no** debe contener un campo `id`. Intentar construir una con un `id` lanza un error de validación.
:::

### Métodos

#### `try_from_dict(data: dict) -> Result[JsonRpcNotification, Exception]` *(classmethod)*

Intenta construir una notificación a partir de un diccionario plano.

| Parámetro | Tipo | Descripción |
|---|---|---|
| `data` | `dict[str, Any]` | Un diccionario con campos de notificación JSON-RPC. |

**Retorna:** `Ok(notificación)` en éxito, o `Err(excepción)` en fallo de validación.

#### `try_from_json(data: str) -> Result[JsonRpcNotification, Exception]` *(classmethod)*

Intenta construir una notificación a partir de una cadena JSON.

| Parámetro | Tipo | Descripción |
|---|---|---|
| `data` | `str` | Una cadena codificada en JSON que representa una notificación. |

**Retorna:** `Ok(notificación)` en éxito, o `Err(excepción)` en fallo de parseo/validación.

#### `to_dict() -> dict[str, Any]`

Serializa la notificación a un diccionario plano. La clave `params` se omite cuando es `None`.

**Retorna:** Un diccionario adecuado para serialización JSON.

#### `to_json() -> str`

Serializa la notificación a una cadena JSON.

**Retorna:** Una representación JSON compacta de esta notificación.

#### `serialize() -> str`

Serializa la notificación a una cadena JSON. Alias de `to_json()`.

**Retorna:** Una representación JSON compacta de esta notificación.

---

## `JsonRpcResponse`

```python
class JsonRpcResponse(BaseModel)
```

Un objeto de respuesta de JSON-RPC 2.0. Exactamente uno de `result` o `error` debe estar establecido. El `id` coincide con el `id` de la solicitud originaria.

### Atributos

| Atributo | Tipo | Predeterminado | Descripción |
|---|---|---|---|
| `id` | `JsonRpcId` | *(requerido)* | El identificador de la solicitud a la que corresponde esta respuesta. |
| `result` | `Any` | `None` | El valor de retorno cuando el método se ejecutó exitosamente. |
| `error` | `JsonRpcError \| None` | `None` | Un `JsonRpcError` cuando el método falló. |
| `jsonrpc` | `JsonRpcVersion` | `Version2` | La versión del protocolo. |

::: warning
Una respuesta debe tener **ya sea** un `result` **o** un `error`, no ambos. Intentar establecer ambos lanza un error de validación.
:::

### Métodos

#### `from_result(id, result) -> JsonRpcResponse` *(estático)*

Construye una respuesta a partir de un `Result`.

| Parámetro | Tipo | Descripción |
|---|---|---|
| `id` | `JsonRpcId` | El identificador de la solicitud a resonar. |
| `result` | `Result[Any, JsonRpcError]` | El resultado del handler. |

**Retorna:** Un `JsonRpcResponse` completamente construido.

```python
>>> from pyfplib import Result
>>> JsonRpcResponse.from_result(1, Result.ok("data"))
JsonRpcResponse(id=1, result='data', error=None, ...)
>>> JsonRpcResponse.from_result(2, Result.err(JsonRpcError(code=JsonRpcErrorCode.InternalError)))
JsonRpcResponse(id=2, result=None, error=JsonRpcError(...), ...)
```

#### `from_jrpc_error(id, error) -> JsonRpcResponse` *(estático)*

Construye una respuesta de error.

| Parámetro | Tipo | Descripción |
|---|---|---|
| `id` | `JsonRpcId` | El identificador de la solicitud a resonar. |
| `error` | `JsonRpcError \| Exception` | El error a incluir. |

**Retorna:** Un `JsonRpcResponse` con solo `error` establecido.

#### `from_jrpc_result(id, result) -> JsonRpcResponse` *(estático)*

Construye una respuesta exitosa.

| Parámetro | Tipo | Descripción |
|---|---|---|
| `id` | `JsonRpcId` | El identificador de la solicitud a resonar. |
| `result` | `Any` | El valor de retorno del método. |

**Retorna:** Un `JsonRpcResponse` con solo `result` establecido.

#### `try_from_dict(data: dict) -> Result[JsonRpcResponse, Exception]` *(estático)*

Intenta construir una respuesta a partir de un diccionario plano.

| Parámetro | Tipo | Descripción |
|---|---|---|
| `data` | `dict[str, Any]` | Un diccionario con campos de respuesta JSON-RPC. |

**Retorna:** `Ok(respuesta)` en éxito, o `Err(excepción)` en fallo de validación.

#### `try_from_json(data: str) -> Result[JsonRpcResponse, Exception]` *(estático)*

Intenta construir una respuesta a partir de una cadena JSON.

| Parámetro | Tipo | Descripción |
|---|---|---|
| `data` | `str` | Una cadena codificada en JSON que representa una respuesta. |

**Retorna:** `Ok(respuesta)` en éxito, o `Err(excepción)` en fallo de parseo/validación.

#### `to_dict() -> dict[str, Any]`

Serializa la respuesta a un diccionario plano. Cuando hay un `error` presente, la clave `result` se elimina y el código de error se convierte a `int`. Cuando `result` está presente, la clave `error` se elimina.

**Retorna:** Un diccionario adecuado para serialización JSON.

#### `to_json() -> str`

Serializa la respuesta a una cadena JSON.

**Retorna:** Una representación JSON compacta de esta respuesta.

#### `serialize() -> str`

Serializa la respuesta a una cadena JSON. Alias de `to_json()`.

**Retorna:** Una representación JSON compacta de esta respuesta.

---

## `try_parse()`

```python
def try_parse(data: str) -> Result[JsonRpcResponse | JsonRpcNotification | JsonRpcRequest, JsonRpcError]
```

Intenta parsear una cadena JSON como un mensaje JSON-RPC. La función primero intenta parsear como `JsonRpcResponse`; si falla, recurre a `JsonRpcNotification`; si falla, recurre a `JsonRpcRequest`. Si todas fallan, se retorna el error de parseo del intento de solicitud.

| Parámetro | Tipo | Descripción |
|---|---|---|
| `data` | `str` | Una cadena codificada en JSON. |

**Retorna:** `Ok(respuesta | notificación | solicitud)` en éxito, o `Err(JsonRpcError)` con el fallo de parseo.

```python
>>> try_parse('{"jsonrpc":"2.0","method":"add","id":1}')
Result.ok(JsonRpcRequest(method='add', id=1, ...))
```
