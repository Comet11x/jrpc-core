# SPDX-FileCopyrightText: 2026-present comet11x <comet11x@protonmail.com>
#
# SPDX-License-Identifier: MIT
"""JSON-RPC 2.0 message primitives: requests, responses, and notifications."""

from __future__ import annotations

from typing import Any
from uuid import uuid4
import json
from pydantic import BaseModel, field_validator, model_validator
from pyfplib import Err, Ok, Result
from enum import Enum, StrEnum

JsonRpcId = str | int | float | None
JsonRpcParams = dict[str, Any] | list[Any] | None


class JsonRpcErrorCode(Enum):
    ParseError = -32700
    InvalidRequest = -32600
    MethodNotFound = -32601
    InvalidParams = -32602
    InternalError = -32603

    def __int__(self):
        return self.value


class JsonRpcVersion(StrEnum):
    Version1 = "1.0"
    Version2 = "2.0"


class JsonRpcError(BaseModel):
    code: JsonRpcErrorCode | int = JsonRpcErrorCode.InternalError
    message: str = "Something went wrong"
    data: Any | None = None


class JsonRpcRequest(BaseModel):
    """A JSON-RPC 2.0 request: ``{"jsonrpc": "2.0", "method": ..., "params": ..., "id": ...}``."""

    method: str
    id: JsonRpcId = str(uuid4())
    params: JsonRpcParams = None
    jsonrpc: JsonRpcVersion = JsonRpcVersion.Version2

    @field_validator("method", mode="before")
    @classmethod
    def _validate_method(cls, value: Any) -> Any:
        if not isinstance(value, str) or not value:
            raise ValueError("method must be a non-empty string")
        return value

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Result[JsonRpcRequest, Exception]:
        """Parse a request from a dict, returning a ``Result`` instead of raising."""
        try:
            return Ok(cls.model_validate(data))
        except Exception as exc:
            return Err(exc)

    @classmethod
    def from_json(cls, data: str) -> Result[JsonRpcRequest, Exception]:
        """Parse a request from a JSON string, returning a ``Result`` instead of raising."""
        try:
            return Ok(cls.model_validate_json(data))
        except Exception as exc:
            return Err(exc)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dict, omitting the optional ``params`` when absent."""
        data = self.model_dump()
        if self.params is None:
            data.pop("params", None)
        return data

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    def make_error(self, error: JsonRpcError) -> JsonRpcResponse:
        return JsonRpcResponse(id=self.id, error=error)

    def make_response(self, result: Any) -> JsonRpcResponse:
        return JsonRpcResponse(id=self.id, result=result)


class JsonRpcNotification(BaseModel):
    """A JSON-RPC 2.0 notification: a request without an ``id`` (no response expected)."""

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
    def from_dict(cls, data: dict[str, Any]) -> Result[JsonRpcNotification, Exception]:
        """Parse a notification from a dict, returning a ``Result`` instead of raising."""
        try:
            return Ok(cls.model_validate(data))
        except Exception as exc:
            return Err(exc)

    @classmethod
    def from_json(cls, data: str) -> Result[JsonRpcNotification, Exception]:
        """Parse a notification from a JSON string, returning a ``Result`` instead of raising."""
        try:
            return Ok(cls.model_validate_json(data))
        except Exception as exc:
            return Err(exc)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dict, omitting the optional ``params`` when absent."""
        data = self.model_dump()
        if self.params is None:
            data.pop("params", None)
        return data

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


class JsonRpcResponse(BaseModel):
    """A JSON-RPC 2.0 response: carries exactly one of ``result`` or ``error`` plus an ``id``."""

    id: JsonRpcId
    result: Any = None
    error: JsonRpcError | None = None
    jsonrpc: JsonRpcVersion = JsonRpcVersion.Version2

    @field_validator("error")
    @classmethod
    def _validate_error(cls, error: JsonRpcError) -> JsonRpcError:
        if error is not None:
            if "code" not in error or "message" not in error:
                raise ValueError("error must contain 'code' and 'message'")
            if not isinstance(error.code, int) or not isinstance(error.message, str):
                raise TypeError(
                    "error 'code' must be an int and 'message' must be a str"
                )
        return error

    @model_validator(mode="after")
    def _validate_result_error(self) -> JsonRpcResponse:
        if self.error is not None and self.result is not None:
            raise ValueError(
                "a response must have either a result or an error, not both"
            )
        return self

    @staticmethod
    def from_result(id: JsonRpcId, result: Any) -> JsonRpcResponse:
        """Build a successful response carrying ``result``."""
        return JsonRpcResponse(id=id, result=result)

    @staticmethod
    def from_error(
        req: JsonRpcRequest,
        error: JsonRpcError,
    ) -> JsonRpcResponse:
        """Build an error response from a ``code``, ``message``, and optional ``data``."""
        return JsonRpcResponse(id=id, error=error)

    @staticmethod
    def from_request(req: JsonRpcRequest, response: Any) -> JsonRpcResponse:
        return JsonRpcResponse(id=req.id, response=response)

    @staticmethod
    def from_dict(data: dict[str, Any]) -> Result[JsonRpcResponse, Exception]:
        """Parse a response from a dict, returning a ``Result`` instead of raising."""
        try:
            return Ok(JsonRpcResponse.model_validate(data))
        except Exception as exc:
            return Err(exc)

    @staticmethod
    def from_json(data: str) -> Result[JsonRpcResponse, Exception]:
        """Parse a response from a JSON string, returning a ``Result`` instead of raising."""
        try:
            return Ok(JsonRpcResponse.model_validate_json(data))
        except Exception as exc:
            return Err(exc)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dict, carrying exactly one of ``result`` or ``error``."""
        data = self.model_dump()
        if self.error is not None:
            data.pop("result", None)
        else:
            data.pop("error", None)
        return data

    def to_json(self) -> str:
        return json.dumps(self.to_dict())
