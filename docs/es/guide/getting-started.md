# Primeros Pasos

## Instalación

```bash
pip install jrpc-core
```

## Ejemplo Mínimo

```python
from pyfplib import Result
from jrpc_core.messages import JsonRpcRequest, JsonRpcResponse

# Crear una solicitud
request = JsonRpcRequest(method="add", params=[1, 2])
print(request.to_json())
# {"jsonrpc":"2.0","method":"add","params":[1,2],"id":"<uuid>"}

# Crear una respuesta a partir de un Result
response = request.into(Result.ok(3))
print(response.to_json())
# {"jsonrpc":"2.0","id":"<uuid>","result":3}
```

## Uso del Dispatcher

```python
from pyfplib import Result
from jrpc_core.dispatcher import JsonRpcDispatcher, JsonRpcMethodWrapper

def add(args):
    return args[0] + args[1]

dispatcher = JsonRpcDispatcher()
dispatcher.request_handler_registry.add(
    JsonRpcMethodWrapper(name="add", method=add)
)

# Enviar una solicitud
response_opt = dispatcher('{"jsonrpc":"2.0","method":"add","params":[1,2],"id":"1"}')
response = response_opt.unwrap().unwrap()
print(response.to_json())
# {"jsonrpc":"2.0","id":"1","result":3}
```

## ¿Qué Sigue?

- [API de Mensajes](/es/guide/messages) — referencia completa de todos los modelos de mensaje
- [API de Dispatcher](/es/guide/dispatcher) — referencia completa de enrutamiento y registro de handlers
