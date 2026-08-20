# 시작하기

## 설치

```bash
pip install jrpc-core
```

## 최소 예제

```python
from pyfplib import Result
from jrpc_core.messages import JsonRpcRequest, JsonRpcResponse

# 요청 생성
request = JsonRpcRequest(method="add", params=[1, 2])
print(request.to_json())
# {"jsonrpc":"2.0","method":"add","params":[1,2],"id":"<uuid>"}

# Result에서 응답 생성
response = request.into(Result.ok(3))
print(response.to_json())
# {"jsonrpc":"2.0","id":"<uuid>","result":3}
```

## 디스패처 사용

```python
from pyfplib import Result
from jrpc_core.dispatcher import JsonRpcDispatcher, JsonRpcMethodWrapper

def add(args):
    return args[0] + args[1]

dispatcher = JsonRpcDispatcher()
dispatcher.request_handler_registry.add(
    JsonRpcMethodWrapper(name="add", method=add)
)

# 요청 전송
response_opt = dispatcher('{"jsonrpc":"2.0","method":"add","params":[1,2],"id":"1"}')
response = response_opt.unwrap().unwrap()
print(response.to_json())
# {"jsonrpc":"2.0","id":"1","result":3}
```

## 다음 단계

- [메시지 API](/ko/guide/messages) — 모든 메시지 모델에 대한 전체 참조
- [디스패처 API](/ko/guide/dispatcher) — 라우팅 및 핸들러 등록에 대한 전체 참조
