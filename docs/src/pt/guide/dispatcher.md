# API de Dispatcher

A camada de dispatcher está no módulo `jrpc_core.dispatcher`.

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

Envolve uma chamável como um método JSON-RPC com validadores de parâmetros opcionais.

### Construtor

```python
JsonRpcMethodWrapper(
    *,
    name: str,
    method: Callable[..., Any],
    validator: Callable[..., Option[JsonRpcError] | bool] | None = None,
    converter: Callable[..., Option[Any] | Result[Any, Exception | JsonRpcError] | Any] | None = None,
)
```

| Parâmetro | Tipo | Padrão | Descrição |
|---|---|---|---|
| `name` | `str` | *(obrigatório)* | O nome do método JSON-RPC. |
| `method` | `Callable[..., Any]` | *(obrigatório)* | A chamável a ser invocada quando este método é despachado. |
| `validator` | `Callable[..., Option[JsonRpcError] \| bool] \| None` | `None` | Uma chamável opcional que recebe os `params` analisados e retorna um sinal de rejeição. |
| `converter` | `Callable[..., Option[Any] \| Result[Any, Exception \| JsonRpcError] \| Any] \| None` | `None` | Uma chamável opcional que transforma os `params` analisados antes do método ser invocado. |

### Protocolo de Validador

O validador recebe os `params` analisados e pode retornar:

| Valor de retorno | Comportamento |
|---|---|
| `Some(JsonRpcError)` | Rejeita com aquele erro |
| `Some(Exception)` | Rejeita com aquele erro envolvido em `InvalidParams` |
| `False` | Rejeita com um erro genérico `InvalidParams` |
| `Exception` ou `JsonRpcError` | Rejeita com aquele erro diretamente |
| `True`, `None`, ou qualquer outro valor truthy | Aceita — continua para conversão ou invocação do método |

### Protocolo de Conversor

O conversor recebe o payload `params` bruto e pode retornar:

| Valor de retorno | Comportamento |
|---|---|
| `Some(value)` | Usa `value` como argumento do método |
| `Nothing()` | Rejeita com `ConversionError` |
| `Ok(value)` | Usa `value` como argumento do método |
| `Err(reason)` | Rejeita com `ConversionError`, anexando `reason` ao `data` |
| Qualquer outro valor | Usa o valor diretamente como argumento do método |
| Lança `Exception` | Rejeita com `ConversionError`, anexando a exceção ao `data` |

### Atributos

| Atributo | Tipo | Descrição |
|---|---|---|
| `name` | `str` | O nome do método JSON-RPC sob o qual este wrapper está registrado. |

### Métodos

#### `__hash__() -> int`

Retorna um hash baseado no nome do método. Dois wrappers com o mesmo nome têm o mesmo hash.

#### `__eq__(other) -> bool`

Compara dois wrappers pelo nome do método.

#### `__call__(params: Option[Any]) -> Result[Any, JsonRpcError]`

Executa o método envolvido com parâmetros opcionais. A validação é executada primeiro, depois a conversão; se qualquer etapa rejeitar os parâmetros, a chamada é interrompida com um `Err`.

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `params` | `Option[Any]` | Um `Option` contendo os parâmetros do método. `Some` significa que parâmetros foram fornecidos; `Nothing` significa que nenhum foi. |

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
JsonRpcDispatcher(
    response_handler: Callable[[JsonRpcResponse], None] | None = None,
)
```

| Parâmetro | Tipo | Padrão | Descrição |
|---|---|---|---|
| `response_handler` | `Callable[[JsonRpcResponse], None] \| None` | `None` | Callback opcional invocado quando um `JsonRpcResponse` é despachado diretamente. |

### Atributos de Classe

| Atributo | Tipo | Descrição |
|---|---|---|
| `ERROR_CASE` | `JsonRpcResponseCtorWrapper.State` | Seletor de resultado para respostas de erro. |
| `RESULT_CASE` | `JsonRpcResponseCtorWrapper.State` | Seletor de resultado para resultados bem-sucedidos. |
| `BOTH_CASES` | `JsonRpcResponseCtorWrapper._When` | Seletor de resultado correspondendo a ambos os resultados. |

### Atributos

| Atributo | Tipo | Descrição |
|---|---|---|
| `request_handler_registry` | `JsonRpcHandlerCollection` | Registro para handlers de requisição. |
| `notification_handler_registry` | `JsonRpcHandlerCollection` | Registro para handlers de notificação. |

### Métodos

#### `emplace_request_handler(*, name, method, validator=None, converter=None) -> bool`

Registra um handler de requisição em uma chamada. Conveniência para `request_handler_registry.add(JsonRpcMethodWrapper(...))`.

| Parâmetro | Tipo | Padrão | Descrição |
|---|---|---|---|
| `name` | `str` | *(obrigatório)* | O nome do método JSON-RPC. |
| `method` | `Callable[..., Any]` | *(obrigatório)* | A chamável a ser invocada quando despachado. |
| `validator` | `Callable[..., Option[JsonRpcError] \| bool] \| None` | `None` | Validador de parâmetros opcional. |
| `converter` | `Callable[..., Option[Any] \| Result[Any, Exception \| JsonRpcError] \| Any] \| None` | `None` | Conversor de parâmetros opcional. |

**Retorna:** `True` se recém-registrado, `False` se o nome já existia.

#### `emplace_notification_handler(*, name, method, validator=None, converter=None) -> bool`

Registra um handler de notificação em uma chamada. Conveniência para `notification_handler_registry.add(JsonRpcMethodWrapper(...))`.

| Parâmetro | Tipo | Padrão | Descrição |
|---|---|---|---|
| `name` | `str` | *(obrigatório)* | O nome do método JSON-RPC. |
| `method` | `Callable[..., Any]` | *(obrigatório)* | A chamável a ser invocada quando despachado. |
| `validator` | `Callable[..., Option[JsonRpcError] \| bool] \| None` | `None` | Validador de parâmetros opcional. |
| `converter` | `Callable[..., Option[Any] \| Result[Any, Exception \| JsonRpcError] \| Any] \| None` | `None` | Conversor de parâmetros opcional. |

**Retorna:** `True` se recém-registrado, `False` se o nome já existia.

#### `emplace_custom_response_ctor(method, ctor, *states)`

Registra um construtor de resposta personalizado para *method*.

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `method` | `str` | O nome do método JSON-RPC ao qual o construtor se aplica. |
| `ctor` | `Callable[..., JsonRpcResponse]` | Chamável que constrói um `JsonRpcResponse`. |
| `*states` | `JsonRpcResponseCtorWrapper.State` | Membros de estado opcionais restringindo quando o *ctor* é usado. |

#### `add_custom_response_ctor(ctor: JsonRpcResponseCtorWrapper)`

Registra um construtor de resposta personalizado pré-construído. Substitui qualquer construtor previamente registrado para o mesmo método.

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `ctor` | `JsonRpcResponseCtorWrapper` | O wrapper que vincula um construtor a um nome de método. |

#### `__call__(data) -> Option[Result[JsonRpcResponse, JsonRpcError]]`

Despacha uma mensagem JSON-RPC.

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `data` | `str \| JsonRpcRequest \| JsonRpcNotification \| JsonRpcResponse \| Result[...]` | Uma string JSON, `JsonRpcRequest`, `JsonRpcNotification`, `JsonRpcResponse` ou `Result`. |

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

#### `try_parse(data: str) -> Result[JsonRpcResponse | JsonRpcNotification | JsonRpcRequest, JsonRpcError]` *(classmethod)*

Tenta analisar uma string JSON em uma resposta, requisição ou notificação. Primeiro tenta `JsonRpcResponse`; em caso de falha, recorre a `JsonRpcNotification`; em caso de falha, recorre a `JsonRpcRequest`.

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `data` | `str` | Uma string codificada em JSON. |

**Retorna:** `Ok(response | notification | request)` em caso de sucesso, ou `Err(JsonRpcError)` em caso de falha de parsing.

---

## `JsonRpcResponseCtorWrapper`

```python
class JsonRpcResponseCtorWrapper
```

Vincula um construtor personalizado de `JsonRpcResponse` a um nome de método. O wrapper registra *quando* o construtor se aplica — resultados bem-sucedidos, erros ou ambos — para que o dispatcher possa escolher o tipo de resposta correto para cada resultado.

### Construtor

```python
JsonRpcResponseCtorWrapper(
    method: str,
    ctor: Callable[..., JsonRpcResponse],
    *states: JsonRpcResponseCtorWrapper.State,
)
```

| Parâmetro | Tipo | Padrão | Descrição |
|---|---|---|---|
| `method` | `str` | *(obrigatório)* | O nome do método JSON-RPC ao qual este construtor se aplica. |
| `ctor` | `Callable[..., JsonRpcResponse]` | *(obrigatório)* | Chamável que recebe argumentos de palavra-chave (`id`, `result` ou `error`, e `jsonrpc`) e retorna um `JsonRpcResponse`. |
| `*states` | `State` | Ambos os resultados | Membros `State` opcionais limitando quando o *ctor* é usado. |

### Classe Interna: `State`

```python
class State(Enum)
```

Seletor de resultado controlando quando um construtor é aplicado.

| Membro | Valor | Descrição |
|---|---|---|
| `Result` | `1` | O construtor lida com resultados bem-sucedidos. |
| `Error` | `2` | O construtor lida com respostas de erro. |

### Atributos

| Atributo | Tipo | Descrição |
|---|---|---|
| `method` | `str` | O nome do método JSON-RPC ao qual este construtor está vinculado. |
| `when` | `_When` | O seletor de resultado para este construtor. |
