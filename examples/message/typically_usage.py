from typing import cast

from pyfplib import Result

from jrpc_core.messages import (
    JsonRpcErrorCode,
    JsonRpcNotification,
    JsonRpcRequest,
    JsonRpcResponse,
    try_parse,
)


def handle_incoming_message(data: str):
    res = try_parse(data)
    if res.is_ok():
        jrpc_message = res.unwrap()
        if isinstance(jrpc_message, JsonRpcRequest):
            handle_request(jrpc_message)
        elif isinstance(jrpc_message, JsonRpcNotification):
            handle_notification(jrpc_message)
        else:
            handle_response(jrpc_message)
    else:
        print(f"ERROR: {res.unwrap_err()}")


def handle_request(req: JsonRpcRequest):
    print(f"INCOMING REQUEST: {req}")
    if req.method == "sum":
        result = Result.try_call(sum, cast(list[int], req.params)).map_err(
            lambda err: JsonRpcErrorCode.ExecutionError.into(str(err))
        )
        res = JsonRpcResponse.from_result(req.id, result)
        # or
        # res = req.into(result)
    else:
        jrpc_err = JsonRpcErrorCode.MethodNotFound.into()
        res = JsonRpcResponse.from_jrpc_error(req.id, jrpc_err)
        # or
        # res = req.into(Err(jrpc_err))
    send_response(res)


def handle_notification(ntf: JsonRpcNotification):
    print(f"INCOMING NOTIFICATION: {ntf}")
    if ntf.method == "sum":
        result = Result.try_call(sum, cast(list[int], ntf.params))
        if result.is_ok():
            print(f"NOTIFICATION HANDLER OK: {result.unwrap()}")
        else:
            print(f"NOTIFICATION HANDLER ERR: {result.unwrap_err()}")
    else:
        print(f"NOTIFICATION HANDLER ERR: method `{ntf.method}` not found")


def handle_response(res: JsonRpcResponse):
    print(f"INCOMING RESPONSE: {res}")


def send_response(res: JsonRpcResponse):
    data = res.serialize()
    handle_incoming_message(data)


def send_request():
    message = JsonRpcRequest(method="sum", params=[1, 2, 3])
    handle_incoming_message(message.serialize())


def send_bad_request():
    message = JsonRpcRequest(method="concat", params=["1", "2", "3"])
    handle_incoming_message(message.serialize())


def send_notification():
    message = JsonRpcNotification(method="sum", params=[11, 12, 13])
    handle_incoming_message(message.serialize())


def send_bad_notification():
    message = JsonRpcNotification(method="concat", params=["1", "2", "3"])
    handle_incoming_message(message.serialize())


def main():
    send_request()
    send_notification()
    send_bad_request()
    send_bad_notification()


if __name__ == "__main__":
    main()
