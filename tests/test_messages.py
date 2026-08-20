# SPDX-FileCopyrightText: 2026-present comet11x <comet11x@protonmail.com>
#
# SPDX-License-Identifier: MIT
"""Unit tests for jrpc_core.messages module."""

from __future__ import annotations

import json

import pytest
from pyfplib import Nothing, Option, Result, Some

from jrpc_core.messages import (
    JsonRpcError,
    JsonRpcErrorCode,
    JsonRpcNotification,
    JsonRpcRequest,
    JsonRpcResponse,
    JsonRpcVersion,
    try_parse,
)


# ---------------------------------------------------------------------------
# JsonRpcErrorCode
# ---------------------------------------------------------------------------


class TestJsonRpcErrorCode:
    def test_member_values(self):
        assert JsonRpcErrorCode.ParseError.value == -32700
        assert JsonRpcErrorCode.InternalError.value == -32603
        assert JsonRpcErrorCode.InvalidParams.value == -32602
        assert JsonRpcErrorCode.MethodNotFound.value == -32601
        assert JsonRpcErrorCode.InvalidRequest.value == -32600
        assert JsonRpcErrorCode.ExecutionError.value == -32000

    def test_int_conversion(self):
        assert int(JsonRpcErrorCode.ParseError) == -32700

    def test_description(self):
        assert JsonRpcErrorCode.ParseError.description() == "Parse error"
        assert JsonRpcErrorCode.InternalError.description() == "Internal error"
        assert JsonRpcErrorCode.InvalidParams.description() == "Invalid params"
        assert JsonRpcErrorCode.MethodNotFound.description() == "Method not found"
        assert JsonRpcErrorCode.InvalidRequest.description() == "Invalid Request"
        assert JsonRpcErrorCode.ExecutionError.description() == "Execution error"

    def test_default(self):
        assert JsonRpcErrorCode.default() is JsonRpcErrorCode.InternalError

    def test_into(self):
        err = JsonRpcErrorCode.ParseError.into()
        assert isinstance(err, JsonRpcError)
        assert err.code is JsonRpcErrorCode.ParseError
        assert err.message == "Parse error"
        assert err.data is None

    def test_into_with_data(self):
        err = JsonRpcErrorCode.InternalError.into(data={"detail": "oops"})
        assert err.data == {"detail": "oops"}


# ---------------------------------------------------------------------------
# JsonRpcVersion
# ---------------------------------------------------------------------------


class TestJsonRpcVersion:
    def test_values(self):
        assert JsonRpcVersion.Version1 == "1.0"
        assert JsonRpcVersion.Version2 == "2.0"


# ---------------------------------------------------------------------------
# JsonRpcError
# ---------------------------------------------------------------------------


class TestJsonRpcError:
    def test_default(self):
        err = JsonRpcError.default()
        assert err.code is JsonRpcErrorCode.InternalError
        assert err.message == "Something went wrong"
        assert err.data is None

    def test_from_error_already_jrpc(self):
        original = JsonRpcError(code=JsonRpcErrorCode.ParseError, message="bad")
        returned = JsonRpcError.from_error(original)
        assert returned is original

    def test_from_error_obj_with_code(self):
        class FakeError:
            code = -32600

        returned = JsonRpcError.from_error(FakeError())
        assert returned.code == -32600

    def test_from_error_plain_object(self):
        returned = JsonRpcError.from_error("something broke")
        assert returned.code is JsonRpcErrorCode.InternalError
        assert returned.data == "something broke"

    def test_try_from_some(self):
        opt = JsonRpcError.try_from(Some(JsonRpcError(code=JsonRpcErrorCode.InvalidParams)))
        assert opt.is_some()
        assert opt.unwrap().code is JsonRpcErrorCode.InvalidParams

    def test_try_from_nothing(self):
        opt: Option[JsonRpcError] = JsonRpcError.try_from(Nothing())
        assert not opt.is_some()


# ---------------------------------------------------------------------------
# JsonRpcRequest
# ---------------------------------------------------------------------------


class TestJsonRpcRequest:
    def test_minimal(self):
        req = JsonRpcRequest(method="foo")
        assert req.method == "foo"
        assert req.jsonrpc == JsonRpcVersion.Version2
        assert isinstance(req.id, str)
        assert req.params is None

    def test_method_empty_rejected(self):
        with pytest.raises(Exception):
            JsonRpcRequest(method="")

    def test_method_non_string_rejected(self):
        with pytest.raises(Exception):
            JsonRpcRequest(method=123)

    def test_try_from_dict_ok(self):
        result = JsonRpcRequest.try_from_dict({"method": "bar", "id": 1})
        assert result.is_ok()
        req = result.unwrap()
        assert req.method == "bar"
        assert req.id == 1

    def test_try_from_dict_err(self):
        result = JsonRpcRequest.try_from_dict({"method": ""})
        assert result.is_err()

    def test_try_from_json_ok(self):
        result = JsonRpcRequest.try_from_json('{"method": "baz", "id": "abc"}')
        assert result.is_ok()
        assert result.unwrap().method == "baz"

    def test_try_from_json_err(self):
        result = JsonRpcRequest.try_from_json('{"method": ""}')
        assert result.is_err()

    def test_to_dict_omits_params_when_none(self):
        req = JsonRpcRequest(method="m")
        d = req.to_dict()
        assert "params" not in d
        assert d["method"] == "m"
        assert d["jsonrpc"] == "2.0"
        assert "id" in d

    def test_to_dict_includes_params(self):
        req = JsonRpcRequest(method="m", params={"x": 1})
        d = req.to_dict()
        assert d["params"] == {"x": 1}

    def test_to_json_roundtrip(self):
        req = JsonRpcRequest(method="m", params=[1, 2], id=42)
        raw = req.to_json()
        parsed = json.loads(raw)
        assert parsed["method"] == "m"
        assert parsed["params"] == [1, 2]
        assert parsed["id"] == 42

    def test_into_with_result_ok(self):
        req = JsonRpcRequest(method="m", id=10)
        resp = req.into(Result(value="hello"))
        assert isinstance(resp, JsonRpcResponse)
        assert resp.id == 10
        assert resp.result == "hello"
        assert resp.error is None

    def test_into_with_result_err(self):
        req = JsonRpcRequest(method="m", id=10)
        jerr = JsonRpcError(code=JsonRpcErrorCode.MethodNotFound, message="nope")
        resp = req.into(Result(error=jerr))
        assert resp.error is not None
        assert resp.error.code is JsonRpcErrorCode.MethodNotFound
        assert resp.result is None

    def test_into_with_jrpc_error(self):
        req = JsonRpcRequest(method="m", id=5)
        jerr = JsonRpcError(code=JsonRpcErrorCode.InvalidRequest)
        resp = req.into(jerr)
        assert resp.id == 5
        assert resp.error is jerr

    def test_into_with_raw_value(self):
        req = JsonRpcRequest(method="m", id=7)
        resp = req.into(42)
        assert resp.result == 42
        assert resp.error is None


# ---------------------------------------------------------------------------
# JsonRpcNotification
# ---------------------------------------------------------------------------


class TestJsonRpcNotification:
    def test_minimal(self):
        n = JsonRpcNotification(method="evt")
        assert n.method == "evt"
        assert n.params is None
        assert n.jsonrpc == JsonRpcVersion.Version2

    def test_rejects_id(self):
        with pytest.raises(Exception):
            JsonRpcNotification(method="evt", id="bad")  # type: ignore[arg-type]

    def test_method_empty_rejected(self):
        with pytest.raises(Exception):
            JsonRpcNotification(method="")

    def test_try_from_dict_ok(self):
        result = JsonRpcNotification.try_from_dict({"method": "evt", "params": [1]})
        assert result.is_ok()
        n = result.unwrap()
        assert n.method == "evt"
        assert n.params == [1]

    def test_try_from_dict_rejects_id(self):
        result = JsonRpcNotification.try_from_dict({"method": "evt", "id": 1})
        assert result.is_err()

    def test_try_from_json_ok(self):
        result = JsonRpcNotification.try_from_json('{"method": "evt"}')
        assert result.is_ok()

    def test_to_dict_omits_params_when_none(self):
        n = JsonRpcNotification(method="evt")
        d = n.to_dict()
        assert "params" not in d
        assert "id" not in d

    def test_to_json_roundtrip(self):
        n = JsonRpcNotification(method="evt", params={"a": 1})
        raw = n.to_json()
        parsed = json.loads(raw)
        assert parsed["method"] == "evt"
        assert parsed["params"] == {"a": 1}
        assert "id" not in parsed


# ---------------------------------------------------------------------------
# JsonRpcResponse
# ---------------------------------------------------------------------------


class TestJsonRpcResponse:
    def test_from_result_ok(self):
        resp = JsonRpcResponse.from_result(1, Result(value="data"))
        assert resp.id == 1
        assert resp.result == "data"
        assert resp.error is None

    def test_from_result_err(self):
        jerr = JsonRpcError(code=JsonRpcErrorCode.InternalError, message="fail")
        resp = JsonRpcResponse.from_result(2, Result(error=jerr))
        assert resp.id == 2
        assert resp.error is jerr
        assert resp.result is None

    def test_from_jrpc_error(self):
        jerr = JsonRpcError(code=JsonRpcErrorCode.ParseError)
        resp = JsonRpcResponse.from_jrpc_error(3, jerr)
        assert resp.id == 3
        assert resp.error is jerr

    def test_from_jrpc_result(self):
        resp = JsonRpcResponse.from_jrpc_result(4, [1, 2, 3])
        assert resp.id == 4
        assert resp.result == [1, 2, 3]

    def test_both_result_and_error_rejected(self):
        with pytest.raises(Exception):
            JsonRpcResponse(
                id=1,
                result="ok",
                error=JsonRpcError(code=JsonRpcErrorCode.InternalError),
            )

    def test_try_from_dict_ok(self):
        result = JsonRpcResponse.try_from_dict({"id": 1, "result": "yes"})
        assert result.is_ok()
        assert result.unwrap().result == "yes"

    def test_try_from_dict_err(self):
        result = JsonRpcResponse.try_from_dict({"nope": True})
        assert result.is_err()

    def test_try_from_json_ok(self):
        result = JsonRpcResponse.try_from_json('{"id": 1, "result": 42}')
        assert result.is_ok()
        assert result.unwrap().result == 42

    def test_to_dict_success(self):
        resp = JsonRpcResponse(id=1, result="ok")
        d = resp.to_dict()
        assert d["result"] == "ok"
        assert "error" not in d

    def test_to_dict_error(self):
        resp = JsonRpcResponse(
            id=1, error=JsonRpcError(code=JsonRpcErrorCode.InvalidParams, message="bad")
        )
        d = resp.to_dict()
        assert "result" not in d
        assert d["error"]["code"] == -32602
        assert d["error"]["message"] == "bad"

    def test_to_json_roundtrip(self):
        resp = JsonRpcResponse(id="x", result={"key": "val"})
        raw = resp.to_json()
        parsed = json.loads(raw)
        assert parsed["id"] == "x"
        assert parsed["result"] == {"key": "val"}

    def test_validate_error_raw_dict_coerced(self):
        resp = JsonRpcResponse(id=1, error={"code": -32600, "message": "bad req"})
        assert isinstance(resp.error, JsonRpcError)
        assert resp.error.code == -32600
        assert resp.error.message == "bad req"

    def test_validate_error_raw_dict_defaults_filled(self):
        resp = JsonRpcResponse(id=1, error={"message": "only message"})
        assert resp.error.code is JsonRpcErrorCode.InternalError
        assert resp.error.message == "only message"


# ---------------------------------------------------------------------------
# try_parse
# ---------------------------------------------------------------------------


class TestTryParse:
    def test_parse_request(self):
        raw = json.dumps({"jsonrpc": "2.0", "method": "add", "id": 1, "params": [1, 2]})
        result = try_parse(raw)
        assert result.is_ok()
        msg = result.unwrap()
        assert isinstance(msg, JsonRpcRequest)
        assert msg.method == "add"

    def test_parse_notification(self):
        # NOTE: try_parse always succeeds as JsonRpcRequest because
        # JsonRpcRequest defaults `id` via uuid4(). This means notifications
        # without `id` are parsed as requests, not notifications.
        raw = json.dumps({"jsonrpc": "2.0", "method": "evt"})
        result = try_parse(raw)
        assert result.is_ok()
        msg = result.unwrap()
        assert isinstance(msg, JsonRpcRequest)
        assert msg.method == "evt"
        assert isinstance(msg.id, str)

    def test_parse_invalid(self):
        result = try_parse("not json at all")
        assert result.is_err()

    def test_parse_empty_object(self):
        result = try_parse("{}")
        assert result.is_err()

    def test_parse_invalid_json_syntax(self):
        result = try_parse("{bad")
        assert result.is_err()
