import asyncio
from typing import Callable

from jrpc_core import (
    JsonRpcDispatcher,
    JsonRpcError,
    JsonRpcRequest,
    JsonRpcResponse,
    JsonRpcNotification,
)
from pyfplib import Option, Result
from enum import Enum

dispatcher = JsonRpcDispatcher()


@dispatcher.notification(method="concat")
@dispatcher.request(method="join")
def foo(args: list[str]) -> str:
    print("Incoming data of foo: ", args)
    return "-".join(args)


@dispatcher.request(method="sum")
@dispatcher.notification(method="sum")
def bar(args: list[int]) -> int:
    print("Incoming data of bar: ", args)
    return sum(args)


class Kind(Enum):
    Request = 0
    Notification = 1

    def into(self) -> Callable[..., JsonRpcRequest | JsonRpcNotification]:
        if self == Kind.Notification:
            return JsonRpcNotification
        else:
            return JsonRpcRequest


def make_message_to_get_sum(
    kind: Kind = Kind.Request,
) -> JsonRpcRequest | JsonRpcNotification:
    return kind.into()(method="sum", params=[1, 2, 3])


def make_message_to_concat(
    kind: Kind = Kind.Request,
) -> JsonRpcRequest | JsonRpcNotification:
    return kind.into()(method="concat", params=["1", "2", "3"])


def make_message_to_join(
    kind: Kind = Kind.Request,
) -> JsonRpcRequest | JsonRpcNotification:
    return kind.into()(method="join", params=["1", "2", "3"])


def handle_response(maybe_res: Option[Result[JsonRpcResponse, JsonRpcError]]):
    if maybe_res.is_some():
        res1 = maybe_res.unwrap()
        if res1.is_ok():
            print(res1.unwrap().model_dump_json())
            # print(res1.unwrap())
        else:
            print(res1.unwrap_err())
    else:
        print("Error: option is empty")


async def async_main():
    req = make_message_to_join()
    print(req)
    handle_response(await dispatcher(req))
    print("-" * 10)

    req1 = make_message_to_concat(Kind.Request)
    print(req1)
    handle_response(await dispatcher(req1))
    print("-" * 10)

    not1 = make_message_to_concat(Kind.Notification)
    print(not1)
    await dispatcher(not1)
    print("-" * 10)

    req2 = make_message_to_get_sum(Kind.Request)
    print(req2)
    handle_response(await dispatcher(req2))
    print("-" * 10)

    not2 = make_message_to_get_sum(Kind.Notification)
    print(not2)
    await dispatcher(not2)
    print("-" * 10)


def main():
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
