# API Dispatcher

La couche dispatcher se trouve dans le module `jrpc_core.dispatcher`.

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

Encapsule un appelable en tant que méthode JSON-RPC avec des validateurs de paramètres optionnels.

### Constructeur

```python
JsonRpcMethodWrapper(
    *,
    name: str,
    method: Callable[..., Any],
    validator: Callable[..., Option[JsonRpcError] | bool] | None = None,
    converter: Callable[..., Option[Any] | Result[Any, Exception | JsonRpcError] | Any] | None = None,
)
```

| Paramètre | Type | Par défaut | Description |
|---|---|---|---|
| `name` | `str` | *(requis)* | Le nom de la méthode JSON-RPC. |
| `method` | `Callable[..., Any]` | *(requis)* | L'appelable à invoquer lorsque cette méthode est dispatchée. |
| `validator` | `Callable[..., Option[JsonRpcError] \| bool] \| None` | `None` | Un appelable optionnel qui reçoit les `params` parsés et renvoie un signal de rejet. |
| `converter` | `Callable[..., Option[Any] \| Result[Any, Exception \| JsonRpcError] \| Any] \| None` | `None` | Un appelable optionnel qui transforme les `params` parsés avant l'invocation de la méthode. |

### Protocole de Validateur

Le validateur reçoit les `params` parsés et peut renvoyer :

| Valeur de retour | Comportement |
|---|---|
| `Some(JsonRpcError)` | Rejette avec cette erreur |
| `Some(Exception)` | Rejette avec cette erreur enveloppée dans `InvalidParams` |
| `False` | Rejette avec une erreur générique `InvalidParams` |
| `Exception` ou `JsonRpcError` | Rejette directement avec cette erreur |
| `True`, `None`, ou toute autre valeur truthy | Accepte — passe à la conversion ou à l'invocation de la méthode |

### Protocole de Convertisseur

Le convertisseur reçoit le payload `params` brut et peut renvoyer :

| Valeur de retour | Comportement |
|---|---|
| `Some(value)` | Utilise `value` comme argument de la méthode |
| `Nothing()` | Rejette avec `ConversionError` |
| `Ok(value)` | Utilise `value` comme argument de la méthode |
| `Err(reason)` | Rejette avec `ConversionError`, en attachant `reason` à `data` |
| Toute autre valeur | Utilise la valeur directement comme argument de la méthode |
| Lève une `Exception` | Rejette avec `ConversionError`, en attachant l'exception à `data` |

### Attributs

| Attribut | Type | Description |
|---|---|---|
| `name` | `str` | Le nom de la méthode JSON-RPC sous lequel cet encapsuleur est enregistré. |

### Méthodes

#### `__hash__() -> int`

Renvoie un hash basé sur le nom de la méthode. Deux encapsuleurs avec le même nom ont le même hash.

#### `__eq__(other) -> bool`

Compare deux encapsuleurs par nom de méthode.

#### `__call__(params: Option[Any]) -> Result[Any, JsonRpcError]`

Exécute la méthode encapsulée avec des paramètres optionnels. La validation est exécutée en premier, puis la conversion ; si l'une des étapes rejette les paramètres, l'appel est interrompu avec un `Err`.

| Paramètre | Type | Description |
|---|---|---|
| `params` | `Option[Any]` | Un `Option` contenant les paramètres de la méthode. `Some` signifie que des paramètres ont été fournis ; `Nothing` signifie aucun. |

**Renvoie :** `Ok(result)` en cas de succès, ou `Err(JsonRpcError)` en cas d'échec.

```python
>>> from pyfplib import Some, Nothing, Result
>>> wrapper = JsonRpcMethodWrapper(name="add", method=lambda a: a[0] + a[1])
>>> wrapper(Some([1, 2]))
Result.ok(3)
>>> wrapper(Nothing())
Result.ok(...)  # appelle la méthode sans arguments
```

---

## `JsonRpcHandlerCollection`

```python
class JsonRpcHandlerCollection
```

Un registre d'instances `JsonRpcMethodWrapper` indexées par nom de méthode.

### Constructeur

```python
JsonRpcHandlerCollection()
```

Initialise une collection de handlers vide.

### Méthodes

#### `add(method: JsonRpcMethodWrapper) -> bool`

Enregistre un encapsuleur de méthode. Si une méthode du même nom existe déjà, l'appel n'a aucun effet.

| Paramètre | Type | Description |
|---|---|---|
| `method` | `JsonRpcMethodWrapper` | L'encapsuleur à enregistrer. |

**Renvoie :** `True` si la méthode a été nouvellement enregistrée, `False` si elle existait déjà.

```python
>>> collection = JsonRpcHandlerCollection()
>>> wrapper = JsonRpcMethodWrapper(name="add", method=lambda a: a)
>>> collection.add(wrapper)
True
>>> collection.add(wrapper)  # doublon
False
```

#### `try_get(name: str) -> Option[JsonRpcMethodWrapper]`

Recherche une méthode par nom.

| Paramètre | Type | Description |
|---|---|---|
| `name` | `str` | Le nom de la méthode JSON-RPC. |

**Renvoie :** `Some(wrapper)` si trouvée, sinon `Nothing`.

#### `exists(name: str) -> bool`

Vérifie si une méthode est enregistrée.

| Paramètre | Type | Description |
|---|---|---|
| `name` | `str` | Le nom de la méthode JSON-RPC. |

**Renvoie :** `True` si un encapsuleur avec ce nom existe.

#### `remove_by_name(name: str) -> bool`

Supprime une méthode par nom.

| Paramètre | Type | Description |
|---|---|---|
| `name` | `str` | Le nom de la méthode JSON-RPC à supprimer. |

**Renvoie :** `True` si la méthode existait et a été supprimée, `False` sinon.

#### `remove(method: str | JsonRpcMethodWrapper) -> bool`

Supprime une méthode par nom ou par instance d'encapsuleur.

| Paramètre | Type | Description |
|---|---|---|
| `method` | `str \| JsonRpcMethodWrapper` | Soit une chaîne de nom de méthode, soit un `JsonRpcMethodWrapper`. |

**Renvoie :** `True` si la méthode existait et a été supprimée, `False` sinon.

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

Routage les messages JSON-RPC entrants vers les handlers enregistrés. Maintient des registres séparés pour les requêtes (qui attendent une réponse) et les notifications (fire-and-forget).

### Constructeur

```python
JsonRpcDispatcher(
    response_handler: Callable[[JsonRpcResponse], None] | None = None,
)
```

| Paramètre | Type | Par défaut | Description |
|---|---|---|---|
| `response_handler` | `Callable[[JsonRpcResponse], None] \| None` | `None` | Callback optionnel invoqué lorsqu'un `JsonRpcResponse` est dispatché directement. |

### Attributs de Classe

| Attribut | Type | Description |
|---|---|---|
| `ERROR_CASE` | `JsonRpcResponseCtorWrapper.State` | Sélecteur de résultat pour les réponses d'erreur. |
| `RESULT_CASE` | `JsonRpcResponseCtorWrapper.State` | Sélecteur de résultat pour les résultats réussis. |
| `BOTH_CASES` | `JsonRpcResponseCtorWrapper._When` | Sélecteur de résultat correspondant aux deux types de résultats. |

### Attributs

| Attribut | Type | Description |
|---|---|---|
| `request_handler_registry` | `JsonRpcHandlerCollection` | Registre des handlers de requêtes. |
| `notification_handler_registry` | `JsonRpcHandlerCollection` | Registre des handlers de notifications. |

### Méthodes

#### `emplace_request_handler(*, name, method, validator=None, converter=None) -> bool`

Enregistre un handler de requête en une seule ligne. Raccourci pour `request_handler_registry.add(JsonRpcMethodWrapper(...))`.

| Paramètre | Type | Par défaut | Description |
|---|---|---|---|
| `name` | `str` | *(requis)* | Le nom de la méthode JSON-RPC. |
| `method` | `Callable[..., Any]` | *(requis)* | L'appelable à invoquer lors du dispatch. |
| `validator` | `Callable[..., Option[JsonRpcError] \| bool] \| None` | `None` | Validateur de paramètres optionnel. |
| `converter` | `Callable[..., Option[Any] \| Result[Any, Exception \| JsonRpcError] \| Any] \| None` | `None` | Convertisseur de paramètres optionnel. |

**Renvoie :** `True` si nouvellement enregistré, `False` si le nom existe déjà.

#### `emplace_notification_handler(*, name, method, validator=None, converter=None) -> bool`

Enregistre un handler de notification en une seule ligne. Raccourci pour `notification_handler_registry.add(JsonRpcMethodWrapper(...))`.

| Paramètre | Type | Par défaut | Description |
|---|---|---|---|
| `name` | `str` | *(requis)* | Le nom de la méthode JSON-RPC. |
| `method` | `Callable[..., Any]` | *(requis)* | L'appelable à invoquer lors du dispatch. |
| `validator` | `Callable[..., Option[JsonRpcError] \| bool] \| None` | `None` | Validateur de paramètres optionnel. |
| `converter` | `Callable[..., Option[Any] \| Result[Any, Exception \| JsonRpcError] \| Any] \| None` | `None` | Convertisseur de paramètres optionnel. |

**Renvoie :** `True` si nouvellement enregistré, `False` si le nom existe déjà.

#### `emplace_custom_response_ctor(method, ctor, *states)`

Enregistre un constructeur de réponse personnalisé pour la *method*.

| Paramètre | Type | Description |
|---|---|---|
| `method` | `str` | Le nom de la méthode JSON-RPC à laquelle le constructeur s'applique. |
| `ctor` | `Callable[..., JsonRpcResponse]` | Appelable construisant un `JsonRpcResponse`. |
| `*states` | `JsonRpcResponseCtorWrapper.State` | Membres d'état optionnels restreignant l'utilisation du constructeur. |

#### `add_custom_response_ctor(ctor: JsonRpcResponseCtorWrapper)`

Enregistre un constructeur de réponse personnalisé pré-construit. Remplace tout constructeur précédemment enregistré pour la même méthode.

| Paramètre | Type | Description |
|---|---|---|
| `ctor` | `JsonRpcResponseCtorWrapper` | L'encapsuleur liant un constructeur à un nom de méthode. |

#### `__call__(data) -> Option[Result[JsonRpcResponse, JsonRpcError]]`

Dispatche un message JSON-RPC.

| Paramètre | Type | Description |
|---|---|---|
| `data` | `str \| JsonRpcRequest \| JsonRpcNotification \| JsonRpcResponse \| Result[...]` | Une chaîne JSON, un `JsonRpcRequest`, un `JsonRpcNotification`, un `JsonRpcResponse`, ou un `Result`. |

**Renvoie :**

| Entrée | Handler trouvé | Handler non trouvé |
|---|---|---|
| `str` (parsing ok) | Délègue au traitement requête/notification | — |
| `str` (échec de parsing) | `Some(Err(ParseError))` | — |
| `JsonRpcRequest` | `Some(Ok(response))` | `Some(Err(MethodNotFound))` via réponse |
| `JsonRpcNotification` | `Nothing` (succès) | `Some(Err(MethodNotFound))` |
| Type inconnu | `Some(Err(InternalError))` | — |

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

Tente d'analyser une chaîne JSON en réponse, requête ou notification. Essaie d'abord `JsonRpcResponse` ; en cas d'échec se replie sur `JsonRpcNotification` ; en cas d'échec se replie sur `JsonRpcRequest`.

| Paramètre | Type | Description |
|---|---|---|
| `data` | `str` | Une chaîne encodée en JSON. |

**Renvoie :** `Ok(response | notification | request)` en cas de succès, ou `Err(JsonRpcError)` en cas d'échec de parsing.

---

## `JsonRpcResponseCtorWrapper`

```python
class JsonRpcResponseCtorWrapper
```

Lie un constructeur de `JsonRpcResponse` personnalisé à un nom de méthode. L'encapsuleur enregistre *quand* le constructeur s'applique — résultats réussis, erreurs, ou les deux — afin que le dispatcher puisse choisir le bon type de réponse selon le résultat.

### Constructeur

```python
JsonRpcResponseCtorWrapper(
    method: str,
    ctor: Callable[..., JsonRpcResponse],
    *states: JsonRpcResponseCtorWrapper.State,
)
```

| Paramètre | Type | Par défaut | Description |
|---|---|---|---|
| `method` | `str` | *(requis)* | Le nom de la méthode JSON-RPC à laquelle ce constructeur s'applique. |
| `ctor` | `Callable[..., JsonRpcResponse]` | *(requis)* | Appelable recevant des arguments par mot-clé (`id`, `result` ou `error`, et `jsonrpc`) et renvoyant un `JsonRpcResponse`. |
| `*states` | `State` | Les deux résultats | Membres `State` optionnels limitant l'utilisation du constructeur. |

### Classe Interne : `State`

```python
class State(Enum)
```

Sélecteur de résultat contrôlant quand un constructeur est appliqué.

| Membre | Valeur | Description |
|---|---|---|
| `Result` | `1` | Le constructeur gère les résultats réussis. |
| `Error` | `2` | Le constructeur gère les réponses d'erreur. |

### Attributs

| Attribut | Type | Description |
|---|---|---|
| `method` | `str` | Le nom de la méthode JSON-RPC auquel ce constructeur est lié. |
| `when` | `_When` | Le sélecteur de résultat pour ce constructeur. |
