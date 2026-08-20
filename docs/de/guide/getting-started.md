# Erste Schritte

## Installation

```bash
pip install jrpc-core
```

## Minimalbeispiel

```python
from pyfplib import Result
from jrpc_core.messages import JsonRpcRequest, JsonRpcResponse

# Anfrage erstellen
request = JsonRpcRequest(method="add", params=[1, 2])
print(request.to_json())
# {"jsonrpc":"2.0","method":"add","params":[1,2],"id":"<uuid>"}

# Antwort aus einem Result erstellen
response = request.into(Result.ok(3))
print(response.to_json())
# {"jsonrpc":"2.0","id":"<uuid>","result":3}
```

## Verwendung des Dispatchers

```python
from pyfplib import Result
from jrpc_core.dispatcher import JsonRpcDispatcher, JsonRpcMethodWrapper

def add(args):
    return args[0] + args[1]

dispatcher = JsonRpcDispatcher()
dispatcher.request_handler_registry.add(
    JsonRpcMethodWrapper(name="add", method=add)
)

# Anfrage senden
response_opt = dispatcher('{"jsonrpc":"2.0","method":"add","params":[1,2],"id":"1"}')
response = response_opt.unwrap().unwrap()
print(response.to_json())
# {"jsonrpc":"2.0","id":"1","result":3}
```

## Was als Nächstes?

- [Nachrichten-API](/de/guide/messages) — vollständige Referenz für alle Nachrichtenmodelle
- [Dispatcher-API](/de/guide/dispatcher) — vollständige Referenz für Routing und Handler-Registrierung
