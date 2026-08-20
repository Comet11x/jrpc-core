# API Dispatcher

La couche dispatcher se trouve dans le module `jrpc_core.dispatcher`.

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

Encapsule un appelable en tant que méthode JSON-RPC avec des validateurs de paramètres optionnels.

### Constructeur

```python
JsonRpcMethodWrapper(
    *,
    name: str,
    method: Callable[..., Any],
    validators: list[Callable[..., Option[JsonRpcError]]] | None = None,
)
```

| Paramètre | Type | Par défaut | Description |
|---|---|---|---|
| `name` | `str` | *(requis)* | Le nom de la méthode JSON-RPC. |
| `method` | `Callable[..., Any]` | *(requis)* | L'appelable à invoquer lorsque cette méthode est dispatchée. |
| `validators` | `list[Callable[..., Option[JsonRpcError]]] \| None` | `None` | Une liste optionnelle d'appelables qui reçoivent les `params` parsés et renvoient un signal de rejet. |

### Protocole de Validateur

Chaque validateur reçoit les `params` parsés et peut renvoyer :

| Valeur de retour | Comportement |
|---|---|
| `Some(JsonRpcError)` ou `Some(Exception)` | Rejette avec cette erreur enveloppée dans `InvalidParams` |
| `False` | Rejette avec une erreur générique `InvalidParams` |
| `Exception` ou `JsonRpcError` | Rejette directement avec cette erreur |
| `True`, `None`, ou toute autre valeur truthy | Accepte — passe au validateur suivant ou à l'invocation de la méthode |

### Attributs

| Attribut | Type | Description |
|---|---|---|
| `name` | `str` | Le nom de la méthode JSON-RPC sous lequel cet encapsuleur est enregistré. |

### Méthodes

#### `__hash__() -> int`

Renvoie un hash basé sur le nom de la méthode. Deux encapsuleurs avec le même nom ont le même hash.

#### `__eq__(other) -> bool`

Compare deux encapsuleurs par nom de méthode.

#### `__call__(args: Option[Any]) -> Result[Any, JsonRpcError]`

Exécute la méthode encapsulée avec des paramètres optionnels. Les validateurs sont exécutés avant la méthode. Si un validateur rejette les paramètres, l'appel est interrompu avec un `Err`.

| Paramètre | Type | Description |
|---|---|---|
| `args` | `Option[Any]` | Un `Option` contenant les paramètres de la méthode. `Some` signifie que des paramètres ont été fournis ; `None` signifie aucun. |

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
JsonRpcDispatcher()
```

Initialise le dispatcher avec des registres de handlers vides.

### Attributs

| Attribut | Type | Description |
|---|---|---|
| `request_handler_registry` | `JsonRpcHandlerCollection` | Registre des handlers de requêtes. |
| `notification_handler_registry` | `JsonRpcHandlerCollection` | Registre des handlers de notifications. |

### Méthodes

#### `__call__(data: str | JsonRpcRequest | JsonRpcNotification) -> Option[Result[JsonRpcResponse, JsonRpcError]]`

Dispatche un message JSON-RPC.

| Paramètre | Type | Description |
|---|---|---|
| `data` | `str \| JsonRpcRequest \| JsonRpcNotification` | Une chaîne JSON, un `JsonRpcRequest`, ou un `JsonRpcNotification`. |

**Renvoie :**

| Entrée | Handler trouvé | Handler non trouvé |
|---|---|---|
| `str` (parsing ok) Délègue au traitement requête/notification | — |
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

#### `try_parse(data: str) -> Result[JsonRpcRequest | JsonRpcNotification, JsonRpcError]` *(classmethod)*

Tente d'analyser une chaîne JSON en requête ou notification. Essaie d'abord `JsonRpcRequest` ; en cas d'échec se replie sur `JsonRpcNotification`.

| Paramètre | Type | Description |
|---|---|---|
| `data` | `str` | Une chaîne encodée en JSON. |

**Renvoie :** `Ok(request | notification)` en cas de succès, ou `Err(JsonRpcError)` en cas d'échec de parsing.
