import asyncio

from jrpc_core import (
    JsonRpcDispatcher,
    JsonRpcError,
    JsonRpcMethodWrapper,
    JsonRpcNotification,
    JsonRpcRequest,
    JsonRpcResponse,
)
from pyfplib import Option, Result


def foo(args: list[str]) -> str:
    return "-".join(args)


def bar(args: list[int]) -> int:
    print("Call bar")
    return sum(args)


def get_request_1() -> JsonRpcRequest:
    return JsonRpcRequest(method="concat", params=["a", "b", "c"])


def get_request_2() -> JsonRpcRequest:
    return JsonRpcRequest(method="sum", params=[1, 2, 3])


def get_notification() -> JsonRpcNotification:
    return JsonRpcNotification(method="sum", params=[1, 2, 3])


def handle_response(maybe_res: Option[Result[JsonRpcResponse, JsonRpcError]]):
    if maybe_res.is_some():
        res1 = maybe_res.unwrap()
        if res1.is_ok():
            print(res1.unwrap().model_dump_json())
        else:
            print(res1.unwrap_err())
    else:
        print("Error: option is empty")


async def async_main():
    mw1 = JsonRpcMethodWrapper(name="concat", method=foo)
    mw2 = JsonRpcMethodWrapper(name="sum", method=bar)
    dispatcher = JsonRpcDispatcher()
    dispatcher.request_handler_registry.add(mw1)
    dispatcher.request_handler_registry.add(mw2)
    dispatcher.notification_handler_registry.add(mw2)
    maybe_res1 = await dispatcher(get_request_1())
    maybe_res2 = await dispatcher(get_request_2())
    maybe_res3 = await dispatcher(get_notification())
    handle_response(maybe_res1)
    handle_response(maybe_res2)
    handle_response(maybe_res3)


def main():
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
