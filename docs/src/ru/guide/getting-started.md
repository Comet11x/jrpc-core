# Начало работы

## Установка

```bash
pip install jrpc-core
```

## Минимальный пример

```python
from pyfplib import Result
from jrpc_core.messages import JsonRpcRequest, JsonRpcResponse

# Создание запроса
request = JsonRpcRequest(method="add", params=[1, 2])
print(request.to_json())
# {"jsonrpc":"2.0","method":"add","params":[1,2],"id":"<uuid>"}

# Создание ответа из Result
response = request.into(Result.ok(3))
print(response.to_json())
# {"jsonrpc":"2.0","id":"<uuid>","result":3}
```

## Использование диспетчера

```python
from pyfplib import Result
from jrpc_core.dispatcher import JsonRpcDispatcher, JsonRpcMethodWrapper

def add(args):
    return args[0] + args[1]

dispatcher = JsonRpcDispatcher()
dispatcher.request_handler_registry.add(
    JsonRpcMethodWrapper(name="add", method=add)
)

# Отправка запроса
response_opt = dispatcher('{"jsonrpc":"2.0","method":"add","params":[1,2],"id":"1"}')
response = response_opt.unwrap().unwrap()
print(response.to_json())
# {"jsonrpc":"2.0","id":"1","result":3}
```

## Что дальше?

- [API сообщений](/ru/guide/messages) — полный справочник по моделям сообщений
- [API диспетчера](/ru/guide/dispatcher) — полный справочник по маршрутизации и регистрации обработчиков
