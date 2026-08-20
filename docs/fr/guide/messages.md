# API Messages

Toutes les primitives de messages se trouvent dans le module `jrpc_core.messages`.

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

## Alias de Types

### `JsonRpcId`

```python
JsonRpcId = str | int | float | None
```

Alias de type pour l'identifiant d'un message JSON-RPC. Un identifiant valide est un `str`, `int`, `float` ou `None`. La variante `None` n'est autorisée que dans les notifications.

### `JsonRpcParams`

```python
JsonRpcParams = dict[str, Any] | list[Any] | None
```

Alias de type pour les valeurs `params` de JSON-RPC. Les paramètres peuvent être un mapping nommé (`dict`), une liste positionnelle (`list`) ou `None` lorsque omis.

---

## `JsonRpcErrorCode`

```python
class JsonRpcErrorCode(Enum)
```

Énumération des codes d'erreur JSON-RPC 2.0 standard. Chaque membre correspond au code entier défini par la spécification ou les extensions courantes (`-32xxx` réservé, `-320xx` défini par le serveur).

### Membres

| Membre | Valeur | Description |
|---|---|---|
| `ParseError` | `-32700` | Le serveur a reçu un JSON invalide. |
| `InternalError` | `-32603` | Une erreur interne JSON-RPC s'est produite. |
| `InvalidParams` | `-32602` | Les paramètres envoyés avec la méthode sont invalides. |
| `MethodNotFound` | `-32601` | La méthode n'existe pas ou n'est pas disponible. |
| `InvalidRequest` | `-32600` | Le JSON envoyé n'est pas un objet requête valide. |
| `ExecutionError` | `-32000` | Une erreur d'exécution définie par le serveur s'est produite. |

### Méthodes

#### `__int__() -> int`

Renvoie la valeur entière de ce code d'erreur.

```python
>>> int(JsonRpcErrorCode.ParseError)
-32700
```

#### `description() -> str`

Renvoie une description lisible de ce code d'erreur.

```python
>>> JsonRpcErrorCode.ParseError.description()
'Parse error'
```

#### `default() -> JsonRpcErrorCode` *(statique)*

Renvoie le code d'erreur par défaut utilisé lorsqu'aucun autre code n'est approprié. Renvoie `InternalError`.

```python
>>> JsonRpcErrorCode.default()
<JsonRpcErrorCode.InternalError: -32603>
```

#### `into(data: Any = None) -> JsonRpcError`

Crée un `JsonRpcError` à partir de ce code.

| Paramètre | Type | Par défaut | Description |
|---|---|---|---|
| `data` | `Any` | `None` | Charge supplémentaire optionnelle attachée à l'erreur. |

**Renvoie :** Un nouveau `JsonRpcError` avec ce code et sa description.

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

Versions du protocole JSON-RPC prises en charge.

| Membre | Valeur |
|---|---|
| `Version1` | `"1.0"` |
| `Version2` | `"2.0"` |

---

## `JsonRpcError`

```python
class JsonRpcError(BaseModel)
```

Un objet d'erreur JSON-RPC 2.0.

### Attributs

| Attribut | Type | Par défaut | Description |
|---|---|---|---|
| `code` | `JsonRpcErrorCode \| int` | `JsonRpcErrorCode.InternalError` | Un code d'erreur entier. |
| `message` | `str` | `"Something went wrong"` | Une courte description lisible. |
| `data` | `Any \| None` | `None` | Informations supplémentaires optionnelles sur l'erreur. |

### Méthodes

#### `default() -> JsonRpcError` *(statique)*

Renvoie une erreur par défaut avec `JsonRpcErrorCode.InternalError`.

```python
>>> JsonRpcError.default()
JsonRpcError(code=<JsonRpcErrorCode.InternalError: -32603>, message='Something went wrong', data=None)
```

#### `from_error(error: JsonRpcError | Any) -> JsonRpcError` *(statique)*

Convertit une valeur arbitraire en un `JsonRpcError`. Si *error* est déjà un `JsonRpcError`, il est renvoyé tel quel. Sinon, la fonction tente d'extraire un attribut `code` et construit une erreur autour, avec un repli sur `JsonRpcErrorCode.InternalError`.

| Paramètre | Type | Description |
|---|---|---|
| `error` | `JsonRpcError \| Any` | La valeur à convertir. |

**Renvoie :** Une instance de `JsonRpcError`.

```python
>>> JsonRpcError.from_error(RuntimeError("oops"))
JsonRpcError(code=<JsonRpcErrorCode.InternalError: -32603>, message='Internal error', data=RuntimeError('oops'))
```

#### `try_from(value: Option[JsonRpcError | Any]) -> Option[JsonRpcError]` *(statique)*

Tente de convertir un `Option` en une erreur.

| Paramètre | Type | Description |
|---|---|---|
| `value` | `Option[JsonRpcError \| Any]` | Un `Option` pouvant contenir une valeur à convertir. |

**Renvoie :** `Some(JsonRpcError)` si *value* était `Some`, sinon `Nothing`.

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

Un objet requête JSON-RPC 2.0. Contient un nom de `method`, une charge `params` optionnelle, et un `id` que le client utilise pour corréler la réponse.

### Attributs

| Attribut | Type | Par défaut | Description |
|---|---|---|---|
| `method` | `str` | *(requis)* | Le nom de la procédure distante à appeler. Doit être une chaîne non vide. |
| `id` | `JsonRpcId` | `str(uuid4())` | Un identifiant unique pour cette requête (UUID généré automatiquement par défaut). |
| `params` | `JsonRpcParams` | `None` | Arguments positionnels ou nommés optionnels pour la méthode. |
| `jsonrpc` | `JsonRpcVersion` | `Version2` | La version du protocole. |

### Méthodes

#### `try_from_dict(data: dict) -> Result[JsonRpcRequest, Exception]` *(classmethod)*

Tente de construire une requête à partir d'un dictionnaire simple.

| Paramètre | Type | Description |
|---|---|---|
| `data` | `dict[str, Any]` | Un dictionnaire contenant les champs d'une requête JSON-RPC. |

**Renvoie :** `Ok(request)` en cas de succès, ou `Err(exception)` en cas d'échec de validation.

```python
>>> JsonRpcRequest.try_from_dict({"method": "add", "id": 1}).is_ok()
True
```

#### `try_from_json(data: str) -> Result[JsonRpcRequest, Exception]` *(classmethod)*

Tente de construire une requête à partir d'une chaîne JSON.

| Paramètre | Type | Description |
|---|---|---|
| `data` | `str` | Une chaîne encodée en JSON représentant une requête. |

**Renvoie :** `Ok(request)` en cas de succès, ou `Err(exception)` en cas d'échec de parsing/validation.

```python
>>> JsonRpcRequest.try_from_json('{"method":"add","id":1}').is_ok()
True
```

#### `to_dict() -> dict[str, Any]`

Sérialise la requête en un dictionnaire simple. La clé `params` est omise lorsque `None`.

**Renvoie :** Un dictionnaire adapté à la sérialisation JSON.

```python
>>> JsonRpcRequest(method="add", params=[1, 2]).to_dict()
{'method': 'add', 'id': '<uuid>', 'params': [1, 2], 'jsonrpc': '2.0'}
```

#### `to_json() -> str`

Sérialise la requête en une chaîne JSON.

**Renvoie :** Une représentation JSON compacte de cette requête.

#### `into(result: Result[Any, JsonRpcError]) -> JsonRpcResponse`

Crée un `JsonRpcResponse` à partir du résultat d'un handler. Accepte un `Result`, un `JsonRpcError`, ou une valeur brute.

| Paramètre | Type | Description |
|---|---|---|
| `result` | `Result[Any, JsonRpcError]` | Le résultat du traitement de cette requête. |

**Renvoie :** Une réponse contenant le résultat extrait ou l'erreur.

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

Un objet notification JSON-RPC 2.0. Identique à une requête mais omet le champ `id`, indiquant qu'aucune réponse n'est attendue du serveur.

### Attributs

| Attribut | Type | Par défaut | Description |
|---|---|---|---|
| `method` | `str` | *(requis)* | Le nom de l'événement ou de la procédure annoncée. Doit être une chaîne non vide. |
| `params` | `JsonRpcParams` | `None` | Arguments positionnels ou nommés optionnels. |
| `jsonrpc` | `JsonRpcVersion` | `Version2` | La version du protocole. |

::: warning
Une notification ne doit **pas** contenir un champ `id`. Tenter d'en construire une avec un `id` déclenche une erreur de validation.
:::

### Méthodes

#### `try_from_dict(data: dict) -> Result[JsonRpcNotification, Exception]` *(classmethod)*

Tente de construire une notification à partir d'un dictionnaire simple.

| Paramètre | Type | Description |
|---|---|---|
| `data` | `dict[str, Any]` | Un dictionnaire contenant les champs d'une notification JSON-RPC. |

**Renvoie :** `Ok(notification)` en cas de succès, ou `Err(exception)` en cas d'échec de validation.

#### `try_from_json(data: str) -> Result[JsonRpcNotification, Exception]` *(classmethod)*

Tente de construire une notification à partir d'une chaîne JSON.

| Paramètre | Type | Description |
|---|---|---|
| `data` | `str` | Une chaîne encodée en JSON représentant une notification. |

**Renvoie :** `Ok(notification)` en cas de succès, ou `Err(exception)` en cas d'échec de parsing/validation.

#### `to_dict() -> dict[str, Any]`

Sérialise la notification en un dictionnaire simple. La clé `params` est omise lorsque `None`.

**Renvoie :** Un dictionnaire adapté à la sérialisation JSON.

#### `to_json() -> str`

Sérialise la notification en une chaîne JSON.

**Renvoie :** Une représentation JSON compacte de cette notification.

---

## `JsonRpcResponse`

```python
class JsonRpcResponse(BaseModel)
```

Un objet réponse JSON-RPC 2.0. Exactement l'un de `result` ou `error` doit être défini. Le `id` correspond au `id` de la requête d'origine.

### Attributs

| Attribut | Type | Par défaut | Description |
|---|---|---|---|
| `id` | `JsonRpcId` | *(requis)* | L'identifiant de la requête à laquelle cette réponse correspond. |
| `result` | `Any` | `None` | La valeur de retour lorsque la méthode s'est exécutée avec succès. |
| `error` | `JsonRpcError \| None` | `None` | Un `JsonRpcError` lorsque la méthode a échoué. |
| `jsonrpc` | `JsonRpcVersion` | `Version2` | La version du protocole. |

::: warning
Une réponse doit avoir **soit** un `result` **soit** un `error`, pas les deux. Tenter de définir les deux déclenche une erreur de validation.
:::

### Méthodes

#### `from_result(id, result) -> JsonRpcResponse` *(statique)*

Construit une réponse à partir d'un `Result`.

| Paramètre | Type | Description |
|---|---|---|
| `id` | `JsonRpcId` | L'identifiant de la requête à renvoyer. |
| `result` | `Result[Any, JsonRpcError]` | Le résultat du handler. |

**Renvoie :** Un `JsonRpcResponse` entièrement construit.

```python
>>> from pyfplib import Result
>>> JsonRpcResponse.from_result(1, Result.ok("data"))
JsonRpcResponse(id=1, result='data', error=None, ...)
>>> JsonRpcResponse.from_result(2, Result.err(JsonRpcError(code=JsonRpcErrorCode.InternalError)))
JsonRpcResponse(id=2, result=None, error=JsonRpcError(...), ...)
```

#### `from_jrpc_error(id, error) -> JsonRpcResponse` *(statique)*

Construit une réponse d'erreur.

| Paramètre | Type | Description |
|---|---|---|
| `id` | `JsonRpcId` | L'identifiant de la requête à renvoyer. |
| `error` | `JsonRpcError` | L'erreur à inclure. |

**Renvoie :** Un `JsonRpcResponse` avec uniquement `error` défini.

#### `from_jrpc_result(id, result) -> JsonRpcResponse` *(statique)*

Construit une réponse réussie.

| Paramètre | Type | Description |
|---|---|---|
| `id` | `JsonRpcId` | L'identifiant de la requête à renvoyer. |
| `result` | `Any` | La valeur de retour de la méthode. |

**Renvoie :** Un `JsonRpcResponse` avec uniquement `result` défini.

#### `try_from_dict(data: dict) -> Result[JsonRpcResponse, Exception]` *(statique)*

Tente de construire une réponse à partir d'un dictionnaire simple.

| Paramètre | Type | Description |
|---|---|---|
| `data` | `dict[str, Any]` | Un dictionnaire contenant les champs d'une réponse JSON-RPC. |

**Renvoie :** `Ok(response)` en cas de succès, ou `Err(exception)` en cas d'échec de validation.

#### `try_from_json(data: str) -> Result[JsonRpcResponse, Exception]` *(statique)*

Tente de construire une réponse à partir d'une chaîne JSON.

| Paramètre | Type | Description |
|---|---|---|
| `data` | `str` | Une chaîne encodée en JSON représentant une réponse. |

**Renvoie :** `Ok(response)` en cas de succès, ou `Err(exception)` en cas d'échec de parsing/validation.

#### `to_dict() -> dict[str, Any]`

Sérialise la réponse en un dictionnaire simple. Lorsqu'un `error` est présent, la clé `result` est supprimée et le code d'erreur est converti en `int`. Lorsque `result` est présent, la clé `error` est supprimée.

**Renvoie :** Un dictionnaire adapté à la sérialisation JSON.

#### `to_json() -> str`

Sérialise la réponse en une chaîne JSON.

**Renvoie :** Une représentation JSON compacte de cette réponse.

---

## `try_parse()`

```python
def try_parse(data: str) -> Result[JsonRpcRequest | JsonRpcNotification, JsonRpcError]
```

Tente d'analyser une chaîne JSON en tant que message JSON-RPC. La fonction essaie d'abord d'analyser en tant que `JsonRpcRequest` ; si cela échoue, elle se replie sur `JsonRpcNotification`. Si les deux échouent, l'erreur de parsing de la tentative de requête est renvoyée.

| Paramètre | Type | Description |
|---|---|---|
| `data` | `str` | Une chaîne encodée en JSON. |

**Renvoie :** `Ok(request | notification)` en cas de succès, ou `Err(JsonRpcError)` contenant l'échec de parsing.

::: warning
Étant donné que `JsonRpcRequest` initialise `id` par défaut via `uuid4()`, une charge de notification (sans `id`) réussira en tant que requête. Utilisez directement `JsonRpcNotification.try_from_json` lorsque vous devez imposer la forme notification.
:::

```python
>>> try_parse('{"jsonrpc":"2.0","method":"add","id":1}')
Result.ok(JsonRpcRequest(method='add', id=1, ...))
```
