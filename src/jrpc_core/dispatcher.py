# SPDX-FileCopyrightText: 2026-present comet11x <comet11x@protonmail.com>
#
# SPDX-License-Identifier: MIT
"""JSON-RPC 2.0 dispatcher: method registration, validation, and request routing.

This module provides a registry-based dispatcher that maps JSON-RPC method
names to callables, validates parameters, and routes incoming requests and
notifications to the appropriate handler.

Typical usage::

    from jrpc_core.dispatcher import JsonRpcDispatcher, JsonRpcMethodWrapper

    dispatcher = JsonRpcDispatcher()
    dispatcher.request_handler_registry.add(
        JsonRpcMethodWrapper(name="add", method=lambda args: args[0] + args[1])
    )
    response = dispatcher(JsonRpcRequest(method="add", params=[1, 2]))
"""

from typing import Any, Callable

from pyfplib import Err, Nothing, Option, Ok, Result, Some

from jrpc_core.messages import (
    JsonRpcError,
    JsonRpcErrorCode,
    JsonRpcNotification,
    JsonRpcRequest,
    JsonRpcResponse,
)


class JsonRpcMethodWrapper:
    """Wraps a callable as a JSON-RPC method with optional parameter validators.

    Attributes:
        name: The JSON-RPC method name this wrapper is registered under.
    """

    def __init__(
        self,
        *,
        name: str,
        method: Callable[..., Any],
        validators: list[Callable[..., Option[JsonRpcError]]] | None = None,
    ):
        """Initialise the wrapper.

        Args:
            name: The JSON-RPC method name.
            method: The callable to invoke when this method is dispatched.
            validators: An optional list of callables that receive the parsed
                ``params`` and return ``Some(error)`` to reject, ``False`` to
                reject with a generic error, an :class:`Exception` /
                :class:`JsonRpcError` to reject, or any truthy / ``None``
                value to accept.
        """
        self._name = name
        self._method = method
        self._validators = validators or []

    @property
    def name(self) -> str:
        """Return the JSON-RPC method name."""
        return self._name

    def __hash__(self) -> int:
        """Return a hash based on the method name."""
        return hash(self._name)

    def __eq__(self, other: "JsonRpcMethodWrapper") -> bool:
        """Compare two wrappers by method name."""
        return isinstance(other, JsonRpcMethodWrapper) and self._name == other._name

    @classmethod
    def _handle_invalid_params_error(cls, error: JsonRpcError | Exception) -> JsonRpcError:
        """Convert a validator result into a :class:`JsonRpcError`.

        If *error* is already a :class:`JsonRpcError` it is returned as-is;
        otherwise it is wrapped with :attr:`JsonRpcErrorCode.InvalidParams`.

        Args:
            error: The error returned by a validator.

        Returns:
            A :class:`JsonRpcError` suitable for the response.
        """
        if isinstance(error, JsonRpcError):
            return error
        else:
            return JsonRpcErrorCode.InvalidParams.into(error)

    def __call__(self, args: Option[Any]) -> Result[Any, JsonRpcError]:
        """Execute the wrapped method with optional parameters.

        Validators are run before the method.  If any validator rejects the
        parameters the call short-circuits with an ``Err``.

        Args:
            args: An ``Option`` containing the method parameters.  ``Some``
                means parameters were provided; ``None`` means none.

        Returns:
            ``Ok(result)`` on success, or ``Err(JsonRpcError)`` on failure.
        """
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
    """A registry of :class:`JsonRpcMethodWrapper` instances keyed by method name."""

    def __init__(self):
        """Initialise an empty handler collection."""
        self._registry: dict[str, JsonRpcMethodWrapper] = {}

    def add(self, method: JsonRpcMethodWrapper) -> bool:
        """Register a method wrapper.

        If a method with the same name already exists, the call is a no-op.

        Args:
            method: The wrapper to register.

        Returns:
            ``True`` if the method was newly registered, ``False`` if it
            already existed.
        """
        not_exists = self._registry.get(method.name) is None

        if not_exists:
            self._registry[method.name] = method

        return not_exists

    def try_get(self, name: str) -> Option[JsonRpcMethodWrapper]:
        """Look up a method by name.

        Args:
            name: The JSON-RPC method name.

        Returns:
            ``Some(wrapper)`` if found, otherwise ``Nothing``.
        """
        return Option.from_optional(self._registry.get(name))

    def exists(self, name: str) -> bool:
        """Check whether a method is registered.

        Args:
            name: The JSON-RPC method name.

        Returns:
            ``True`` if a wrapper with that name exists.
        """
        return name in self._registry

    def remove_by_name(self, name: str) -> bool:
        """Remove a method by name.

        Args:
            name: The JSON-RPC method name to remove.

        Returns:
            ``True`` if the method existed and was removed, ``False``
            otherwise.
        """
        exists = self._registry.get(name) is not None
        if exists:
            del self._registry[name]
        return exists

    def remove(self, method: str | JsonRpcMethodWrapper) -> bool:
        """Remove a method by name or wrapper instance.

        Args:
            method: Either a method name string or a
                :class:`JsonRpcMethodWrapper`.

        Returns:
            ``True`` if the method existed and was removed, ``False``
            otherwise.
        """
        if isinstance(method, JsonRpcMethodWrapper):
            method = method.name
        ret_value = False
        if isinstance(method, str):
            ret_value = self.remove_by_name(method)
        return ret_value


class JsonRpcDispatcher:
    """Routes incoming JSON-RPC messages to registered handlers.

    Maintains separate registries for requests (which expect a response) and
    notifications (fire-and-forget).
    """

    def __init__(self):
        """Initialise the dispatcher with empty handler registries."""
        self._request_handler_registry = JsonRpcHandlerCollection()
        self._notification_handler_registry = JsonRpcHandlerCollection()

    @property
    def request_handler_registry(self) -> JsonRpcHandlerCollection:
        """Return the registry for request handlers."""
        return self._request_handler_registry

    @property
    def notification_handler_registry(self) -> JsonRpcHandlerCollection:
        """Return the registry for notification handlers."""
        return self._notification_handler_registry

    def __call__(
        self, data: str | JsonRpcRequest | JsonRpcNotification
    ) -> Option[Result[JsonRpcResponse, JsonRpcError]]:
        """Dispatch a JSON-RPC message.

        Args:
            data: A JSON string, :class:`JsonRpcRequest`, or
                :class:`JsonRpcNotification`.

        Returns:
            ``Some(Ok(response))`` or ``Some(Err(error))`` for requests,
            ``Some(Err(error))`` when a notification handler is missing,
            or ``Nothing`` when a notification is handled successfully
            (no response expected).
        """
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
        """Route a notification to its handler.

        Args:
            notification: The incoming notification.

        Returns:
            ``Nothing`` if the handler executed successfully, or
            ``Some(JsonRpcError)`` if the method was not found.
        """
        maybe_method = self._notification_handler_registry.try_get(notification.method)
        if maybe_method.is_none():
            return Some(JsonRpcErrorCode.MethodNotFound.into())
        method = maybe_method.unwrap()
        method(self._extract_params(notification))
        return Nothing()

    def _handle_request(self, request: JsonRpcRequest) -> JsonRpcResponse:
        """Route a request to its handler and build a response.

        Args:
            request: The incoming request.

        Returns:
            A :class:`JsonRpcResponse` carrying the result or an error.
        """
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
        """Extract the ``params`` field from a request or notification.

        Args:
            rpc_object: A request or notification object.

        Returns:
            ``Some(params)`` if present, otherwise ``Nothing``.
        """
        res = Result.try_call(getattr, rpc_object, "params")
        return res.ok()

    @classmethod
    def try_parse(
        cls, data: str
    ) -> Result[JsonRpcRequest | JsonRpcNotification, JsonRpcError]:
        """Attempt to parse a JSON string into a request or notification.

        First tries :class:`JsonRpcRequest`; on failure falls back to
        :class:`JsonRpcNotification`.

        Args:
            data: A JSON-encoded string.

        Returns:
            ``Ok(request | notification)`` on success, or ``Err(JsonRpcError)``
            on parse failure.
        """
        return (
            Result.try_call(JsonRpcRequest.try_from_json, data)
            .map_err(lambda _: Result.try_call(JsonRpcNotification.try_from_json, data))
            .flatten()
        )
