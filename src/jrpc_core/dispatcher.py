# SPDX-FileCopyrightText: 2026-present comet11x <comet11x@protonmail.com>
#
# SPDX-License-Identifier: MIT
"""JSON-RPC 2.0 dispatcher: method registration, validation, and request routing.

This module provides a registry-based dispatcher that maps JSON-RPC method
names to callables, validates parameters, and routes incoming requests and
notifications to the appropriate handler.

Typical usage::

    import asyncio
    from jrpc_core.dispatcher import JsonRpcDispatcher, JsonRpcMethodWrapper

    dispatcher = JsonRpcDispatcher()
    dispatcher.request_handler_registry.add(
        JsonRpcMethodWrapper(name="add", method=lambda args: args[0] + args[1])
    )
    response = asyncio.run(dispatcher(JsonRpcRequest(method="add", params=[1, 2])))
"""

import inspect
from enum import Enum
from typing import Any, Awaitable, Callable

from pyfplib import Err, Nothing, Option, Ok, Result, Some

from jrpc_core.messages import (
    JsonRpcError,
    JsonRpcErrorCode,
    JsonRpcNotification,
    JsonRpcRequest,
    JsonRpcResponse,
    try_parse,
)

ConverterType = Callable[..., Option[Any] | Result[Any, Exception | JsonRpcError] | Any]
"""Type alias for a converter callable.

A converter receives the raw ``params`` payload and may return an
``Option``, a ``Result``, or any other value used directly as the
method argument.
"""

ValidatorType = Callable[..., Option[JsonRpcError] | bool]
"""Type alias for a validator callable.

A validator receives the parsed ``params`` payload and reports whether
they are acceptable (see :meth:`JsonRpcMethodWrapper._validate`).
"""


class _AsyncWrapper:
    def __init__(self, fn: Callable[..., Any]):
        self._fn = fn

    async def __call__(self, *args, **kwargs) -> Awaitable[Any]:
        return self._fn(*args, **kwargs)

    @staticmethod
    def wrap(fn: Callable[..., Any]) -> Callable[..., Any] | "_AsyncWrapper":
        return (
            fn
            if inspect.iscoroutinefunction(fn)
            or inspect.iscoroutinefunction(fn.__call__)
            else _AsyncWrapper(fn)
        )

    @staticmethod
    def try_wrap(fn: Any) -> Option[Callable[..., Any] | "_AsyncWrapper"]:
        if isinstance(fn, Callable):
            return Some(_AsyncWrapper.wrap(fn))
        else:
            return Nothing()


class JsonRpcMethodWrapper:
    """Wraps a callable as a JSON-RPC method with optional validation and conversion.

    Attributes:
        name: The JSON-RPC method name this wrapper is registered under.
    """

    def __init__(
        self,
        *,
        name: str,
        method: Callable[..., Any],
        validator: ValidatorType | None = None,
        converter: ConverterType | None = None,
    ):
        """Initialise the wrapper.

        Args:
            name: The JSON-RPC method name.
            method: The callable to invoke when this method is dispatched.
            validator: An optional callable that receives the parsed
                ``params`` and returns ``Some(error)`` to reject, ``False``
                to reject with a generic error, an :class:`Exception` /
                :class:`JsonRpcError` to reject, or any truthy / ``None``
                value to accept.
            converter: An optional callable that transforms the parsed
                ``params`` before the method is invoked.  It may return an
                ``Option`` (``Some`` value used as-is, ``Nothing``
                rejected), a ``Result`` (``Ok`` value used as-is, ``Err``
                rejected), or any other value used directly.  Failures
                become :attr:`JsonRpcErrorCode.ConversionError`.
        """
        self._name = name
        self._method = _AsyncWrapper.wrap(method)
        self._validator: ValidatorType = validator
        self._converter = converter

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
    def _handle_invalid_params_error(
        cls, error: JsonRpcError | Exception
    ) -> JsonRpcError:
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

    def _convert(self, params: Any) -> Result[Any, JsonRpcError]:
        """Run the optional converter over the raw parameters.

        Args:
            params: The raw ``params`` payload.

        Returns:
            ``Ok(converted)`` when conversion succeeded (or no converter is
            set), otherwise ``Err(JsonRpcError)`` with
            :attr:`JsonRpcErrorCode.ConversionError`.
        """
        if isinstance(self._converter, Callable):
            try:
                converted_args = self._converter(params)
                if isinstance(converted_args, Option):
                    return (
                        Ok(converted_args.unwrap())
                        if converted_args.is_some()
                        else Err(JsonRpcErrorCode.ConversionError.into())
                    )
                elif isinstance(converted_args, Result):
                    if converted_args.is_ok():
                        return Ok(converted_args.unwrap())
                    else:
                        err = JsonRpcErrorCode.ConversionError.into()
                        err.data = converted_args.unwrap_err()
                        return Err(err)
                else:
                    return Ok(converted_args)
            except Exception as exc:
                err = JsonRpcErrorCode.ConversionError.into()
                err.data = exc
                return Err(err)
        else:
            return Ok(params)

    def _validate(self, params: Any) -> Option[JsonRpcError]:
        """Run the optional validator over the raw parameters.

        Args:
            params: The raw ``params`` payload.

        Returns:
            ``Some(JsonRpcError)`` if the validator rejected the parameters
            or raised, otherwise ``Nothing``.
        """
        if isinstance(self._validator, Callable):
            try:
                maybe_error = self._validator(params)
                if isinstance(maybe_error, Option) and maybe_error.is_some():
                    return Some(self._handle_invalid_params_error(maybe_error.unwrap()))
                elif isinstance(maybe_error, bool) and not maybe_error:
                    return Some(JsonRpcErrorCode.InvalidParams.into())
                elif isinstance(maybe_error, Exception) or isinstance(
                    maybe_error, JsonRpcError
                ):
                    return Some(JsonRpcError.from_error(maybe_error))
            except Exception as err:
                return Some(JsonRpcError.from_error(err))
        return Nothing()

    async def __call__(self, params: Option[Any]) -> Result[Any, JsonRpcError]:
        """Execute the wrapped method with optional parameters.

        Validation runs first, then conversion; if either step rejects the
        parameters the call short-circuits with an ``Err``.

        Args:
            params: An ``Option`` containing the method parameters.  ``Some``
                means parameters were provided; ``Nothing`` means none.

        Returns:
            ``Ok(result)`` on success, or ``Err(JsonRpcError)`` on failure.
        """
        if params.is_some():
            params = params.unwrap()
            maybe_err = self._validate(params)
            if maybe_err.is_some():
                return Err(maybe_err.unwrap())

            res = self._convert(params)
            if res.is_err():
                return res
            else:
                params = res.unwrap()

            return await self._call_with_params(params)
        else:
            return await self._call_without_params()

    async def _call_without_params(self) -> Result[Any, JsonRpcError]:
        """Invoke the wrapped method with no arguments.

        Returns:
            ``Ok(result)`` on success, or ``Err(JsonRpcError)`` on failure.
        """
        try:
            res = Ok(await self._method()).flatten()
            if res.is_err() and not isinstance(res.unwrap_err(), JsonRpcError):
                res = Err(JsonRpcErrorCode.ExecutionError.into(res.unwrap_err()))
            return res
        except Exception as e:
            err = (
                e
                if isinstance(e, JsonRpcError)
                else JsonRpcErrorCode.ExecutionError.into(e)
            )
            return Err(err)

    async def _call_with_params(self, params: Any) -> Result[Any, JsonRpcError]:
        """Invoke the wrapped method with the converted parameters.

        Args:
            params: The converted parameters passed to the method.

        Returns:
            ``Ok(result)`` on success, or ``Err(JsonRpcError)`` on failure.
        """
        try:
            res = Ok(await self._method(params)).flatten()
            if res.is_err() and not isinstance(res.unwrap_err(), JsonRpcError):
                res = Err(JsonRpcErrorCode.ExecutionError.into(res.unwrap_err()))
            return res
        except Exception as e:
            err = (
                e
                if isinstance(e, JsonRpcError)
                else JsonRpcErrorCode.ExecutionError.into(e)
            )
            return Err(err)


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


class JsonRpcResponseCtorWrapper:
    """Binds a custom :class:`JsonRpcResponse` constructor to a method name.

    The wrapper records *when* the constructor applies — successful
    results, errors, or both — so the dispatcher can pick the right
    response type per outcome.
    """

    class State(Enum):
        """Outcome selector controlling when a constructor is applied."""

        Result = 1
        """The constructor handles successful results."""

        Error = 2
        """The constructor handles error responses."""

        def is_error(self) -> bool:
            """Return whether this state selects error responses."""
            return self == JsonRpcResponseCtorWrapper.State.Error

        def is_result(self) -> bool:
            """Return whether this state selects successful results."""
            return self == JsonRpcResponseCtorWrapper.State.Result

        def __int__(self) -> int:
            """Return the bitmask code of this state."""
            return self.value

    class _When:
        """A bitmask combination of :class:`State` values.

        Use the factory methods :meth:`for_result`, :meth:`for_error`, and
        :meth:`for_both_cases` instead of instantiating directly.
        """

        def __init__(self, *states):
            """Combine *states* into a single bitmask.

            Args:
                *states: :class:`State` members to combine.
            """
            code = 0
            for state in states:
                code |= int(state)
            self._code = code

        def __hash__(self) -> int:
            """Return a hash based on the underlying bitmask."""
            return hash(self._code)

        def __eq__(
            self,
            other: "JsonRpcResponseCtorWrapper._When | JsonRpcResponseCtorWrapper.State",
        ) -> bool:
            """Compare against another ``When``, or test ``State`` membership."""
            if isinstance(other, JsonRpcResponseCtorWrapper.State):
                return (self._code & int(other)) != 0
            else:
                return self._code == other._code

        def __int__(self) -> int:
            """Return the underlying bitmask."""
            return self._code

        def __str__(self) -> str:
            """Return a human-readable description of the selected outcomes."""
            if self._code == int(JsonRpcResponseCtorWrapper.State.Result):
                return "for result"
            elif self._code == int(JsonRpcResponseCtorWrapper.State.Error):
                return "for error"
            else:
                return "for both cases"

        def __repr__(self) -> str:
            """Return the same text as :meth:`__str__`."""
            return str(self)

        @staticmethod
        def for_result() -> "JsonRpcResponseCtorWrapper._When":
            """Return a selector matching only successful results."""
            return JsonRpcResponseCtorWrapper._When(
                JsonRpcResponseCtorWrapper.State.Result
            )

        @staticmethod
        def for_error() -> "JsonRpcResponseCtorWrapper._When":
            """Return a selector matching only error responses."""
            return JsonRpcResponseCtorWrapper._When(
                JsonRpcResponseCtorWrapper.State.Error
            )

        @staticmethod
        def for_both_cases() -> "JsonRpcResponseCtorWrapper._When":
            """Return a selector matching both outcomes."""
            return JsonRpcResponseCtorWrapper._When(
                JsonRpcResponseCtorWrapper.State.Result,
                JsonRpcResponseCtorWrapper.State.Error,
            )

    def __init__(self, method: str, ctor: Callable[..., JsonRpcResponse], *states):
        """Bind *ctor* to *method*, restricted to the given outcome states.

        Args:
            method: The JSON-RPC method name this constructor applies to.
            ctor: Callable receiving keyword arguments (``id``, ``result``
                or ``error``, and ``jsonrpc``) and returning a
                :class:`JsonRpcResponse`.
            *states: Optional :class:`State` members limiting when *ctor*
                is used; defaults to both outcomes.
        """
        self._method = method
        self._when = (
            JsonRpcResponseCtorWrapper._When.for_both_cases()
            if len(states) == 0
            else JsonRpcResponseCtorWrapper._When(*states)
        )
        self._ctor = ctor

    @property
    def method(self) -> str:
        """Return the JSON-RPC method name this constructor is bound to."""
        return self._method

    @property
    def when(self) -> _When:
        """Return the outcome selector for this constructor."""
        return self._when

    def __call__(self, **kwargs):
        """Build a response via the wrapped constructor."""
        return self._ctor(**kwargs)


class JsonRpcDispatcher:
    """Routes incoming JSON-RPC messages to registered handlers.

    Maintains separate registries for requests (which expect a response) and
    notifications (fire-and-forget).
    """

    # Outcome selectors for custom response constructors registered via
    # emplace_custom_response_ctor() / add_custom_response_ctor().
    ERROR_CASE = JsonRpcResponseCtorWrapper.State.Error
    RESULT_CASE = JsonRpcResponseCtorWrapper.State.Result
    BOTH_CASES = JsonRpcResponseCtorWrapper._When.for_both_cases()

    def __init__(
        self, response_handler: Callable[[JsonRpcResponse], None] | None = None
    ):
        """Initialise the dispatcher with empty handler registries."""
        self._request_handler_registry = JsonRpcHandlerCollection()
        self._notification_handler_registry = JsonRpcHandlerCollection()
        self._registry: dict[
            str, tuple[JsonRpcResponseCtorWrapper._When, JsonRpcResponseCtorWrapper]
        ] = {}
        self._response_handler_collection: list[
            Callable[[JsonRpcResponse], None] | Callable[[Any], None]
        ] = []
        if isinstance(response_handler, Callable):
            self._response_handler_collection.append(
                _AsyncWrapper.wrap(response_handler)
            )

    def emplace_custom_response_ctor(
        self, method: str, ctor: Callable[..., JsonRpcResponse], *states
    ):
        """Register a custom response constructor for *method*.

        Convenience overload of :meth:`add_custom_response_ctor` taking
        the constructor parts individually.

        Args:
            method: The JSON-RPC method name the constructor applies to.
            ctor: Callable building a :class:`JsonRpcResponse`.
            *states: Optional :class:`JsonRpcResponseCtorWrapper.State`
                members restricting when *ctor* is used.
        """
        return self.add_custom_response_ctor(
            JsonRpcResponseCtorWrapper(method, ctor, *states)
        )

    def add_custom_response_ctor(self, ctor: JsonRpcResponseCtorWrapper):
        """Register a pre-built custom response constructor.

        Replaces any constructor previously registered for the same method.

        Args:
            ctor: The wrapper binding a constructor to a method name.
        """
        self._registry[ctor.method] = (ctor.when, ctor)

    @property
    def request_handler_registry(self) -> JsonRpcHandlerCollection:
        """Return the registry for request handlers."""
        return self._request_handler_registry

    @property
    def notification_handler_registry(self) -> JsonRpcHandlerCollection:
        """Return the registry for notification handlers."""
        return self._notification_handler_registry

    def emplace_request_handler(
        self,
        *,
        name: str,
        method: Callable[..., Any],
        validator: ValidatorType | None = None,
        converter: ConverterType | None = None,
    ) -> bool:
        """Register a request handler in one call.

        Convenience for
        ``request_handler_registry.add(JsonRpcMethodWrapper(...))``.

        Args:
            name: The JSON-RPC method name.
            method: The callable to invoke when dispatched.
            validator: Optional parameter validator (see
                :class:`JsonRpcMethodWrapper`).
            converter: Optional parameter converter (see
                :class:`JsonRpcMethodWrapper`).

        Returns:
            ``True`` if newly registered, ``False`` if the name already exists.
        """
        return self._request_handler_registry.add(
            JsonRpcMethodWrapper(
                name=name, method=method, validator=validator, converter=converter
            )
        )

    def emplace_notification_handler(
        self,
        *,
        name: str,
        method: Callable[..., Any],
        validator: ValidatorType | None = None,
        converter: ConverterType | None = None,
    ) -> bool:
        """Register a notification handler in one call.

        Convenience for
        ``notification_handler_registry.add(JsonRpcMethodWrapper(...))``.

        Args:
            name: The JSON-RPC method name.
            method: The callable to invoke when dispatched.
            validator: Optional parameter validator (see
                :class:`JsonRpcMethodWrapper`).
            converter: Optional parameter converter (see
                :class:`JsonRpcMethodWrapper`).

        Returns:
            ``True`` if newly registered, ``False`` if the name already exists.
        """
        return self._notification_handler_registry.add(
            JsonRpcMethodWrapper(
                name=name, method=method, validator=validator, converter=converter
            )
        )

    def request(
        self,
        *,
        method: str | None = None,
        validator: ValidatorType | None = None,
        converter: ConverterType | None = None,
    ) -> Callable[Callable[[JsonRpcRequest], Any]]:
        def decorator(
            fn: Callable[[JsonRpcRequest], Any],
        ) -> Callable[[JsonRpcRequest], Any]:
            name = fn.__name__ if method is None else method
            self.emplace_request_handler(
                name=name, method=fn, validator=validator, converter=converter
            )
            # def wrapper(*args, **kwarg):
            #    return fn(*args, **kwarg)
            return fn

        return decorator

    def notification(
        self,
        *,
        method: str | None = None,
        validator: ValidatorType | None = None,
        converter: ConverterType | None = None,
    ) -> Callable[Callable[JsonRpcNotification], None]:
        def decorator(
            fn: Callable[[JsonRpcNotification], None],
        ) -> Callable[[JsonRpcNotification], None]:
            name = fn.__name__ if method is None else method
            self.emplace_notification_handler(
                name=name, method=fn, validator=validator, converter=converter
            )
            # def wrapper(*args, **kwarg):
            #    return fn(*args, **kwarg)
            return fn

        return decorator

    def response(
        self,
        *,
        converter: Callable[[JsonRpcResponse], Any] | None = None,
    ):
        def decorator(fn: Callable[[JsonRpcResponse | Any], None]):
            fn_wrapper = _AsyncWrapper(fn)

            async def wrapper(message: JsonRpcResponse):
                arg = converter(message) if isinstance(converter, Callable) else message
                await fn_wrapper(arg)

            self._response_handler_collection.append(fn_wrapper)

            return wrapper

        return decorator

    async def __call__(
        self,
        data: str
        | JsonRpcRequest
        | JsonRpcNotification
        | JsonRpcResponse
        | Result[JsonRpcRequest | JsonRpcNotification | JsonRpcResponse, JsonRpcError],
    ) -> Option[Result[JsonRpcResponse, JsonRpcError]]:
        """Dispatch a JSON-RPC message.

        Args:
            data: A JSON string, :class:`JsonRpcRequest`, or
                :class:`JsonRpcNotification`, or :class:`JsonRpcResponse`, or
                :class:`Result[JsonRpcRequest | JsonRpcNotification | JsonRpcResponse, JsonRpcError]`.

        Returns:
            ``Some(Ok(response))`` or ``Some(Err(error))`` for requests,
            ``Some(Err(error))`` when a notification handler is missing,
            or ``Nothing`` when a notification is handled successfully
            (no response expected).
        """
        if isinstance(data, str):
            res = self.try_parse(data)
            if res.is_ok():
                return await self(res.unwrap())
            else:
                return Some(Err(JsonRpcErrorCode.ParseError.into()))
        elif isinstance(data, JsonRpcNotification):
            return (await self._handle_notification(data)).map(lambda err: Err(err))
        elif isinstance(data, JsonRpcRequest):
            return Some(Ok(await self._handle_request(data)))
        elif isinstance(data, JsonRpcResponse):
            await self._handle_response(data)
            return Nothing()
        elif isinstance(data, Result):
            if data.is_ok():
                return await self(data.flatten().unwrap())
            else:
                return Some(JsonRpcError.from_error(data.unwrap_err()))
        else:
            return Some(Err(JsonRpcErrorCode.InternalError.into()))

    async def _handle_notification(
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
        await method(self._extract_params(notification))
        return Nothing()

    async def _handle_request(self, request: JsonRpcRequest) -> JsonRpcResponse:
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
        ret_value = await method(self._extract_params(request))
        return self._make_jrpc_response(request, ret_value)

    async def _handle_response(self, response: JsonRpcResponse):
        for fn in self._response_handler_collection:
            await fn(response)

    def _make_jrpc_response(
        self, request: JsonRpcRequest, result: Result[Any, JsonRpcError]
    ) -> JsonRpcResponse:
        """Build a response using a custom constructor when one applies.

        Looks up a constructor registered for the request's method and uses
        it when its outcome selector matches; otherwise falls back to
        :meth:`JsonRpcRequest.into`.

        Args:
            request: The incoming request.
            result: The handler's outcome.

        Returns:
            A :class:`JsonRpcResponse` carrying the result or the error.
        """
        record = self._registry.get(request.method)
        if record is not None:
            when, ctor = record

            if result.is_ok() and (
                when == JsonRpcDispatcher.RESULT_CASE
                or when == JsonRpcDispatcher.BOTH_CASES
            ):
                return ctor(
                    id=request.id, result=result.unwrap(), jsonrpc=request.jsonrpc
                )
            elif result.is_err() and (
                when == JsonRpcDispatcher.ERROR_CASE
                or when == JsonRpcDispatcher.BOTH_CASES
            ):
                return ctor(
                    id=request.id,
                    error=JsonRpcError.from_error(result.unwrap_err()),
                    jsonrpc=request.jsonrpc,
                )
        return request.into(result)

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
    ) -> Result[JsonRpcResponse | JsonRpcNotification | JsonRpcRequest, JsonRpcError]:
        """Attempt to parse a JSON string as a JSON-RPC message.

        The function first tries to parse as a :class:`JsonRpcResponse`; if that
        fails it falls back to :class:`JsonRpcNotification`; if that
        fails it falls back to :class:`JsonRpcRequest`.  If all of them fail, the
        parse error from the request attempt is returned.

        Args:
            data: A JSON-encoded string.

        Returns:
            ``Ok(request | notification | response)`` on success, or ``Err(JsonRpcError)``
            containing the parse failure.
        """
        return try_parse(data)
