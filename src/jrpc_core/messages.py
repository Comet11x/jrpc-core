# SPDX-FileCopyrightText: 2026-present comet11x <comet11x@protonmail.com>
#
# SPDX-License-Identifier: MIT
"""JSON-RPC 2.0 message primitives: requests, responses, and notifications."""

from __future__ import annotations

import json
from enum import Enum, StrEnum
from typing import Any, cast
from uuid import uuid4

from pydantic import BaseModel, field_validator, model_validator
from pyfplib import Nothing, Option, Result, Some

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

    @staticmethod
    def default() -> JsonRpcErrorCode:
        return JsonRpcErrorCode.InternalError


class JsonRpcVersion(StrEnum):
    Version1 = "1.0"
    Version2 = "2.0"


class JsonRpcError(BaseModel):
    code: JsonRpcErrorCode | int = JsonRpcErrorCode.default()
    message: str = "Something went wrong"
    data: Any | None = None

    @staticmethod
    def default() -> JsonRpcError:
        return JsonRpcError(code=JsonRpcErrorCode.default())

    @staticmethod
    def into(value: JsonRpcError | Any) -> JsonRpcError:
        if isinstance(value, JsonRpcError):
            return value
        else:
            maybe_code: Option[int] = Result.try_call(cast(Any, value), "code").ok()
            code = (
                int(maybe_code.unwrap())
                if maybe_code.is_some()
                else JsonRpcErrorCode.InternalError
            )
            return JsonRpcError(code=code, data=value)

    @staticmethod
    def try_into(value: Option[JsonRpcError | Any]) -> Option[JsonRpcError]:
        return Some(JsonRpcError.into(value.unwrap())) if value.is_some() else Nothing()


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
    def try_from_dict(cls, data: dict[str, Any]) -> Result[JsonRpcRequest, Exception]:
        return Result.try_call(cls.model_validate, data)

    @classmethod
    def try_from_json(cls, data: str) -> Result[JsonRpcRequest, Exception]:
        return Result.try_call(cls.model_validate_json, data)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dict, omitting the optional ``params`` when absent."""
        data = self.model_dump()
        if self.params is None:
            data.pop("params", None)
        return data

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    def into(self, result: Result[Any, JsonRpcError]) -> JsonRpcResponse:
        return JsonRpcResponse.from_result(self.id, result)


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
    def try_from_dict(
        cls, data: dict[str, Any]
    ) -> Result[JsonRpcNotification, Exception]:
        return Result.try_call(cls.model_validate, data)

    @classmethod
    def try_from_json(cls, data: str) -> Result[JsonRpcNotification, Exception]:
        return Result.try_call(cls.model_validate_json, data)

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
        if not isinstance(error, JsonRpcError):
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
    def from_result(
        id: JsonRpcId, result: Result[Any, JsonRpcError]
    ) -> JsonRpcResponse:
        return (
            JsonRpcResponse(id=id, result=result.unwrap())
            if result.is_ok()
            else JsonRpcResponse(id=id, error=result.unwrap_err())
        )

    @staticmethod
    def from_jrpc_error(id: JsonRpcId, error: JsonRpcError) -> JsonRpcResponse:
        return JsonRpcResponse(id=id, error=error)

    @staticmethod
    def from_jrpc_result(id: JsonRpcId, result: Any) -> JsonRpcResponse:
        return JsonRpcResponse(id=id, result=result)

    @staticmethod
    def try_from_dict(data: dict[str, Any]) -> Result[JsonRpcResponse, Exception]:
        return Result.try_call(JsonRpcResponse.model_validate, data)

    @staticmethod
    def try_from_json(data: str) -> Result[JsonRpcResponse, Exception]:
        return Result.try_call(JsonRpcResponse.model_validate_json, data)

    def to_dict(self) -> dict[str, Any]:
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
        return json.dumps(self.to_dict())


def try_parse(data: str) -> Result[JsonRpcRequest | JsonRpcNotification, JsonRpcError]:
    return (
        Result.try_call(JsonRpcRequest.try_from_json, data)
        .map_err(lambda _: Result.try_call(JsonRpcNotification.try_from_json, data))
        .flatten()
    )
