# API de Dispatcher

La capa de dispatcher vive en el módulo `jrpc_core.dispatcher`.

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

Envuelve un callable como un método JSON-RPC con validadores de parámetros opcionales.

### Constructor

```python
JsonRpcMethodWrapper(
    *,
    name: str,
    method: Callable[..., Any],
    validators: list[Callable[..., Option[JsonRpcError]]] | None = None,
)
```

| Parámetro | Tipo | Predeterminado | Descripción |
|---|---|---|---|
| `name` | `str` | *(requerido)* | El nombre del método JSON-RPC. |
| `method` | `Callable[..., Any]` | *(requerido)* | El callable a invocar cuando se despacha este método. |
| `validators` | `list[Callable[..., Option[JsonRpcError]]] \| None` | `None` | Una lista opcional de callables que reciben los `params` parseados y retornan una señal de rechazo. |

### Protocolo de Validador

Cada validador recibe los `params` parseados y puede retornar:

| Valor de retorno | Comportamiento |
|---|---|
| `Some(JsonRpcError)` o `Some(Exception)` | Rechaza con ese error envuelto en `InvalidParams` |
| `False` | Rechaza con un error genérico de `InvalidParams` |
| `Exception` o `JsonRpcError` | Rechaza con ese error directamente |
| `True`, `None`, o cualquier otro valor truthy | Acepta — continúa al siguiente validador o invocación del método |

### Atributos

| Atributo | Tipo | Descripción |
|---|---|---|
| `name` | `str` | El nombre del método JSON-RPC bajo el cual está registrado este wrapper. |

### Métodos

#### `__hash__() -> int`

Retorna un hash basado en el nombre del método. Dos wrappers con el mismo nombre tienen el mismo hash.

#### `__eq__(other) -> bool`

Compara dos wrappers por nombre de método.

#### `__call__(args: Option[Any]) -> Result[Any, JsonRpcError]`

Ejecuta el método envuelto con parámetros opcionales. Los validadores se ejecutan antes del método. Si algún validador rechaza los parámetros, la llamada se cortocircuita con un `Err`.

| Parámetro | Tipo | Descripción |
|---|---|---|
| `args` | `Option[Any]` | Un `Option` que contiene los parámetros del método. `Some` significa que se proporcionaron parámetros; `None` significa ninguno. |

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
JsonRpcDispatcher()
```

Inicializa el dispatcher con registros de handlers vacíos.

### Atributos

| Atributo | Tipo | Descripción |
|---|---|---|
| `request_handler_registry` | `JsonRpcHandlerCollection` | Registro de handlers de solicitudes. |
| `notification_handler_registry` | `JsonRpcHandlerCollection` | Registro de handlers de notificaciones. |

### Métodos

#### `__call__(data: str | JsonRpcRequest | JsonRpcNotification) -> Option[Result[JsonRpcResponse, JsonRpcError]]`

Despacha un mensaje JSON-RPC.

| Parámetro | Tipo | Descripción |
|---|---|---|
| `data` | `str \| JsonRpcRequest \| JsonRpcNotification` | Una cadena JSON, `JsonRpcRequest`, o `JsonRpcNotification`. |

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

#### `try_parse(data: str) -> Result[JsonRpcRequest | JsonRpcNotification, JsonRpcError]` *(classmethod)*

Intenta parsear una cadena JSON en una solicitud o notificación. Primero intenta `JsonRpcRequest`; en caso de fallo recurre a `JsonRpcNotification`.

| Parámetro | Tipo | Descripción |
|---|---|---|
| `data` | `str` | Una cadena codificada en JSON. |

**Retorna:** `Ok(solicitud | notificación)` en éxito, o `Err(JsonRpcError)` en fallo de parseo.
