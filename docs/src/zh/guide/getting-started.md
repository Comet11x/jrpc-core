# 快速开始

## 安装

```bash
pip install jrpc-core
```

## 最小示例

```python
from pyfplib import Result
from jrpc_core.messages import JsonRpcRequest, JsonRpcResponse

# 创建请求
request = JsonRpcRequest(method="add", params=[1, 2])
print(request.to_json())
# {"jsonrpc":"2.0","method":"add","params":[1,2],"id":"<uuid>"}

# 从 Result 创建响应
response = request.into(Result.ok(3))
print(response.to_json())
# {"jsonrpc":"2.0","id":"<uuid>","result":3}
```

## 使用调度器

```python
from pyfplib import Result
from jrpc_core.dispatcher import JsonRpcDispatcher, JsonRpcMethodWrapper

def add(args):
    return args[0] + args[1]

dispatcher = JsonRpcDispatcher()
dispatcher.request_handler_registry.add(
    JsonRpcMethodWrapper(name="add", method=add)
)

# 发送请求
response_opt = dispatcher('{"jsonrpc":"2.0","method":"add","params":[1,2],"id":"1"}')
response = response_opt.unwrap().unwrap()
print(response.to_json())
# {"jsonrpc":"2.0","id":"1","result":3}
```

## 接下来

- [消息 API](/zh/guide/messages) — 所有消息模型的完整参考
- [调度器 API](/zh/guide/dispatcher) — 路由和处理程序注册的完整参考
