# SPDX-FileCopyrightText: 2026-present comet11x <comet11x@protonmail.com>
#
# SPDX-License-Identifier: MIT
"""Unit tests for jrpc_core.dispatcher module."""

from __future__ import annotations

import json

import pytest
from pyfplib import Err, Nothing, Ok, Option, Result, Some

from jrpc_core.dispatcher import (
    JsonRpcDispatcher,
    JsonRpcHandlerCollection,
    JsonRpcMethodWrapper,
)
from jrpc_core.messages import (
    JsonRpcError,
    JsonRpcErrorCode,
    JsonRpcNotification,
    JsonRpcRequest,
    JsonRpcResponse,
)


# ---------------------------------------------------------------------------
# JsonRpcMethodWrapper
# ---------------------------------------------------------------------------


class TestJsonRpcMethodWrapper:
    def test_init_without_validators(self):
        w = JsonRpcMethodWrapper(name="m", method=lambda x: x)
        assert w.name == "m"
        assert w._validators == []

    def test_init_with_validators(self):
        v = lambda args: True
        w = JsonRpcMethodWrapper(name="m", method=lambda x: x, validators=[v])
        assert w._validators == [v]

    def test_name_property(self):
        w = JsonRpcMethodWrapper(name="hello", method=lambda: None)
        assert w.name == "hello"

    def test_hash(self):
        w = JsonRpcMethodWrapper(name="m", method=lambda: None)
        assert hash(w) == hash("m")

    def test_eq_same_name(self):
        a = JsonRpcMethodWrapper(name="m", method=lambda: 1)
        b = JsonRpcMethodWrapper(name="m", method=lambda: 2)
        assert a == b

    def test_eq_different_name(self):
        a = JsonRpcMethodWrapper(name="a", method=lambda: None)
        b = JsonRpcMethodWrapper(name="b", method=lambda: None)
        assert a != b

    def test_eq_non_wrapper(self):
        w = JsonRpcMethodWrapper(name="m", method=lambda: None)
        assert w != "m"
        assert w != 42

    def test_hash_equal_for_same_name(self):
        a = JsonRpcMethodWrapper(name="x", method=lambda: None)
        b = JsonRpcMethodWrapper(name="x", method=lambda: None)
        assert hash(a) == hash(b)

    def test_hashable_in_set(self):
        a = JsonRpcMethodWrapper(name="x", method=lambda: None)
        b = JsonRpcMethodWrapper(name="x", method=lambda: None)
        assert len({a, b}) == 1

    def test_handle_invalid_params_error_jrpc_error(self):
        jerr = JsonRpcError(code=JsonRpcErrorCode.ParseError, message="bad")
        result = JsonRpcMethodWrapper._handle_invalid_params_error(jerr)
        assert result is jerr

    def test_handle_invalid_params_error_exception(self):
        result = JsonRpcMethodWrapper._handle_invalid_params_error(RuntimeError("oops"))
        assert isinstance(result, JsonRpcError)
        assert result.code is JsonRpcErrorCode.InvalidParams

    def test_call_with_args_validator_option_some(self):
        def validator(args):
            return Some(JsonRpcError(code=JsonRpcErrorCode.InvalidParams, message="nope"))

        w = JsonRpcMethodWrapper(name="m", method=lambda x: x, validators=[validator])
        result = w(Some([1, 2]))
        assert result.is_err()
        assert result.unwrap_err().message == "nope"

    def test_call_with_args_validator_false(self):
        def validator(args):
            return False

        w = JsonRpcMethodWrapper(name="m", method=lambda x: x, validators=[validator])
        result = w(Some([1, 2]))
        assert result.is_err()
        assert result.unwrap_err().code is JsonRpcErrorCode.InvalidParams

    def test_call_with_args_validator_exception(self):
        def validator(args):
            return RuntimeError("bad params")

        w = JsonRpcMethodWrapper(name="m", method=lambda x: x, validators=[validator])
        result = w(Some([1, 2]))
        assert result.is_err()
        assert result.unwrap_err().code is JsonRpcErrorCode.InternalError

    def test_call_with_args_validator_jrpc_error(self):
        def validator(args):
            return JsonRpcErrorCode.MethodNotFound.into()

        w = JsonRpcMethodWrapper(name="m", method=lambda x: x, validators=[validator])
        result = w(Some([1, 2]))
        assert result.is_err()
        assert result.unwrap_err().code is JsonRpcErrorCode.MethodNotFound

    def test_call_with_args_validator_passes(self):
        def validator(args):
            return True

        w = JsonRpcMethodWrapper(name="m", method=lambda x: sum(x), validators=[validator])
        result = w(Some([1, 2, 3]))
        assert result.is_ok()
        assert result.unwrap() == 6

    def test_call_with_args_method_success(self):
        w = JsonRpcMethodWrapper(name="m", method=lambda x: x[0] + x[1])
        result = w(Some([10, 20]))
        assert result.is_ok()
        assert result.unwrap() == 30

    def test_call_with_args_method_raises_exception(self):
        def bad_method(args):
            raise ValueError("boom")

        w = JsonRpcMethodWrapper(name="m", method=bad_method)
        result = w(Some([1]))
        assert result.is_err()
        assert result.unwrap_err().code is JsonRpcErrorCode.ExecutionError

    def test_call_no_args_method_success(self):
        w = JsonRpcMethodWrapper(name="m", method=lambda: 42)
        result = w(Nothing())
        assert result.is_ok()
        assert result.unwrap() == 42

    def test_call_no_args_method_raises_exception(self):
        def bad_method():
            raise RuntimeError("boom")

        w = JsonRpcMethodWrapper(name="m", method=bad_method)
        result = w(Nothing())
        assert result.is_err()
        assert result.unwrap_err().code is JsonRpcErrorCode.ExecutionError


# ---------------------------------------------------------------------------
# JsonRpcHandlerCollection
# ---------------------------------------------------------------------------


class TestJsonRpcHandlerCollection:
    def test_init(self):
        c = JsonRpcHandlerCollection()
        assert c._registry == {}

    def test_add_new(self):
        c = JsonRpcHandlerCollection()
        w = JsonRpcMethodWrapper(name="m", method=lambda: None)
        assert c.add(w) is True

    def test_add_duplicate(self):
        c = JsonRpcHandlerCollection()
        w = JsonRpcMethodWrapper(name="m", method=lambda: None)
        c.add(w)
        assert c.add(w) is False

    def test_try_get_found(self):
        c = JsonRpcHandlerCollection()
        w = JsonRpcMethodWrapper(name="m", method=lambda: None)
        c.add(w)
        opt = c.try_get("m")
        assert opt.is_some()
        assert opt.unwrap() is w

    def test_try_get_not_found(self):
        c = JsonRpcHandlerCollection()
        opt = c.try_get("missing")
        assert not opt.is_some()

    def test_exists_true(self):
        c = JsonRpcHandlerCollection()
        c.add(JsonRpcMethodWrapper(name="m", method=lambda: None))
        assert c.exists("m") is True

    def test_exists_false(self):
        c = JsonRpcHandlerCollection()
        assert c.exists("nope") is False

    def test_remove_by_name_found(self):
        c = JsonRpcHandlerCollection()
        c.add(JsonRpcMethodWrapper(name="m", method=lambda: None))
        assert c.remove_by_name("m") is True
        assert not c.try_get("m").is_some()

    def test_remove_by_name_not_found(self):
        c = JsonRpcHandlerCollection()
        assert c.remove_by_name("nope") is False

    def test_remove_by_string(self):
        c = JsonRpcHandlerCollection()
        c.add(JsonRpcMethodWrapper(name="m", method=lambda: None))
        assert c.remove("m") is True

    def test_remove_by_wrapper(self):
        c = JsonRpcHandlerCollection()
        w = JsonRpcMethodWrapper(name="m", method=lambda: None)
        c.add(w)
        assert c.remove(w) is True

    def test_remove_nonexistent(self):
        c = JsonRpcHandlerCollection()
        assert c.remove("nope") is False

    def test_remove_unexpected_type(self):
        c = JsonRpcHandlerCollection()
        assert c.remove(42) is False


# ---------------------------------------------------------------------------
# JsonRpcDispatcher
# ---------------------------------------------------------------------------


class TestJsonRpcDispatcher:
    def test_init(self):
        d = JsonRpcDispatcher()
        assert isinstance(d.request_handler_registry, JsonRpcHandlerCollection)
        assert isinstance(d.notification_handler_registry, JsonRpcHandlerCollection)

    def test_request_handler_registry_property(self):
        d = JsonRpcDispatcher()
        assert d.request_handler_registry is d._request_handler_registry

    def test_notification_handler_registry_property(self):
        d = JsonRpcDispatcher()
        assert d.notification_handler_registry is d._notification_handler_registry

    def test_call_with_request_handler_found(self):
        d = JsonRpcDispatcher()
        d.request_handler_registry.add(
            JsonRpcMethodWrapper(name="add", method=lambda args: args[0] + args[1])
        )
        req = JsonRpcRequest(method="add", params=[1, 2], id=1)
        result = d(req)
        assert result.is_some()
        resp = result.unwrap()
        assert resp.is_ok()
        assert resp.unwrap().result == 3

    def test_call_with_request_handler_not_found(self):
        d = JsonRpcDispatcher()
        req = JsonRpcRequest(method="missing", id=1)
        result = d(req)
        assert result.is_some()
        resp = result.unwrap()
        assert resp.is_ok()
        assert resp.unwrap().error.code is JsonRpcErrorCode.MethodNotFound

    def test_call_with_notification_handler_found(self):
        d = JsonRpcDispatcher()
        called = []

        def handler(args):
            called.append(args)

        d.notification_handler_registry.add(
            JsonRpcMethodWrapper(name="evt", method=handler)
        )
        notif = JsonRpcNotification(method="evt", params=[1, 2])
        result = d(notif)
        assert not result.is_some()
        assert called == [[1, 2]]

    def test_call_with_notification_handler_not_found(self):
        d = JsonRpcDispatcher()
        notif = JsonRpcNotification(method="missing")
        result = d(notif)
        assert result.is_some()
        assert result.unwrap().is_err()
        assert result.unwrap().unwrap_err().code is JsonRpcErrorCode.MethodNotFound

    def test_call_with_string_parse_success(self):
        d = JsonRpcDispatcher()
        d.request_handler_registry.add(
            JsonRpcMethodWrapper(name="add", method=lambda args: sum(args))
        )
        raw = json.dumps({"jsonrpc": "2.0", "method": "add", "params": [1, 2, 3], "id": 1})
        result = d(raw)
        assert result.is_some()
        resp = result.unwrap()
        assert resp.is_ok()
        assert resp.unwrap().result == 6

    def test_call_with_string_parse_failure(self):
        d = JsonRpcDispatcher()
        result = d("not json")
        assert result.is_some()
        resp = result.unwrap()
        assert resp.is_err()
        assert resp.unwrap_err().code is JsonRpcErrorCode.ParseError

    def test_call_with_unknown_type(self):
        d = JsonRpcDispatcher()
        result = d(42)
        assert result.is_some()
        resp = result.unwrap()
        assert resp.is_err()
        assert resp.unwrap_err().code is JsonRpcErrorCode.InternalError

    def test_extract_params_with_params(self):
        req = JsonRpcRequest(method="m", params=[1, 2])
        opt = JsonRpcDispatcher._extract_params(req)
        assert opt.is_some()
        assert opt.unwrap() == [1, 2]

    def test_extract_params_without_params(self):
        req = JsonRpcRequest(method="m")
        opt = JsonRpcDispatcher._extract_params(req)
        assert not opt.is_some()

    def test_extract_params_notification(self):
        n = JsonRpcNotification(method="m", params={"key": "val"})
        opt = JsonRpcDispatcher._extract_params(n)
        assert opt.is_some()
        assert opt.unwrap() == {"key": "val"}

    def test_try_parse_request(self):
        raw = json.dumps({"jsonrpc": "2.0", "method": "add", "id": 1, "params": [1]})
        result = JsonRpcDispatcher.try_parse(raw)
        assert result.is_ok()
        assert isinstance(result.unwrap(), JsonRpcRequest)

    def test_try_parse_invalid(self):
        result = JsonRpcDispatcher.try_parse("bad json")
        assert result.is_err()

    def test_dispatch_string_notification(self):
        d = JsonRpcDispatcher()
        d.request_handler_registry.add(
            JsonRpcMethodWrapper(name="evt", method=lambda args: None)
        )
        raw = json.dumps({"jsonrpc": "2.0", "method": "evt", "params": [1]})
        result = d(raw)
        assert result.is_some()
        resp = result.unwrap()
        assert resp.is_ok()
        assert resp.unwrap().result is None
