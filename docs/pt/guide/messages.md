# API de Mensagens

Todas as primitivas de mensagem estão no módulo `jrpc_core.messages`.

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

Alias de tipo para o identificador de uma mensagem JSON-RPC. Um identificador válido é um `str`, `int`, `float` ou `None`. A variante `None` é permitida apenas em notificações.

### `JsonRpcParams`

```python
JsonRpcParams = dict[str, Any] | list[Any] | None
```

Alias de tipo para valores de `params` do JSON-RPC. Os parâmetros podem ser um mapeamento nomeado (`dict`), uma lista posicional (`list`) ou `None` quando omitidos.

---

## `JsonRpcErrorCode`

```python
class JsonRpcErrorCode(Enum)
```

Enumeração dos códigos de erro padrão do JSON-RPC 2.0. Cada membro mapeia para o código inteiro definido pela especificação ou extensões comuns (`-32xxx` reservado, `-320xx` definido pelo servidor).

### Membros

| Membro | Valor | Descrição |
|---|---|---|
| `ParseError` | `-32700` | JSON inválido foi recebido pelo servidor. |
| `InternalError` | `-32603` | Ocorreu um erro interno do JSON-RPC. |
| `InvalidParams` | `-32602` | Os parâmetros enviados com o método são inválidos. |
| `MethodNotFound` | `-32601` | O método não existe ou não está disponível. |
| `InvalidRequest` | `-32600` | O JSON enviado não é um objeto de requisição válido. |
| `ExecutionError` | `-32000` | Ocorreu um erro de execução definido pelo servidor. |

### Métodos

#### `__int__() -> int`

Retorna o valor inteiro deste código de erro.

```python
>>> int(JsonRpcErrorCode.ParseError)
-32700
```

#### `description() -> str`

Retorna uma descrição legível deste código de erro.

```python
>>> JsonRpcErrorCode.ParseError.description()
'Parse error'
```

#### `default() -> JsonRpcErrorCode` *(static)*

Retorna o código de erro padrão usado quando nenhum outro código é apropriado. Retorna `InternalError`.

```python
>>> JsonRpcErrorCode.default()
<JsonRpcErrorCode.InternalError: -32603>
```

#### `into(data: Any = None) -> JsonRpcError`

Cria um `JsonRpcError` a partir deste código.

| Parâmetro | Tipo | Padrão | Descrição |
|---|---|---|---|
| `data` | `Any` | `None` | Dados extras opcionais anexados ao erro. |

**Retorna:** Um novo `JsonRpcError` com este código e sua descrição.

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

Versões de protocolo JSON-RPC suportadas.

| Membro | Valor |
|---|---|
| `Version1` | `"1.0"` |
| `Version2` | `"2.0"` |

---

## `JsonRpcError`

```python
class JsonRpcError(BaseModel)
```

Um objeto de erro JSON-RPC 2.0.

### Atributos

| Atributo | Tipo | Padrão | Descrição |
|---|---|---|---|
| `code` | `JsonRpcErrorCode \| int` | `JsonRpcErrorCode.InternalError` | Um código de erro inteiro. |
| `message` | `str` | `"Something went wrong"` | Uma descrição curta e legível. |
| `data` | `Any \| None` | `None` | Informações extras opcionais sobre o erro. |

### Métodos

#### `default() -> JsonRpcError` *(static)*

Retorna um erro padrão com `JsonRpcErrorCode.InternalError`.

```python
>>> JsonRpcError.default()
JsonRpcError(code=<JsonRpcErrorCode.InternalError: -32603>, message='Something went wrong', data=None)
```

#### `from_error(error: JsonRpcError | Any) -> JsonRpcError` *(static)*

Converte um valor arbitrário em um `JsonRpcError`. Se *error* já for um `JsonRpcError`, ele é retornado como está. Caso contrário, a função tenta extrair um atributo `code` e constrói um erro ao redor dele, recorrendo a `JsonRpcErrorCode.InternalError`.

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `error` | `JsonRpcError \| Any` | O valor a ser convertido. |

**Retorna:** Uma instância de `JsonRpcError`.

```python
>>> JsonRpcError.from_error(RuntimeError("oops"))
JsonRpcError(code=<JsonRpcErrorCode.InternalError: -32603>, message='Internal error', data=RuntimeError('oops'))
```

#### `try_from(value: Option[JsonRpcError | Any]) -> Option[JsonRpcError]` *(static)*

Tenta converter um `Option` em um erro.

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `value` | `Option[JsonRpcError \| Any]` | Um `Option` que pode conter um valor a ser convertido. |

**Retorna:** `Some(JsonRpcError)` se *value* era `Some`, caso contrário `Nothing`.

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

Um objeto de requisição JSON-RPC 2.0. Contém um nome de `method`, um payload de `params` opcional e um `id` que o cliente usa para correlacionar a resposta.

### Atributos

| Atributo | Tipo | Padrão | Descrição |
|---|---|---|---|
| `method` | `str` | *(obrigatório)* | O nome do procedimento remoto a ser invocado. Deve ser uma string não vazia. |
| `id` | `JsonRpcId` | `str(uuid4())` | Um identificador único para esta requisição (UUID gerado automaticamente por padrão). |
| `params` | `JsonRpcParams` | `None` | Argumentos posicionais ou nomeados opcionais para o método. |
| `jsonrpc` | `JsonRpcVersion` | `Version2` | A versão do protocolo. |

### Métodos

#### `try_from_dict(data: dict) -> Result[JsonRpcRequest, Exception]` *(classmethod)*

Tenta construir uma requisição a partir de um dicionário simples.

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `data` | `dict[str, Any]` | Um dicionário com os campos de requisição JSON-RPC. |

**Retorna:** `Ok(request)` em caso de sucesso, ou `Err(exception)` em caso de falha de validação.

```python
>>> JsonRpcRequest.try_from_dict({"method": "add", "id": 1}).is_ok()
True
```

#### `try_from_json(data: str) -> Result[JsonRpcRequest, Exception]` *(classmethod)*

Tenta construir uma requisição a partir de uma string JSON.

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `data` | `str` | Uma string codificada em JSON representando uma requisição. |

**Retorna:** `Ok(request)` em caso de sucesso, ou `Err(exception)` em caso de falha de parsing/validação.

```python
>>> JsonRpcRequest.try_from_json('{"method":"add","id":1}').is_ok()
True
```

#### `to_dict() -> dict[str, Any]`

Serializa a requisição em um dicionário simples. A chave `params` é omitida quando `None`.

**Retorna:** Um dicionário adequado para serialização JSON.

```python
>>> JsonRpcRequest(method="add", params=[1, 2]).to_dict()
{'method': 'add', 'id': '<uuid>', 'params': [1, 2], 'jsonrpc': '2.0'}
```

#### `to_json() -> str`

Serializa a requisição em uma string JSON.

**Retorna:** Uma representação JSON compacta desta requisição.

#### `into(result: Result[Any, JsonRpcError]) -> JsonRpcResponse`

Cria um `JsonRpcResponse` a partir do resultado de um handler. Aceita um `Result`, um `JsonRpcError` ou um valor bruto.

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `result` | `Result[Any, JsonRpcError]` | O resultado do processamento desta requisição. |

**Retorna:** Uma resposta contendo o resultado descompactado ou o erro.

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

Um objeto de notificação JSON-RPC 2.0. Idêntico a uma requisição, mas omite o campo `id`, indicando que nenhuma resposta é esperada do servidor.

### Atributos

| Atributo | Tipo | Padrão | Descrição |
|---|---|---|---|
| `method` | `str` | *(obrigatório)* | O nome do evento ou procedimento sendo anunciado. Deve ser uma string não vazia. |
| `params` | `JsonRpcParams` | `None` | Argumentos posicionais ou nomeados opcionais. |
| `jsonrpc` | `JsonRpcVersion` | `Version2` | A versão do protocolo. |

::: warning
Uma notificação **não** deve conter um campo `id`. Tentar construir uma com um `id` levanta um erro de validação.
:::

### Métodos

#### `try_from_dict(data: dict) -> Result[JsonRpcNotification, Exception]` *(classmethod)*

Tenta construir uma notificação a partir de um dicionário simples.

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `data` | `dict[str, Any]` | Um dicionário com os campos de notificação JSON-RPC. |

**Retorna:** `Ok(notification)` em caso de sucesso, ou `Err(exception)` em caso de falha de validação.

#### `try_from_json(data: str) -> Result[JsonRpcNotification, Exception]` *(classmethod)*

Tenta construir uma notificação a partir de uma string JSON.

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `data` | `str` | Uma string codificada em JSON representando uma notificação. |

**Retorna:** `Ok(notification)` em caso de sucesso, ou `Err(exception)` em caso de falha de parsing/validação.

#### `to_dict() -> dict[str, Any]`

Serializa a notificação em um dicionário simples. A chave `params` é omitida quando `None`.

**Retorna:** Um dicionário adequado para serialização JSON.

#### `to_json() -> str`

Serializa a notificação em uma string JSON.

**Retorna:** Uma representação JSON compacta desta notificação.

---

## `JsonRpcResponse`

```python
class JsonRpcResponse(BaseModel)
```

Um objeto de resposta JSON-RPC 2.0. Exatamente um de `result` ou `error` deve ser definido. O `id` corresponde ao `id` da requisição original.

### Atributos

| Atributo | Tipo | Padrão | Descrição |
|---|---|---|---|
| `id` | `JsonRpcId` | *(obrigatório)* | O identificador da requisição a que esta resposta corresponde. |
| `result` | `Any` | `None` | O valor de retorno quando o método foi executado com sucesso. |
| `error` | `JsonRpcError \| None` | `None` | Um `JsonRpcError` quando o método falhou. |
| `jsonrpc` | `JsonRpcVersion` | `Version2` | A versão do protocolo. |

::: warning
Uma resposta deve ter **ou** um `result` **ou** um `error`, não ambos. Tentar definir ambos levanta um erro de validação.
:::

### Métodos

#### `from_result(id, result) -> JsonRpcResponse` *(static)*

Constrói uma resposta a partir de um `Result`.

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `id` | `JsonRpcId` | O identificador da requisição a ser retornado. |
| `result` | `Result[Any, JsonRpcError]` | O resultado do handler. |

**Retorna:** Um `JsonRpcResponse` completamente construído.

```python
>>> from pyfplib import Result
>>> JsonRpcResponse.from_result(1, Result.ok("data"))
JsonRpcResponse(id=1, result='data', error=None, ...)
>>> JsonRpcResponse.from_result(2, Result.err(JsonRpcError(code=JsonRpcErrorCode.InternalError)))
JsonRpcResponse(id=2, result=None, error=JsonRpcError(...), ...)
```

#### `from_jrpc_error(id, error) -> JsonRpcResponse` *(static)*

Constrói uma resposta de erro.

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `id` | `JsonRpcId` | O identificador da requisição a ser retornado. |
| `error` | `JsonRpcError` | O erro a ser incluído. |

**Retorna:** Um `JsonRpcResponse` com apenas `error` definido.

#### `from_jrpc_result(id, result) -> JsonRpcResponse` *(static)*

Constrói uma resposta de sucesso.

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `id` | `JsonRpcId` | O identificador da requisição a ser retornado. |
| `result` | `Any` | O valor de retorno do método. |

**Retorna:** Um `JsonRpcResponse` com apenas `result` definido.

#### `try_from_dict(data: dict) -> Result[JsonRpcResponse, Exception]` *(static)*

Tenta construir uma resposta a partir de um dicionário simples.

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `data` | `dict[str, Any]` | Um dicionário com os campos de resposta JSON-RPC. |

**Retorna:** `Ok(response)` em caso de sucesso, ou `Err(exception)` em caso de falha de validação.

#### `try_from_json(data: str) -> Result[JsonRpcResponse, Exception]` *(static)*

Tenta construir uma resposta a partir de uma string JSON.

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `data` | `str` | Uma string codificada em JSON representando uma resposta. |

**Retorna:** `Ok(response)` em caso de sucesso, ou `Err(exception)` em caso de falha de parsing/validação.

#### `to_dict() -> dict[str, Any]`

Serializa a resposta em um dicionário simples. Quando um `error` está presente, a chave `result` é removida e o código do erro é convertido para `int`. Quando `result` está presente, a chave `error` é removida.

**Retorna:** Um dicionário adequado para serialização JSON.

#### `to_json() -> str`

Serializa a resposta em uma string JSON.

**Retorna:** Uma representação JSON compacta desta resposta.

---

## `try_parse()`

```python
def try_parse(data: str) -> Result[JsonRpcRequest | JsonRpcNotification, JsonRpcError]
```

Tenta analisar uma string JSON como uma mensagem JSON-RPC. A função primeiro tenta analisar como um `JsonRpcRequest`; se falhar, recorre a `JsonRpcNotification`. Se ambos falharem, o erro de parsing da tentativa de requisição é retornado.

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `data` | `str` | Uma string codificada em JSON. |

**Retorna:** `Ok(request | notification)` em caso de sucesso, ou `Err(JsonRpcError)` contendo a falha de parsing.

::: warning
Como `JsonRpcRequest` define `id` por padrão via `uuid4()`, um payload de notificação (sem `id`) será aceito como uma requisição. Use `JsonRpcNotification.try_from_json` diretamente quando precisar forçar a forma de notificação.
:::

```python
>>> try_parse('{"jsonrpc":"2.0","method":"add","id":1}')
Result.ok(JsonRpcRequest(method='add', id=1, ...))
```
