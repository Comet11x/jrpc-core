# SPDX-FileCopyrightText: 2026-present comet11x <comet11x@protonmail.com>
#
# SPDX-License-Identifier: MIT
from typing import Any, Callable
from pyfplib import Ok, Option, Result, Err, Nothing, Some

from jrpc_core.messages import (
    JsonRpcRequest,
    JsonRpcNotification,
    JsonRpcResponse,
    JsonRpcError,
    JsonRpcErrorCode,
)


class JsonRpcMethodWrapper:
    def __init__(
        self,
        *,
        name: str,
        method: Callable[..., Any],
        validators: list[Callable[..., Option[JsonRpcError]]] | None = None,
    ):
        self._name = name
        self._method = method
        self._validators = validators or []

    @property
    def name(self) -> str:
        return self._name

    def __hash__(self) -> int:
        return hash(self._name)

    def __eq__(self, other: "JsonRpcMethodWrapper"):
        return isinstance(other, JsonRpcMethodWrapper) and self._name == other._name

    @classmethod
    def _handle_invalid_params_error(cls, error: JsonRpcError | Exception):
        if isinstance(error, JsonRpcError):
            return error
        else:
            return JsonRpcErrorCode.InvalidParams.into(error)

    def __call__(self, args: Option[Any]) -> Result[Any, JsonRpcError]:
        if args.is_some():
            args = args.unwrap()
            for validator in self._validators:
                maybe_error = validator(args)
                if isinstance(maybe_error, Option) and maybe_error.is_some():
                    return Err(self._handle_invalid_params_error(maybe_error.unwrap()))
                elif isinstance(maybe_error, bool) and not maybe_error:
                    return Err(JsonRpcErrorCode.InvalidParams.into())
                elif isinstance(maybe_error, Exception) or isinstance(
                    maybe_error, JsonRpcError
                ):
                    return Err(JsonRpcError.from_error(maybe_error))

            res = (
                Result.try_call(self._method, args)
                .map_err(
                    lambda err: (
                        err
                        if isinstance(err, JsonRpcError)
                        else JsonRpcErrorCode.ExecutionError.into(err)
                    )
                )
                .flatten()
            )
        else:
            res = (
                Result.try_call(self._method)
                .map_err(
                    lambda err: (
                        err
                        if isinstance(err, JsonRpcError)
                        else JsonRpcErrorCode.ExecutionError.into(err)
                    )
                )
                .flatten()
            )

        return res


class JsonRpcHandlerCollection:
    def __init__(self):
        self._registry: dict[str, JsonRpcMethodWrapper] = {}

    def add(self, method: JsonRpcMethodWrapper) -> bool:
        not_exists = self._registry.get(method.name) is None

        if not_exists:
            self._registry[method.name] = method

        return not_exists

    def try_get(self, name: str) -> Option[JsonRpcMethodWrapper]:
        return Option.from_optional(self._registry.get(name))

    def exists(self, name: str) -> bool:
        return self._registry.get(name)

    def remove_by_name(self, name: str) -> bool:
        exists = self._registry.get(name) is not None
        if exists:
            del self._registry[exists]
        return exists

    def remove(self, method: str | JsonRpcMethodWrapper) -> bool:
        if isinstance(method, JsonRpcMethodWrapper):
            method = method.name
        ret_value = False
        if isinstance(method, str):
            ret_value = self.remove_by_name(method)
        return ret_value


class JsonRpcDispatcher:
    def __init__(self):
        self._request_handler_registry = JsonRpcHandlerCollection()
        self._notification_handler_registry = JsonRpcHandlerCollection()

    @property
    def request_handler_registry(self) -> JsonRpcHandlerCollection:
        return self._request_handler_registry

    @property
    def notification_handler_registry(self) -> JsonRpcHandlerCollection:
        return self._notification_handler_registry

    def __call__(
        self, data: str | JsonRpcRequest | JsonRpcNotification
    ) -> Option[Result[JsonRpcResponse, JsonRpcError]]:
        if isinstance(data, str):
            res = self.try_parse(data)
            if res.is_ok():
                return self(res.unwrap())
            else:
                return Some(Err(JsonRpcErrorCode.ParseError.into()))
        elif isinstance(data, JsonRpcNotification):
            return self._handle_notification(data).map(lambda err: Err(err))
        elif isinstance(data, JsonRpcRequest):
            return Some(Ok(self._handle_request(data)))
        else:
            return Some(Err(JsonRpcErrorCode.InternalError.into()))

    def _handle_notification(
        self, notification: JsonRpcNotification
    ) -> Option[JsonRpcError]:
        maybe_method = self._notification_handler_registry.try_get(notification.method)
        if maybe_method.is_none():
            return Some(JsonRpcErrorCode.MethodNotFound.into())
        method = maybe_method.unwrap()
        method(self._extract_params(notification))
        return Nothing()

    def _handle_request(self, request: JsonRpcRequest) -> JsonRpcResponse:
        maybe_method = self._request_handler_registry.try_get(request.method)
        if maybe_method.is_none():
            return request.into(JsonRpcErrorCode.MethodNotFound.into())

        method = maybe_method.unwrap()
        ret_value = method(self._extract_params(request))
        return request.into(ret_value)

    @classmethod
    def _extract_params(
        cls, rpc_object: JsonRpcRequest | JsonRpcNotification
    ) -> Option[Any]:
        res = Result.try_call(getattr, rpc_object, "params")
        return res.ok()

    @classmethod
    def try_parse(
        cls, data: str
    ) -> Result[JsonRpcRequest | JsonRpcNotification, JsonRpcError]:
        return (
            Result.try_call(JsonRpcRequest.try_from_json, data)
            .map_err(lambda _: Result.try_call(JsonRpcNotification.try_from_json, data))
            .flatten()
        )
