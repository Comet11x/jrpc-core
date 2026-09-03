# Getting Started

## Installation

```bash
pip install jrpc-core
```

## Minimal Example

```python
from pyfplib import Result
from jrpc_core.messages import JsonRpcRequest, JsonRpcResponse

# Build a request
request = JsonRpcRequest(method="add", params=[1, 2])
print(request.serialize())
# {"jsonrpc":"2.0","method":"add","params":[1,2],"id":"<uuid>"}

# Create a response from a Result
response = request.into(Result.ok(3))
print(response.to_json())
# {"jsonrpc":"2.0","id":"<uuid>","result":3}
```

## Using the Dispatcher

```python
from pyfplib import Result
from jrpc_core.dispatcher import JsonRpcDispatcher, JsonRpcMethodWrapper

dispatcher = JsonRpcDispatcher()

@dispatcher.request()
def sum(args: list[int]):
    return sum(args)

@dispatcher.request(method="concat")
def join(args: list[str]):
    retu

dispatcher.request_handler_registry.add(
    JsonRpcMethodWrapper(name="add", method=add)
)

# Dispatch a request
response_opt = dispatcher('{"jsonrpc":"2.0","method":"add","params":[1,2],"id":"1"}')
response = response_opt.unwrap().unwrap()
print(response.to_json())
# {"jsonrpc":"2.0","id":"1","result":3}
```

## What's Next?

- [Messages API](/guide/messages) — full reference for all message models
- [Dispatcher API](/guide/dispatcher) — full reference for routing and handler registration
