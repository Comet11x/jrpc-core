# Primeiros Passos

## Instalação

```bash
pip install jrpc-core
```

## Exemplo Mínimo

```python
from pyfplib import Result
from jrpc_core.messages import JsonRpcRequest, JsonRpcResponse

# Criar uma requisição
request = JsonRpcRequest(method="add", params=[1, 2])
print(request.to_json())
# {"jsonrpc":"2.0","method":"add","params":[1,2],"id":"<uuid>"}

# Criar uma resposta a partir de um Result
response = request.into(Result.ok(3))
print(response.to_json())
# {"jsonrpc":"2.0","id":"<uuid>","result":3}
```

## Usando o Dispatcher

```python
from pyfplib import Result
from jrpc_core.dispatcher import JsonRpcDispatcher, JsonRpcMethodWrapper

def add(args):
    return args[0] + args[1]

dispatcher = JsonRpcDispatcher()
dispatcher.request_handler_registry.add(
    JsonRpcMethodWrapper(name="add", method=add)
)

# Enviar uma requisição
response_opt = dispatcher('{"jsonrpc":"2.0","method":"add","params":[1,2],"id":"1"}')
response = response_opt.unwrap().unwrap()
print(response.to_json())
# {"jsonrpc":"2.0","id":"1","result":3}
```

## Próximos Passos

- [API de Mensagens](/pt/guide/messages) — referência completa para todos os modelos de mensagem
- [API de Dispatcher](/pt/guide/dispatcher) — referência completa para roteamento e registro de handlers
