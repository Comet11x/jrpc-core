# API de Dispatcher

La capa de dispatcher vive en el módulo `jrpc_core.dispatcher`.

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

Envuelve un callable como un método JSON-RPC con validación y conversión opcionales.

### Constructor

```python
JsonRpcMethodWrapper(
    *,
    name: str,
    method: Callable[..., Any],
    validator: Callable[..., Option[JsonRpcError] | bool] | None = None,
    converter: Callable[..., Option[Any] | Result[Any, Exception | JsonRpcError] | Any] | None = None,
)
```

| Parámetro | Tipo | Predeterminado | Descripción |
|---|---|---|---|
| `name` | `str` | *(requerido)* | El nombre del método JSON-RPC. |
| `method` | `Callable[..., Any]` | *(requerido)* | El callable a invocar cuando se despacha este método. |
| `validator` | `Callable[..., Option[JsonRpcError] \| bool] \| None` | `None` | Un callable opcional que recibe los `params` parseados y retorna una señal de rechazo. |
| `converter` | `Callable[..., Option[Any] \| Result[Any, Exception \| JsonRpcError] \| Any] \| None` | `None` | Un callable opcional que transforma los `params` parseados antes de invocar el método. |

### Protocolo de Validador

Cada validador recibe los `params` parseados y puede retornar:

| Valor de retorno | Comportamiento |
|---|---|
| `Some(JsonRpcError)` | Rechaza con ese error |
| `Some(Exception)` | Rechaza con ese error envuelto en `InvalidParams` |
| `False` | Rechaza con un error genérico de `InvalidParams` |
| `Exception` o `JsonRpcError` | Rechaza con ese error directamente |
| `True`, `None`, o cualquier otro valor truthy | Acepta — continúa al siguiente validador o invocación del método |

### Protocolo de Convertidor

El convertidor recibe la carga `params` sin procesar y puede retornar:

| Valor de retorno | Comportamiento |
|---|---|
| `Some(valor)` | Usa `valor` como argumento del método |
| `Nothing()` | Rechaza con `ConversionError` |
| `Ok(valor)` | Usa `valor` como argumento del método |
| `Err(motivo)` | Rechaza con `ConversionError`, adjuntando `motivo` a `data` |
| Cualquier otro valor | Usa el valor directamente como argumento del método |
| Lanza `Exception` | Rechaza con `ConversionError`, adjuntando la excepción a `data` |

### Atributos

| Atributo | Tipo | Descripción |
|---|---|---|
| `name` | `str` | El nombre del método JSON-RPC bajo el cual está registrado este wrapper. |

### Métodos

#### `__hash__() -> int`

Retorna un hash basado en el nombre del método. Dos wrappers con el mismo nombre tienen el mismo hash.

#### `__eq__(other) -> bool`

Compara dos wrappers por nombre de método.

#### `__call__(params: Option[Any]) -> Result[Any, JsonRpcError]`

Ejecuta el método envuelto con parámetros opcionales. La validación se ejecuta primero, luego la conversión; si alguno de estos pasos rechaza los parámetros, la llamada se cortocircuita con un `Err`.

| Parámetro | Tipo | Descripción |
|---|---|---|
| `params` | `Option[Any]` | Un `Option` que contiene los parámetros del método. `Some` significa que se proporcionaron parámetros; `Nothing` significa ninguno. |

**Retorna:** `Ok(resultado)` en éxito, o `Err(JsonRpcError)` en fallo.

```python
>>> from pyfplib import Some, Nothing, Result
>>> wrapper = JsonRpcMethodWrapper(name="add", method=lambda a: a[0] + a[1])
>>> wrapper(Some([1, 2]))
Result.ok(3)
>>> wrapper(Nothing())
Result.ok(...)  # llama al método sin argumentos
```

---

## `JsonRpcHandlerCollection`

```python
class JsonRpcHandlerCollection
```

Un registro de instancias de `JsonRpcMethodWrapper` indexado por nombre de método.

### Constructor

```python
JsonRpcHandlerCollection()
```

Inicializa una colección de handlers vacía.

### Métodos

#### `add(method: JsonRpcMethodWrapper) -> bool`

Registra un wrapper de método. Si ya existe un método con el mismo nombre, la llamada es un no-op.

| Parámetro | Tipo | Descripción |
|---|---|---|
| `method` | `JsonRpcMethodWrapper` | El wrapper a registrar. |

**Retorna:** `True` si el método fue registrado recientemente, `False` si ya existía.

```python
>>> collection = JsonRpcHandlerCollection()
>>> wrapper = JsonRpcMethodWrapper(name="add", method=lambda a: a)
>>> collection.add(wrapper)
True
>>> collection.add(wrapper)  # duplicado
False
```

#### `try_get(name: str) -> Option[JsonRpcMethodWrapper]`

Busca un método por nombre.

| Parámetro | Tipo | Descripción |
|---|---|---|
| `name` | `str` | El nombre del método JSON-RPC. |

**Retorna:** `Some(wrapper)` si se encuentra, de lo contrario `Nothing`.

#### `exists(name: str) -> bool`

Verifica si un método está registrado.

| Parámetro | Tipo | Descripción |
|---|---|---|
| `name` | `str` | El nombre del método JSON-RPC. |

**Retorna:** `True` si existe un wrapper con ese nombre.

#### `remove_by_name(name: str) -> bool`

Elimina un método por nombre.

| Parámetro | Tipo | Descripción |
|---|---|---|
| `name` | `str` | El nombre del método JSON-RPC a eliminar. |

**Retorna:** `True` si el método existía y fue eliminado, `False` de lo contrario.

#### `remove(method: str | JsonRpcMethodWrapper) -> bool`

Elimina un método por nombre o instancia de wrapper.

| Parámetro | Tipo | Descripción |
|---|---|---|
| `method` | `str \| JsonRpcMethodWrapper` | Una cadena con el nombre del método o un `JsonRpcMethodWrapper`. |

**Retorna:** `True` si el método existía y fue eliminado, `False` de lo contrario.

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

Enruta mensajes JSON-RPC entrantes a handlers registrados. Mantiene registros separados para solicitudes (que esperan una respuesta) y notificaciones (fire-and-forget).

### Constructor

```python
JsonRpcDispatcher(
    response_handler: Callable[[JsonRpcResponse], None] | None = None,
)
```

| Parámetro | Tipo | Predeterminado | Descripción |
|---|---|---|---|
| `response_handler` | `Callable[[JsonRpcResponse], None] \| None` | `None` | Callback opcional invocado cuando se despacha un `JsonRpcResponse` directamente. |

### Atributos de Clase

| Atributo | Tipo | Descripción |
|---|---|---|
| `ERROR_CASE` | `JsonRpcResponseCtorWrapper.State` | Selector de resultado para respuestas de error. |
| `RESULT_CASE` | `JsonRpcResponseCtorWrapper.State` | Selector de resultado para resultados exitosos. |
| `BOTH_CASES` | `JsonRpcResponseCtorWrapper._When` | Selector de resultado que coincide con ambos resultados. |

### Atributos

| Atributo | Tipo | Descripción |
|---|---|---|
| `request_handler_registry` | `JsonRpcHandlerCollection` | Registro de handlers de solicitudes. |
| `notification_handler_registry` | `JsonRpcHandlerCollection` | Registro de handlers de notificaciones. |

### Métodos

#### `emplace_request_handler(*, name, method, validator=None, converter=None) -> bool`

Registra un handler de solicitud en una sola llamada. Conveniencia de `request_handler_registry.add(JsonRpcMethodWrapper(...))`.

| Parámetro | Tipo | Predeterminado | Descripción |
|---|---|---|---|
| `name` | `str` | *(requerido)* | El nombre del método JSON-RPC. |
| `method` | `Callable[..., Any]` | *(requerido)* | El callable a invocar cuando se despacha. |
| `validator` | `Callable[..., Option[JsonRpcError] \| bool] \| None` | `None` | Validador de parámetros opcional. |
| `converter` | `Callable[..., Option[Any] \| Result[Any, Exception \| JsonRpcError] \| Any] \| None` | `None` | Convertidor de parámetros opcional. |

**Retorna:** `True` si fue registrado recientemente, `False` si el nombre ya existía.

#### `emplace_notification_handler(*, name, method, validator=None, converter=None) -> bool`

Registra un handler de notificación en una sola llamada. Conveniencia de `notification_handler_registry.add(JsonRpcMethodWrapper(...))`.

| Parámetro | Tipo | Predeterminado | Descripción |
|---|---|---|---|
| `name` | `str` | *(requerido)* | El nombre del método JSON-RPC. |
| `method` | `Callable[..., Any]` | *(requerido)* | El callable a invocar cuando se despacha. |
| `validator` | `Callable[..., Option[JsonRpcError] \| bool] \| None` | `None` | Validador de parámetros opcional. |
| `converter` | `Callable[..., Option[Any] \| Result[Any, Exception \| JsonRpcError] \| Any] \| None` | `None` | Convertidor de parámetros opcional. |

**Retorna:** `True` si fue registrado recientemente, `False` si el nombre ya existía.

#### `emplace_custom_response_ctor(method, ctor, *states)`

Registra un constructor de respuesta personalizado para *method*.

| Parámetro | Tipo | Descripción |
|---|---|---|
| `method` | `str` | El nombre del método JSON-RPC al que aplica el constructor. |
| `ctor` | `Callable[..., JsonRpcResponse]` | Callable que construye un `JsonRpcResponse`. |
| `*states` | `JsonRpcResponseCtorWrapper.State` | Miembros de estado opcionales que restringen cuándo se usa *ctor*. |

#### `add_custom_response_ctor(ctor: JsonRpcResponseCtorWrapper)`

Registra un constructor de respuesta personalizado pre-construido. Reemplaza cualquier constructor previamente registrado para el mismo método.

| Parámetro | Tipo | Descripción |
|---|---|---|
| `ctor` | `JsonRpcResponseCtorWrapper` | El wrapper que vincula un constructor a un nombre de método. |

#### `__call__(data) -> Option[Result[JsonRpcResponse, JsonRpcError]]`

Despacha un mensaje JSON-RPC.

| Parámetro | Tipo | Descripción |
|---|---|---|
| `data` | `str \| JsonRpcRequest \| JsonRpcNotification \| JsonRpcResponse \| Result[...]` | Una cadena JSON, `JsonRpcRequest`, `JsonRpcNotification`, `JsonRpcResponse`, o `Result`. |

**Retorna:**

| Entrada | Handler encontrado | Handler no encontrado |
|---|---|---|
| `str` (parseo ok) | Delega al manejo de solicitud/notificación | — |
| `str` (parseo falla) | `Some(Err(ParseError))` | — |
| `JsonRpcRequest` | `Some(Ok(respuesta))` | `Some(Err(MethodNotFound))` vía respuesta |
| `JsonRpcNotification` | `Nothing` (éxito) | `Some(Err(MethodNotFound))` |
| Tipo desconocido | `Some(Err(InternalError))` | — |

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

Intenta parsear una cadena JSON en una respuesta, solicitud o notificación. Primero intenta `JsonRpcResponse`; en caso de fallo recurre a `JsonRpcNotification`; en caso de fallo recurre a `JsonRpcRequest`.

| Parámetro | Tipo | Descripción |
|---|---|---|
| `data` | `str` | Una cadena codificada en JSON. |

**Retorna:** `Ok(respuesta | notificación | solicitud)` en éxito, o `Err(JsonRpcError)` en fallo de parseo.

---

## `JsonRpcResponseCtorWrapper`

```python
class JsonRpcResponseCtorWrapper
```

Vincula un constructor personalizado de `JsonRpcResponse` a un nombre de método. El wrapper registra *cuándo* aplica el constructor — resultados exitosos, errores, o ambos — para que el dispatcher pueda elegir el tipo de respuesta correcto por resultado.

### Constructor

```python
JsonRpcResponseCtorWrapper(
    method: str,
    ctor: Callable[..., JsonRpcResponse],
    *states: JsonRpcResponseCtorWrapper.State,
)
```

| Parámetro | Tipo | Predeterminado | Descripción |
|---|---|---|---|
| `method` | `str` | *(requerido)* | El nombre del método JSON-RPC al que aplica este constructor. |
| `ctor` | `Callable[..., JsonRpcResponse]` | *(requerido)* | Callable que recibe argumentos de palabra clave (`id`, `result` o `error`, y `jsonrpc`) y retorna un `JsonRpcResponse`. |
| `*states` | `State` | Ambos resultados | Miembros de `State` opcionales que limitan cuándo se usa *ctor*. |

### Clase Interna: `State`

```python
class State(Enum)
```

Selector de resultado que controla cuándo se aplica un constructor.

| Miembro | Valor | Descripción |
|---|---|---|
| `Result` | `1` | El constructor maneja resultados exitosos. |
| `Error` | `2` | El constructor maneja respuestas de error. |

### Atributos

| Atributo | Tipo | Descripción |
|---|---|---|
| `method` | `str` | El nombre del método JSON-RPC al que está vinculado este constructor. |
| `when` | `_When` | El selector de resultado para este constructor. |
