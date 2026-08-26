# SPDX-FileCopyrightText: 2026-present comet11x <comet11x@protonmail.com>
#
# SPDX-License-Identifier: MIT
"""JSON-RPC 2.0 message primitives: requests, responses, and notifications.

This module provides Pydantic models and enumerations for constructing,
validating, and serialising JSON-RPC 2.0 messages as defined in
`the JSON-RPC 2.0 specification <https://www.jsonrpc.org/specification>`_.

Typical usage::

    # Server code
    from jrpc_core import try_parse, JsonRpcRequest, JsonRpcResponse

    def handle_server_data(data: str):
        res = try_parse(data)




    request = JsonRpcRequest(method="add", params=[1, 2])
    data: str = request.to_json()
    // or
    // data: str = request.serialize()
    JsonRpc
    response = request.into(Result.ok(3))
    print(response.to_json())
"""

from __future__ import annotations

import json
from enum import Enum, StrEnum
from typing import Any, cast
from uuid import uuid4

from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from pyfplib import Option, Result

JsonRpcId = str | int | float | None
"""Type alias for a JSON-RPC message identifier.

A valid identifier is a ``str``, ``int``, ``float``, or ``None``.
The ``None`` variant is permitted only in notifications.
"""

JsonRpcParams = dict[str, Any] | list[Any] | None
"""Type alias for JSON-RPC ``params`` values.

Parameters may be a named mapping (``dict``), a positional list (``list``),
or ``None`` when omitted.
"""


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class JsonRpcErrorCode(Enum):
    """Enumeration of standard JSON-RPC 2.0 error codes.

    Each member maps to the integer code defined by the specification or
    common extensions (``-32xxx`` reserved, ``-320xx`` server-defined).
    """

    ParseError = -32700
    """Invalid JSON was received by the server."""

    InternalError = -32603
    """An internal JSON-RPC error occurred."""

    InvalidParams = -32602
    """The parameters sent with the method are invalid."""

    MethodNotFound = -32601
    """The method does not exist or is not available."""

    InvalidRequest = -32600
    """The JSON sent is not a valid request object."""

    ExecutionError = -32000
    """A server-defined execution error occurred."""

    ConversionError = -32001
    """A server-defined conversion error occurred."""

    def __int__(self) -> int:
        """Return the integer value of this error code."""
        return self.value

    def description(self) -> str:
        """Return a human-readable description of this error code.

        Returns:
            A short English sentence describing the error.
        """
        if self == JsonRpcErrorCode.ParseError:
            return "Parse error"
        elif self == JsonRpcErrorCode.InternalError:
            return "Internal error"
        elif self == JsonRpcErrorCode.InvalidParams:
            return "Invalid params"
        elif self == JsonRpcErrorCode.MethodNotFound:
            return "Method not found"
        elif self == JsonRpcErrorCode.InvalidRequest:
            return "Invalid Request"
        elif self == JsonRpcErrorCode.ExecutionError:
            return "Execution error"
        else:
            # ConversionError is the only remaining member.
            return "Data conversion error"

    @staticmethod
    def default() -> JsonRpcErrorCode:
        """Return the default error code used when no other code is appropriate.

        Returns:
            :attr:`InternalError`.
        """
        return JsonRpcErrorCode.InternalError

    def into(self, data: Any = None) -> JsonRpcError:
        """Create a :class:`JsonRpcError` from this code.

        Args:
            data: Optional extra payload attached to the error.

        Returns:
            A new :class:`JsonRpcError` with this code and its description.
        """
        return JsonRpcError(code=self, message=self.description(), data=data)


class JsonRpcVersion(StrEnum):
    """Supported JSON-RPC protocol versions."""

    Version1 = "1.0"
    """JSON-RPC 1.0."""

    Version2 = "2.0"
    """JSON-RPC 2.0 (default)."""


class JsonRpcError(_StrictModel):
    """A JSON-RPC 2.0 error object.

    Attributes:
        code: An integer error code, typically a :class:`JsonRpcErrorCode` member.
        message: A short human-readable description of the error.
        data: Optional extra information about the error.
    """

    code: JsonRpcErrorCode | int = JsonRpcErrorCode.default()
    message: str = "Something went wrong"
    data: Any | None = None

    @staticmethod
    def default() -> JsonRpcError:
        """Return a default error with :attr:`JsonRpcErrorCode.InternalError`.

        Returns:
            A new :class:`JsonRpcError` with the default code and message.
        """
        return JsonRpcError(code=JsonRpcErrorCode.default())

    @staticmethod
    def from_data(
        *,
        data: Any,
        code: JsonRpcErrorCode = JsonRpcErrorCode.InternalError,
        message: str = JsonRpcErrorCode.InternalError.description(),
    ) -> JsonRpcError:
        return JsonRpcError(code=code, message=message, data=data)

    @staticmethod
    def from_error(error: JsonRpcError | Any) -> JsonRpcError:
        """Convert an arbitrary value into a :class:`JsonRpcError`.

        If *error* is already a :class:`JsonRpcError` it is returned as-is.
        Otherwise the function attempts to extract a ``code`` attribute and
        builds an error around it, falling back to
        :attr:`JsonRpcErrorCode.InternalError`.

        Args:
            error: The value to convert.

        Returns:
            A :class:`JsonRpcError` instance.
        """
        if isinstance(error, JsonRpcError):
            return error
        else:
            maybe_code: Option[int | JsonRpcErrorCode] = cast(
                Option[int | JsonRpcErrorCode],
                Result.try_call(getattr, cast(Any, error), "code").ok(),
            )
            maybe_message: Option[str] = Result.try_call(
                getattr, cast(error, Any), "message"
            )
            maybe_data: Option[str] = Result.try_call(getattr, cast(error, Any), "data")
            if maybe_code.is_some() and maybe_message.is_some():
                code = int(maybe_code.unwrap())
                message = maybe_message.unwrap()
                data = maybe_data.unwrap_or(None)
                return JsonRpcError(code=code, message=message, data=data)
            else:
                code = JsonRpcErrorCode.InternalError
                return JsonRpcError(code=code, message=code.description(), data=error)

    @staticmethod
    def try_from(value: Option[JsonRpcError | Any]) -> Option[JsonRpcError]:
        """Attempt to convert an :class:`~pyfplib.option.Option` into an error.

        Args:
            value: An ``Option`` that may contain a value to convert.

        Returns:
            ``Some(JsonRpcError)`` if *value* was ``Some``, otherwise ``Nothing``.
        """
        return value.map(lambda err: JsonRpcError.from_error(err))


class JsonRpcRequest(_StrictModel):
    """A JSON-RPC 2.0 request object.

    A request contains a ``method`` name, an optional ``params`` payload, and
    an ``id`` that the client uses to correlate the response.

    Attributes:
        method: The name of the remote procedure to invoke.
        id: A unique identifier for this request (auto-generated UUID by default).
        params: Optional positional or named arguments for the method.
        jsonrpc: The protocol version, defaults to ``"2.0"``.
    """

    method: str
    id: JsonRpcId = Field(default_factory=lambda: str(uuid4()))
    params: JsonRpcParams = None
    jsonrpc: JsonRpcVersion = JsonRpcVersion.Version2

    @field_validator("method", mode="before")
    @classmethod
    def _validate_method(cls, value: Any) -> Any:
        if not isinstance(value, str) or not value:
            raise ValueError("method must be a non-empty string")
        return value

    @classmethod
    def try_from_dict(cls, data: dict[str, Any]) -> Result[JsonRpcRequest, Exception]:
        """Attempt to build a request from a plain dictionary.

        Args:
            data: A dictionary with JSON-RPC request fields.

        Returns:
            ``Ok(request)`` on success, or ``Err(exception)`` on validation failure.
        """
        return Result.try_call(cls.model_validate, data)

    @classmethod
    def try_from_json(cls, data: str) -> Result[JsonRpcRequest, Exception]:
        """Attempt to build a request from a JSON string.

        Args:
            data: A JSON-encoded string representing a request.

        Returns:
            ``Ok(request)`` on success, or ``Err(exception)`` on parse/validation failure.
        """
        return Result.try_call(cls.model_validate_json, data, strict=True)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the request to a plain dictionary.

        The ``params`` key is omitted when ``None``.

        Returns:
            A dictionary suitable for JSON serialisation.
        """
        data = self.model_dump()
        if self.params is None:
            data.pop("params", None)
        return data

    def to_json(self) -> str:
        """Serialize the request to a JSON string.

        Returns:
            A compact JSON representation of this request.
        """
        return json.dumps(self.to_dict())

    def serialize(self) -> str:
        """Serialize the request to a JSON string.

        Alias for :meth:`to_json`.

        Returns:
            A compact JSON representation of this request.
        """
        return self.to_json()

    def into(self, result: Result[Any, JsonRpcError]) -> JsonRpcResponse:
        """Create a :class:`JsonRpcResponse` from a handler result.

        This is a convenience method for dispatching the result of a method
        handler back as a response.  It accepts a :class:`~pyfplib.result.Result`,
        a :class:`JsonRpcError`, or a raw value.

        Args:
            result: The outcome of processing this request.

        Returns:
            A response carrying either the unwrapped result or the error.
        """
        if isinstance(result, Result):
            return JsonRpcResponse.from_result(self.id, result)
        elif isinstance(result, JsonRpcError):
            return JsonRpcResponse.from_jrpc_error(self.id, result)
        else:
            return JsonRpcResponse.from_jrpc_result(self.id, result)


class JsonRpcNotification(_StrictModel):
    """A JSON-RPC 2.0 notification object.

    A notification is identical to a request but omits the ``id`` field,
    indicating that no response is expected from the server.

    Attributes:
        method: The name of the event or procedure being announced.
        params: Optional positional or named arguments.
        jsonrpc: The protocol version, defaults to ``"2.0"``.
    """

    method: str
    params: JsonRpcParams = None
    jsonrpc: JsonRpcVersion = JsonRpcVersion.Version2

    @field_validator("method", mode="before")
    @classmethod
    def _validate_method(cls, value: Any) -> Any:
        if not isinstance(value, str) or not value:
            raise ValueError("method must be a non-empty string")
        return value

    @model_validator(mode="before")
    @classmethod
    def _reject_id(cls, data: Any) -> Any:
        if isinstance(data, dict) and "id" in data:
            raise ValueError("a notification must not contain an 'id'")
        return data

    @classmethod
    def try_from_dict(
        cls, data: dict[str, Any]
    ) -> Result[JsonRpcNotification, Exception]:
        """Attempt to build a notification from a plain dictionary.

        Args:
            data: A dictionary with JSON-RPC notification fields.

        Returns:
            ``Ok(notification)`` on success, or ``Err(exception)`` on validation failure.
        """
        return Result.try_call(cls.model_validate, data)

    @classmethod
    def try_from_json(cls, data: str) -> Result[JsonRpcNotification, Exception]:
        """Attempt to build a notification from a JSON string.

        Args:
            data: A JSON-encoded string representing a notification.

        Returns:
            ``Ok(notification)`` on success, or ``Err(exception)`` on parse/validation failure.
        """
        return Result.try_call(cls.model_validate_json, data, strict=True)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the notification to a plain dictionary.

        The ``params`` key is omitted when ``None``.

        Returns:
            A dictionary suitable for JSON serialisation.
        """
        data = self.model_dump()
        if self.params is None:
            data.pop("params", None)
        return data

    def to_json(self) -> str:
        """Serialize the notification to a JSON string.

        Returns:
            A compact JSON representation of this notification.
        """
        return json.dumps(self.to_dict())

    def serialize(self) -> str:
        """Serialize the notification to a JSON string.

        Alias for :meth:`to_json`.

        Returns:
            A compact JSON representation of this notification.
        """
        return self.to_json()


class JsonRpcResponse(_StrictModel):
    """A JSON-RPC 2.0 response object.

    Exactly one of ``result`` or ``error`` must be set.  The ``id`` matches
    the ``id`` of the originating request.

    Attributes:
        id: The identifier of the request this response corresponds to.
        result: The return value when the method executed successfully.
        error: A :class:`JsonRpcError` when the method failed.
        jsonrpc: The protocol version, defaults to ``"2.0"``.
    """

    id: JsonRpcId
    result: Any = None
    error: JsonRpcError | None = None
    jsonrpc: JsonRpcVersion = JsonRpcVersion.Version2

    @field_validator("error")
    @classmethod
    def _validate_error(cls, error: JsonRpcError) -> JsonRpcError:
        return error

    @model_validator(mode="after")
    def _validate_result_error(self) -> JsonRpcResponse:
        if self.error is not None and self.result is not None:
            raise ValueError(
                "a response must have either a result or an error, not both"
            )
        return self

    @staticmethod
    def from_result(
        id: JsonRpcId, result: Result[Any, JsonRpcError]
    ) -> JsonRpcResponse:
        """Build a response from a :class:`~pyfplib.result.Result`.

        If *result* is ``Ok`` the unwrapped value becomes ``result``; if it
        is ``Err`` the unwrapped error becomes ``error``.

        Args:
            id: The request identifier to echo back.
            result: The handler's outcome.

        Returns:
            A fully constructed :class:`JsonRpcResponse`.
        """
        return (
            JsonRpcResponse(id=id, result=result.unwrap())
            if result.is_ok()
            else JsonRpcResponse(id=id, error=result.unwrap_err())
        )

    @staticmethod
    def from_jrpc_error(
        id: JsonRpcId, error: JsonRpcError | Exception
    ) -> JsonRpcResponse:
        """Build an error response.

        Args:
            id: The request identifier to echo back.
            error: The error to include.

        Returns:
            A :class:`JsonRpcResponse` with only ``error`` set.
        """
        return JsonRpcResponse(id=id, error=JsonRpcError.from_error(error))

    @staticmethod
    def from_jrpc_result(id: JsonRpcId, result: Any) -> JsonRpcResponse:
        """Build a successful response.

        Args:
            id: The request identifier to echo back.
            result: The return value of the method.

        Returns:
            A :class:`JsonRpcResponse` with only ``result`` set.
        """
        return JsonRpcResponse(id=id, result=result)

    @staticmethod
    def try_from_dict(data: dict[str, Any]) -> Result[JsonRpcResponse, Exception]:
        """Attempt to build a response from a plain dictionary.

        Args:
            data: A dictionary with JSON-RPC response fields.

        Returns:
            ``Ok(response)`` on success, or ``Err(exception)`` on validation failure.
        """
        return Result.try_call(JsonRpcResponse.model_validate, data)

    @staticmethod
    def try_from_json(data: str) -> Result[JsonRpcResponse, Exception]:
        """Attempt to build a response from a JSON string.

        Args:
            data: A JSON-encoded string representing a response.

        Returns:
            ``Ok(response)`` on success, or ``Err(exception)`` on parse/validation failure.
        """
        return Result.try_call(JsonRpcResponse.model_validate_json, data, strict=True)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the response to a plain dictionary.

        When an ``error`` is present the ``result`` key is removed and the
        error code is coerced to ``int``.  When ``result`` is present the
        ``error`` key is removed.

        Returns:
            A dictionary suitable for JSON serialisation.
        """
        data = self.model_dump()
        if self.error is not None:
            data.pop("result", None)
            data["error"]["code"] = int(
                data["error"].get("code", JsonRpcErrorCode.default())
            )
        else:
            data.pop("error", None)
        return data

    def to_json(self) -> str:
        """Serialize the response to a JSON string.

        Returns:
            A compact JSON representation of this response.
        """
        return json.dumps(self.to_dict())

    def serialize(self) -> str:
        """Serialize the response to a JSON string.

        Alias for :meth:`to_json`.

        Returns:
            A compact JSON representation of this response.
        """
        return self.to_json()


def try_parse(
    data: str,
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
    return (
        JsonRpcResponse.try_from_json(data)
        .map_err(lambda _: JsonRpcNotification.try_from_json(data))
        .flatten()
        .map_err(lambda _: JsonRpcRequest.try_from_json(data))
        .flatten()
    )
