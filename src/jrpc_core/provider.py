# SPDX-FileCopyrightText: 2026-present comet11x <comet11x@protonmail.com>
#
# SPDX-License-Identifier: MIT

from typing import Any, Callable
from pyfplib import Option, Result, Err

from jrpc_core.messages import JsonRpcRequest, JsonRpcResponse, JsonRpcError, JsonRpcErrorCode

class JsonRpcMethodWrapper:
    def __init__(self, *, name: str, method: Callable[..., Any], validators: list[Callable[..., Option[JsonRpcError]]] | None = None):
        self._name = name
        self._methos = method
        self._validators = validators or []

    def __call__(self, *args) -> Result[Any, JsonRpcError]:
        for validator in self._validators:
            maybe_error = validator(*args)
            if maybe_error.is_some()
                err: JsonRpcError | Exception = maybe_error.unwrap()
                err: JsonRpcError = err if isinstance(err, JsonRpcError) else JsonRpcError(code=JsonRpcErrorCode.InvalidParams, data=err)
                return Err(err)
        res = Result.try_call(self._methos, *args).map_err(lambda err: err if isinstance(err, JsonRpcError) else JsonRpcError(data=err)).flatten()

        return res

class JsonRpcProvider:

    def __init__(self):
        self.__registry: dict[str, Callable[..., Any]] = {}
