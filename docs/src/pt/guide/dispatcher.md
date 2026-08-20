# API de Dispatcher

A camada de dispatcher está no módulo `jrpc_core.dispatcher`.

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

Envolve uma chamável como um método JSON-RPC com validadores de parâmetros opcionais.

### Construtor

```python
JsonRpcMethodWrapper(
    *,
    name: str,
    method: Callable[..., Any],
    validators: list[Callable[..., Option[JsonRpcError]]] | None = None,
)
```

| Parâmetro | Tipo | Padrão | Descrição |
|---|---|---|---|
| `name` | `str` | *(obrigatório)* | O nome do método JSON-RPC. |
| `method` | `Callable[..., Any]` | *(obrigatório)* | A chamável a ser invocada quando este método é despachado. |
| `validators` | `list[Callable[..., Option[JsonRpcError]]] \| None` | `None` | Uma lista opcional de chamáveis que recebem os `params` analisados e retornam um sinal de rejeição. |

### Protocolo de Validador

Cada validador recebe os `params` analisados e pode retornar:

| Valor de retorno | Comportamento |
|---|---|
| `Some(JsonRpcError)` ou `Some(Exception)` | Rejeita com aquele erro envolvido em `InvalidParams` |
| `False` | Rejeita com um erro genérico `InvalidParams` |
| `Exception` ou `JsonRpcError` | Rejeita com aquele erro diretamente |
| `True`, `None`, ou qualquer outro valor truthy | Aceita — continua para o próximo validador ou invocação do método |

### Atributos

| Atributo | Tipo | Descrição |
|---|---|---|
| `name` | `str` | O nome do método JSON-RPC sob o qual este wrapper está registrado. |

### Métodos

#### `__hash__() -> int`

Retorna um hash baseado no nome do método. Dois wrappers com o mesmo nome têm o mesmo hash.

#### `__eq__(other) -> bool`

Compara dois wrappers pelo nome do método.

#### `__call__(args: Option[Any]) -> Result[Any, JsonRpcError]`

Executa o método envolvido com parâmetros opcionais. Os validadores são executados antes do método. Se algum validador rejeitar os parâmetros, a chamada é interrompida com um `Err`.

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `args` | `Option[Any]` | Um `Option` contendo os parâmetros do método. `Some` significa que parâmetros foram fornecidos; `None` significa que nenhum foi. |

**Retorna:** `Ok(result)` em caso de sucesso, ou `Err(JsonRpcError)` em caso de falha.

```python
>>> from pyfplib import Some, Nothing, Result
>>> wrapper = JsonRpcMethodWrapper(name="add", method=lambda a: a[0] + a[1])
>>> wrapper(Some([1, 2]))
Result.ok(3)
>>> wrapper(Nothing())
Result.ok(...)  # calls method with no args
```

---

## `JsonRpcHandlerCollection`

```python
class JsonRpcHandlerCollection
```

Um registro de instâncias `JsonRpcMethodWrapper` indexado pelo nome do método.

### Construtor

```python
JsonRpcHandlerCollection()
```

Inicializa uma coleção de handlers vazia.

### Métodos

#### `add(method: JsonRpcMethodWrapper) -> bool`

Registra um wrapper de método. Se um método com o mesmo nome já existir, a chamada não faz nada.

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `method` | `JsonRpcMethodWrapper` | O wrapper a ser registrado. |

**Retorna:** `True` se o método foi recém-registrado, `False` se já existia.

```python
>>> collection = JsonRpcHandlerCollection()
>>> wrapper = JsonRpcMethodWrapper(name="add", method=lambda a: a)
>>> collection.add(wrapper)
True
>>> collection.add(wrapper)  # duplicate
False
```

#### `try_get(name: str) -> Option[JsonRpcMethodWrapper]`

Busca um método pelo nome.

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `name` | `str` | O nome do método JSON-RPC. |

**Retorna:** `Some(wrapper)` se encontrado, caso contrário `Nothing`.

#### `exists(name: str) -> bool`

Verifica se um método está registrado.

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `name` | `str` | O nome do método JSON-RPC. |

**Retorna:** `True` se um wrapper com aquele nome existe.

#### `remove_by_name(name: str) -> bool`

Remove um método pelo nome.

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `name` | `str` | O nome do método JSON-RPC a ser removido. |

**Retorna:** `True` se o método existia e foi removido, `False` caso contrário.

#### `remove(method: str | JsonRpcMethodWrapper) -> bool`

Remove um método pelo nome ou instância do wrapper.

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `method` | `str \| JsonRpcMethodWrapper` | Uma string de nome de método ou um `JsonRpcMethodWrapper`. |

**Retorna:** `True` se o método existia e foi removido, `False` caso contrário.

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

Roteia mensagens JSON-RPC recebidas para handlers registrados. Mantém registros separados para requisições (que esperam uma resposta) e notificações (fire-and-forget).

### Construtor

```python
JsonRpcDispatcher()
```

Inicializa o dispatcher com registros de handlers vazios.

### Atributos

| Atributo | Tipo | Descrição |
|---|---|---|
| `request_handler_registry` | `JsonRpcHandlerCollection` | Registro para handlers de requisição. |
| `notification_handler_registry` | `JsonRpcHandlerCollection` | Registro para handlers de notificação. |

### Métodos

#### `__call__(data: str | JsonRpcRequest | JsonRpcNotification) -> Option[Result[JsonRpcResponse, JsonRpcError]]`

Despacha uma mensagem JSON-RPC.

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `data` | `str \| JsonRpcRequest \| JsonRpcNotification` | Uma string JSON, `JsonRpcRequest` ou `JsonRpcNotification`. |

**Retorna:**

| Entrada | Handler encontrado | Handler não encontrado |
|---|---|---|
| `str` (parsing ok) | Delega para tratamento de requisição/notificação | — |
| `str` (parsing falhou) | `Some(Err(ParseError))` | — |
| `JsonRpcRequest` | `Some(Ok(response))` | `Some(Err(MethodNotFound))` via resposta |
| `JsonRpcNotification` | `Nothing` (sucesso) | `Some(Err(MethodNotFound))` |
| Tipo desconhecido | `Some(Err(InternalError))` | — |

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

Tenta analisar uma string JSON em uma requisição ou notificação. Primeiro tenta `JsonRpcRequest`; em caso de falha, recorre a `JsonRpcNotification`.

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `data` | `str` | Uma string codificada em JSON. |

**Retorna:** `Ok(request | notification)` em caso de sucesso, ou `Err(JsonRpcError)` em caso de falha de parsing.
