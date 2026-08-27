# SPDX-FileCopyrightText: 2026-present comet11x <comet11x@protonmail.com>
#
# SPDX-License-Identifier: MIT
"""Unit tests for jrpc_core.dispatcher module."""

from __future__ import annotations

import asyncio
import json

from pyfplib import Err, Nothing, Ok, Result, Some

from jrpc_core.dispatcher import (
    JsonRpcDispatcher,
    JsonRpcHandlerCollection,
    JsonRpcMethodWrapper,
    JsonRpcResponseCtorWrapper,
    _AsyncWrapper,
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
    def test_init_without_validator_and_converter(self):
        w = JsonRpcMethodWrapper(name="m", method=lambda x: x)
        assert w.name == "m"
        assert w._validator is None
        assert w._converter is None

    def test_init_with_validator(self):
        v = lambda args: True
        w = JsonRpcMethodWrapper(name="m", method=lambda x: x, validator=v)
        assert w._validator is v

    def test_init_with_converter(self):
        c = lambda args: args
        w = JsonRpcMethodWrapper(name="m", method=lambda x: x, converter=c)
        assert w._converter is c

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
            return Some(
                JsonRpcError(code=JsonRpcErrorCode.InvalidParams, message="nope")
            )

        w = JsonRpcMethodWrapper(name="m", method=lambda x: x, validator=validator)
        result = asyncio.run(w(Some([1, 2])))
        assert result.is_err()
        assert result.unwrap_err().message == "nope"

    def test_call_with_args_validator_false(self):
        def validator(args):
            return False

        w = JsonRpcMethodWrapper(name="m", method=lambda x: x, validator=validator)
        result = asyncio.run(w(Some([1, 2])))
        assert result.is_err()
        assert result.unwrap_err().code is JsonRpcErrorCode.InvalidParams

    def test_call_with_args_validator_exception(self):
        def validator(args):
            return RuntimeError("bad params")

        w = JsonRpcMethodWrapper(name="m", method=lambda x: x, validator=validator)
        result = asyncio.run(w(Some([1, 2])))
        assert result.is_err()
        assert result.unwrap_err().code is JsonRpcErrorCode.InternalError

    def test_call_with_args_validator_jrpc_error(self):
        def validator(args):
            return JsonRpcErrorCode.MethodNotFound.into()

        w = JsonRpcMethodWrapper(name="m", method=lambda x: x, validator=validator)
        result = asyncio.run(w(Some([1, 2])))
        assert result.is_err()
        assert result.unwrap_err().code is JsonRpcErrorCode.MethodNotFound

    def test_call_with_args_validator_passes(self):
        def validator(args):
            return True

        w = JsonRpcMethodWrapper(name="m", method=lambda x: sum(x), validator=validator)
        result = asyncio.run(w(Some([1, 2, 3])))
        assert result.is_ok()
        assert result.unwrap() == 6

    def test_call_no_converter_passthrough(self):
        w = JsonRpcMethodWrapper(name="m", method=lambda x: x[0] + x[1])
        result = asyncio.run(w(Some([1, 2])))
        assert result.is_ok()
        assert result.unwrap() == 3

    def test_call_converter_raw_value(self):
        w = JsonRpcMethodWrapper(
            name="m",
            method=lambda name: f"hello {name}",
            converter=lambda p: p["name"],
        )
        result = asyncio.run(w(Some({"name": "Ada"})))
        assert result.is_ok()
        assert result.unwrap() == "hello Ada"

    def test_call_converter_option_some(self):
        w = JsonRpcMethodWrapper(
            name="m", method=lambda x: x * 2, converter=lambda p: Some(p)
        )
        result = asyncio.run(w(Some(21)))
        assert result.is_ok()
        assert result.unwrap() == 42

    def test_call_converter_option_nothing_rejected(self):
        w = JsonRpcMethodWrapper(
            name="m", method=lambda x: x, converter=lambda p: Nothing()
        )
        result = asyncio.run(w(Some([1])))
        assert result.is_err()
        err = result.unwrap_err()
        assert err.code is JsonRpcErrorCode.ConversionError

    def test_call_converter_result_ok(self):
        w = JsonRpcMethodWrapper(
            name="m", method=lambda x: x + 1, converter=lambda p: Ok(p)
        )
        result = asyncio.run(w(Some(41)))
        assert result.is_ok()
        assert result.unwrap() == 42

    def test_call_converter_result_err_rejected(self):
        w = JsonRpcMethodWrapper(
            name="m", method=lambda x: x, converter=lambda p: Err("bad shape")
        )
        result = asyncio.run(w(Some([1])))
        assert result.is_err()
        err = result.unwrap_err()
        assert err.code is JsonRpcErrorCode.ConversionError
        assert err.data == "bad shape"

    def test_call_converter_raises_rejected(self):
        def bad_converter(params):
            raise ValueError("nope")

        w = JsonRpcMethodWrapper(name="m", method=lambda x: x, converter=bad_converter)
        result = asyncio.run(w(Some([1])))
        assert result.is_err()
        err = result.unwrap_err()
        assert err.code is JsonRpcErrorCode.ConversionError
        assert isinstance(err.data, ValueError)

    def test_validation_runs_before_conversion(self):
        calls = []

        def validator(args):
            calls.append("validate")
            return True

        def converter(args):
            calls.append("convert")
            return args

        def method(args):
            calls.append("call")

        w = JsonRpcMethodWrapper(
            name="m", method=method, validator=validator, converter=converter
        )
        asyncio.run(w(Some([1])))
        assert calls == ["validate", "convert", "call"]

    def test_call_with_args_method_success(self):
        w = JsonRpcMethodWrapper(name="m", method=lambda x: x[0] + x[1])
        result = asyncio.run(w(Some([10, 20])))
        assert result.is_ok()
        assert result.unwrap() == 30

    def test_call_with_args_method_raises_exception(self):
        def bad_method(args):
            raise ValueError("boom")

        w = JsonRpcMethodWrapper(name="m", method=bad_method)
        result = asyncio.run(w(Some([1])))
        assert result.is_err()
        assert result.unwrap_err().code is JsonRpcErrorCode.ExecutionError

    def test_call_no_args_method_success(self):
        w = JsonRpcMethodWrapper(name="m", method=lambda: 42)
        result = asyncio.run(w(Nothing()))
        assert result.is_ok()
        assert result.unwrap() == 42

    def test_call_no_args_method_raises_exception(self):
        def bad_method():
            raise RuntimeError("boom")

        w = JsonRpcMethodWrapper(name="m", method=bad_method)
        result = asyncio.run(w(Nothing()))
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
# JsonRpcResponseCtorWrapper
# ---------------------------------------------------------------------------


class TestJsonRpcResponseCtorWrapperState:
    def test_is_result(self):
        state = JsonRpcResponseCtorWrapper.State.Result
        assert state.is_result() is True
        assert state.is_error() is False

    def test_is_error(self):
        state = JsonRpcResponseCtorWrapper.State.Error
        assert state.is_error() is True
        assert state.is_result() is False

    def test_int_conversion(self):
        assert int(JsonRpcResponseCtorWrapper.State.Result) == 1
        assert int(JsonRpcResponseCtorWrapper.State.Error) == 2


class TestJsonRpcResponseCtorWrapperWhen:
    W = JsonRpcResponseCtorWrapper
    S = JsonRpcResponseCtorWrapper.State

    def test_for_result_matches_only_result(self):
        when = self.W._When.for_result()
        assert when == self.S.Result
        assert not when == self.S.Error

    def test_for_error_matches_only_error(self):
        when = self.W._When.for_error()
        assert when == self.S.Error
        assert not when == self.S.Result

    def test_for_both_cases_matches_both(self):
        when = self.W._When.for_both_cases()
        assert when == self.S.Result
        assert when == self.S.Error

    def test_eq_same_code(self):
        assert self.W._When.for_result() == self.W._When.for_result()
        assert self.W._When.for_result() != self.W._When.for_error()

    def test_hash_equal_for_same_code(self):
        assert hash(self.W._When.for_result()) == hash(self.W._When.for_result())

    def test_str(self):
        assert str(self.W._When.for_result()) == "for result"
        assert str(self.W._When.for_error()) == "for error"
        assert str(self.W._When.for_both_cases()) == "for both cases"

    def test_repr_equals_str(self):
        when = self.W._When.for_both_cases()
        assert repr(when) == str(when)

    def test_int_returns_bitmask(self):
        assert int(self.W._When.for_result()) == 1
        assert int(self.W._When.for_error()) == 2
        assert int(self.W._When.for_both_cases()) == 3

    def test_eq_unrelated_object(self):
        when = self.W._When.for_result()
        assert (when == 42) is False
        assert (when == "for result") is False


class TestJsonRpcResponseCtorWrapper:
    def test_default_when_is_both_cases(self):
        w = JsonRpcResponseCtorWrapper("m", JsonRpcResponse)
        assert w.when == JsonRpcResponseCtorWrapper.State.Result
        assert w.when == JsonRpcResponseCtorWrapper.State.Error

    def test_explicit_states_restrict_when(self):
        w = JsonRpcResponseCtorWrapper(
            "m", JsonRpcResponse, JsonRpcResponseCtorWrapper.State.Error
        )
        assert w.when == JsonRpcResponseCtorWrapper.State.Error
        assert not w.when == JsonRpcResponseCtorWrapper.State.Result

    def test_method_property(self):
        w = JsonRpcResponseCtorWrapper("m", JsonRpcResponse)
        assert w.method == "m"

    def test_call_delegates_to_ctor(self):
        captured = {}

        def ctor(**kwargs):
            captured.update(kwargs)
            return "built"

        w = JsonRpcResponseCtorWrapper("m", ctor)
        assert w(id=1, result="x") == "built"
        assert captured == {"id": 1, "result": "x"}


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
        result = asyncio.run(d(req))
        assert result.is_some()
        resp = result.unwrap()
        assert resp.is_ok()
        assert resp.unwrap().result == 3

    def test_call_with_request_handler_not_found(self):
        d = JsonRpcDispatcher()
        req = JsonRpcRequest(method="missing", id=1)
        result = asyncio.run(d(req))
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
        result = asyncio.run(d(notif))
        assert not result.is_some()
        assert called == [[1, 2]]

    def test_call_with_notification_handler_not_found(self):
        d = JsonRpcDispatcher()
        notif = JsonRpcNotification(method="missing")
        result = asyncio.run(d(notif))
        assert result.is_some()
        assert result.unwrap().is_err()
        assert result.unwrap().unwrap_err().code is JsonRpcErrorCode.MethodNotFound

    def test_call_with_string_parse_success(self):
        d = JsonRpcDispatcher()
        d.request_handler_registry.add(
            JsonRpcMethodWrapper(name="add", method=lambda args: sum(args))
        )
        raw = json.dumps(
            {"jsonrpc": "2.0", "method": "add", "params": [1, 2, 3], "id": 1}
        )
        result = asyncio.run(d(raw))
        assert result.is_some()
        resp = result.unwrap()
        assert resp.is_ok()
        assert resp.unwrap().result == 6

    def test_call_with_string_parse_failure(self):
        d = JsonRpcDispatcher()
        result = asyncio.run(d("not json"))
        assert result.is_some()
        resp = result.unwrap()
        assert resp.is_err()
        assert resp.unwrap_err().code is JsonRpcErrorCode.ParseError

    def test_call_with_unknown_type(self):
        d = JsonRpcDispatcher()
        result = asyncio.run(d(42))
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
        d.notification_handler_registry.add(
            JsonRpcMethodWrapper(name="evt", method=lambda args: None)
        )
        raw = json.dumps({"jsonrpc": "2.0", "method": "evt", "params": [1]})
        result = asyncio.run(d(raw))
        assert not result.is_some()

    def test_emplace_request_handler_registers(self):
        d = JsonRpcDispatcher()
        assert d.emplace_request_handler(name="add", method=lambda a, b: a + b) is True
        assert d.request_handler_registry.exists("add") is True
        assert d.emplace_request_handler(name="add", method=lambda x: x) is False

    def test_emplace_request_handler_with_validator_and_converter(self):
        d = JsonRpcDispatcher()
        d.emplace_request_handler(
            name="greet",
            method=lambda name: f"hi {name}",
            validator=lambda p: isinstance(p, dict),
            converter=lambda p: p["name"],
        )
        req = JsonRpcRequest(method="greet", params={"name": "Ada"}, id=1)
        resp = asyncio.run(d(req)).unwrap().unwrap()
        assert resp.result == "hi Ada"

    def test_emplace_notification_handler_registers(self):
        d = JsonRpcDispatcher()
        assert (
            d.emplace_notification_handler(name="evt", method=lambda args: None) is True
        )
        assert d.notification_handler_registry.exists("evt") is True
        assert (
            d.emplace_notification_handler(name="evt", method=lambda args: None)
            is False
        )

    def test_custom_response_ctor_used_on_success(self):
        captured = {}

        def ctor(**kwargs):
            captured.update(kwargs)
            return JsonRpcResponse(id=kwargs["id"], result="custom")

        d = JsonRpcDispatcher()
        d.emplace_custom_response_ctor("add", ctor)
        d.emplace_request_handler(name="add", method=lambda args: args[0] + args[1])
        resp = (
            asyncio.run(d(JsonRpcRequest(method="add", params=[1, 2], id=9)))
            .unwrap()
            .unwrap()
        )
        assert resp.result == "custom"
        assert captured["id"] == 9
        assert captured["result"] == 3

    def test_add_custom_response_ctor_used_on_success(self):
        def ctor(**kwargs):
            return JsonRpcResponse(id=kwargs["id"], result="wrapped")

        d = JsonRpcDispatcher()
        d.add_custom_response_ctor(JsonRpcResponseCtorWrapper("m", ctor))
        d.emplace_request_handler(name="m", method=lambda args: 42)
        resp = (
            asyncio.run(d(JsonRpcRequest(method="m", params=[1], id=8)))
            .unwrap()
            .unwrap()
        )
        assert resp.result == "wrapped"

    def test_error_case_ctor_used_on_error(self):
        def ctor(**kwargs):
            return JsonRpcResponse(id=kwargs["id"], error=kwargs["error"])

        def boom(args):
            raise RuntimeError("boom")

        d = JsonRpcDispatcher()
        d.add_custom_response_ctor(
            JsonRpcResponseCtorWrapper("fail", ctor, JsonRpcDispatcher.ERROR_CASE)
        )
        d.emplace_request_handler(name="fail", method=boom)
        resp = (
            asyncio.run(d(JsonRpcRequest(method="fail", params=[1], id=5)))
            .unwrap()
            .unwrap()
        )
        assert resp.error is not None
        assert resp.error.code is JsonRpcErrorCode.ExecutionError
        assert isinstance(resp.error.data, RuntimeError)

    def test_result_case_ctor_ignored_on_error(self):
        def ctor(**kwargs):
            return JsonRpcResponse(id=kwargs["id"], result="should not happen")

        def boom(args):
            raise RuntimeError("boom")

        d = JsonRpcDispatcher()
        d.add_custom_response_ctor(
            JsonRpcResponseCtorWrapper("m", ctor, JsonRpcDispatcher.RESULT_CASE)
        )
        d.emplace_request_handler(name="m", method=boom)
        resp = (
            asyncio.run(d(JsonRpcRequest(method="m", params=[1], id=6)))
            .unwrap()
            .unwrap()
        )
        assert resp.error is not None
        assert resp.error.code is JsonRpcErrorCode.ExecutionError
        assert ctor(id=6, result=1).result == "should not happen"

    def test_error_case_ctor_ignored_on_success(self):
        def ctor(**kwargs):
            return JsonRpcResponse(id=kwargs["id"], result="should not happen")

        d = JsonRpcDispatcher()
        d.add_custom_response_ctor(
            JsonRpcResponseCtorWrapper("m", ctor, JsonRpcDispatcher.ERROR_CASE)
        )
        d.emplace_request_handler(name="m", method=lambda args: 42)
        resp = (
            asyncio.run(d(JsonRpcRequest(method="m", params=[1], id=7)))
            .unwrap()
            .unwrap()
        )
        assert resp.result == 42
        assert ctor(id=7, result=1).result == "should not happen"

    def test_add_custom_response_ctor_replaces_existing(self):
        first = JsonRpcResponseCtorWrapper(
            "m", lambda **kw: JsonRpcResponse(id=kw["id"])
        )
        second = JsonRpcResponseCtorWrapper(
            "m", lambda **kw: JsonRpcResponse(id=kw["id"])
        )
        d = JsonRpcDispatcher()
        d.add_custom_response_ctor(first)
        d.add_custom_response_ctor(second)
        when, ctor = d._registry["m"]
        assert ctor is second


# ---------------------------------------------------------------------------
# JsonRpcDispatcher.request decorator
# ---------------------------------------------------------------------------


class TestJsonRpcDispatcherRequestDecorator:
    def test_registers_under_explicit_method(self):
        d = JsonRpcDispatcher()

        @d.request(method="add")
        def my_adder(args):
            return sum(args)

        assert d.request_handler_registry.exists("add") is True
        assert d.request_handler_registry.exists("my_adder") is False

        req = JsonRpcRequest(method="add", params=[1, 2, 3], id=1)
        resp = asyncio.run(d(req)).unwrap().unwrap()
        assert resp.result == 6

    def test_registers_under_function_name_by_default(self):
        d = JsonRpcDispatcher()

        @d.request()
        def add(args):
            return args[0] + args[1]

        assert d.request_handler_registry.exists("add") is True

        req = JsonRpcRequest(method="add", params=[2, 3], id=1)
        resp = asyncio.run(d(req)).unwrap().unwrap()
        assert resp.result == 5

    def test_returns_same_function(self):
        d = JsonRpcDispatcher()

        @d.request(method="add")
        def add(args):
            return sum(args)

        assert add.__name__ == "add"

        req = JsonRpcRequest(method="add", params=[1, 2, 3], id=1)
        resp = asyncio.run(d(req)).unwrap().unwrap()
        assert resp.result == 6

    def test_dispatch(self):
        d = JsonRpcDispatcher()

        @d.request(method="add")
        def handler(args):
            return sum(args)

        req = JsonRpcRequest(method="add", params=[1, 2, 3], id=7)
        result = asyncio.run(d(req))
        assert result.is_some()
        resp = result.unwrap()
        assert resp.is_ok()
        assert resp.unwrap().id == 7
        assert resp.unwrap().result == 6

    def test_registers_under_explicit_method_for_callable(self):
        d = JsonRpcDispatcher()

        class Adder:
            def __call__(self, args):
                return args[0] + args[1]

        d.request(method="add")(Adder())
        assert d.request_handler_registry.exists("add") is True

        req = JsonRpcRequest(method="add", params=[1, 2], id=1)
        resp = asyncio.run(d(req)).unwrap().unwrap()
        assert resp.result == 3

    def test_with_validator_rejects_invalid_params(self):
        def validator(params):
            return isinstance(params, dict)

        d = JsonRpcDispatcher()

        @d.request(method="greet", validator=validator)
        def greet(args):
            return f"hi {args['name']}"

        req = JsonRpcRequest(method="greet", params=[1, 2], id=1)
        resp = asyncio.run(d(req)).unwrap().unwrap()
        assert resp.error is not None
        assert resp.error.code is JsonRpcErrorCode.InvalidParams

        ok_req = JsonRpcRequest(method="greet", params={"name": "Ada"}, id=2)
        ok_resp = asyncio.run(d(ok_req)).unwrap().unwrap()
        assert ok_resp.result == "hi Ada"

    def test_with_validator_accepts_valid_params(self):
        def validator(params):
            return isinstance(params, dict)

        d = JsonRpcDispatcher()

        @d.request(method="greet", validator=validator)
        def greet(args):
            return f"hi {args['name']}"

        req = JsonRpcRequest(method="greet", params={"name": "Ada"}, id=2)
        resp = asyncio.run(d(req)).unwrap().unwrap()
        assert resp.result == "hi Ada"

    def test_with_converter(self):
        d = JsonRpcDispatcher()

        @d.request(method="double", converter=lambda p: p[0] * 2)
        def double_(args):
            return args

        req = JsonRpcRequest(method="double", params=[21], id=3)
        resp = asyncio.run(d(req)).unwrap().unwrap()
        assert resp.result == 42


# ---------------------------------------------------------------------------
# JsonRpcDispatcher.notification decorator
# ---------------------------------------------------------------------------


class TestJsonRpcDispatcherNotificationDecorator:
    def test_registers_under_explicit_method(self):
        d = JsonRpcDispatcher()

        @d.notification(method="evt")
        def my_handler(args):
            pass

        assert d.notification_handler_registry.exists("evt") is True
        assert d.notification_handler_registry.exists("my_handler") is False

        result = asyncio.run(d(JsonRpcNotification(method="evt", params=[1, 2])))
        assert not result.is_some()

    def test_registers_under_function_name_by_default(self):
        d = JsonRpcDispatcher()

        @d.notification()
        def on_event(args):
            pass

        assert d.notification_handler_registry.exists("on_event") is True

        result = asyncio.run(d(JsonRpcNotification(method="on_event", params=[1])))
        assert not result.is_some()

    def test_returns_same_function(self):
        d = JsonRpcDispatcher()

        @d.notification(method="evt")
        def on_event(args):
            pass

        assert on_event.__name__ == "on_event"

        result = asyncio.run(d(JsonRpcNotification(method="evt", params=[1])))
        assert not result.is_some()

    def test_dispatch(self):
        d = JsonRpcDispatcher()
        called = []

        @d.notification(method="evt")
        def handler(args):
            called.append(args)

        notif = JsonRpcNotification(method="evt", params=[1, 2])
        result = asyncio.run(d(notif))
        assert not result.is_some()
        assert called == [[1, 2]]

    def test_dispatch_without_params(self):
        d = JsonRpcDispatcher()
        called = []

        @d.notification(method="evt")
        def handler():
            called.append("called")

        notif = JsonRpcNotification(method="evt")
        result = asyncio.run(d(notif))
        assert not result.is_some()
        assert called == ["called"]

    def test_with_validator_rejects_invalid_params(self):
        def validator(params):
            return isinstance(params, dict)

        d = JsonRpcDispatcher()
        called = []

        @d.notification(method="evt", validator=validator)
        def handler(args):
            called.append(args)

        notif = JsonRpcNotification(method="evt", params=[1, 2])
        asyncio.run(d(notif))
        assert called == []

        ok_notif = JsonRpcNotification(method="evt", params={"key": "val"})
        asyncio.run(d(ok_notif))
        assert called == [{"key": "val"}]

    def test_with_converter(self):
        d = JsonRpcDispatcher()
        called = []

        @d.notification(method="evt", converter=lambda p: p[0] * 2)
        def handler(args):
            called.append(args)

        notif = JsonRpcNotification(method="evt", params=[21])
        asyncio.run(d(notif))
        assert called == [42]


# ---------------------------------------------------------------------------
# JsonRpcDispatcher.response decorator
# ---------------------------------------------------------------------------


class TestJsonRpcDispatcherResponseDecorator:
    def test_registers_handler(self):
        d = JsonRpcDispatcher()
        seen = []

        @d.response()
        def handler(msg):
            seen.append(msg)

        resp = JsonRpcResponse(id=1, result=42)
        result = asyncio.run(d(resp))
        assert not result.is_some()
        assert len(seen) == 1
        assert seen[0].id == 1
        assert seen[0].result == 42

    def test_returns_async_wrapper(self):
        d = JsonRpcDispatcher()

        @d.response()
        def handler(msg):
            return msg

        assert asyncio.iscoroutinefunction(handler)

        asyncio.run(handler(JsonRpcResponse(id=1, result="x")))

    def test_registers_error_response(self):
        d = JsonRpcDispatcher()
        got = []

        @d.response()
        def handler(msg):
            got.append(msg.error)

        err = JsonRpcError.from_error(RuntimeError("boom"))
        resp = JsonRpcResponse(id=1, error=err)
        asyncio.run(d(resp))
        assert len(got) == 1
        assert got[0].code is JsonRpcErrorCode.InternalError

    def test_multiple_handlers_all_called(self):
        d = JsonRpcDispatcher()
        seen = []

        @d.response()
        def first(msg):
            seen.append(("first", msg.result))

        @d.response()
        def second(msg):
            seen.append(("second", msg.result))

        resp = JsonRpcResponse(id=1, result="x")
        asyncio.run(d(resp))
        assert ("first", "x") in seen
        assert ("second", "x") in seen

    def test_direct_call_without_converter_passes_message(self):
        d = JsonRpcDispatcher()
        seen = []

        @d.response()
        def handler(msg):
            seen.append(msg.result)

        resp = JsonRpcResponse(id=1, result=42)
        asyncio.run(handler(resp))
        assert seen == [42]

    def test_direct_call_applies_converter(self):
        d = JsonRpcDispatcher()
        seen = []

        @d.response(converter=lambda r: r.result * 10)
        def handler(msg):
            seen.append(msg)

        resp = JsonRpcResponse(id=1, result=4)
        asyncio.run(handler(resp))
        assert seen == [40]

    def test_converter_not_applied_on_internal_dispatch(self):
        d = JsonRpcDispatcher()
        seen = []

        @d.response(converter=lambda r: r.result * 10)
        def handler(msg):
            seen.append(msg)

        resp = JsonRpcResponse(id=1, result=4)
        asyncio.run(d(resp))
        assert seen == [resp]


# ---------------------------------------------------------------------------
# Additional coverage
# ---------------------------------------------------------------------------


class TestAsyncWrapper:
    def test_try_wrap_callable(self):
        result = _AsyncWrapper.try_wrap(lambda: None)
        assert result.is_some()

    def test_try_wrap_non_callable(self):
        result = _AsyncWrapper.try_wrap(42)
        assert not result.is_some()

    def test_wrap_sync_function(self):
        wrapped = _AsyncWrapper.wrap(lambda: 42)
        assert isinstance(wrapped, _AsyncWrapper)
        assert asyncio.run(wrapped()) == 42


class TestValidatorRaisesException:
    def test_validator_exception_in_validate(self):
        def bad_validator(args):
            raise RuntimeError("validator crashed")

        w = JsonRpcMethodWrapper(name="m", method=lambda x: x, validator=bad_validator)
        result = asyncio.run(w(Some([1])))
        assert result.is_err()
        assert result.unwrap_err().code is JsonRpcErrorCode.InternalError


class TestMethodReturnsNonJrpcErr:
    def test_no_args_returns_err(self):
        def method():
            return Err("raw error")

        w = JsonRpcMethodWrapper(name="m", method=method)
        result = asyncio.run(w(Nothing()))
        assert result.is_err()
        assert result.unwrap_err().code is JsonRpcErrorCode.ExecutionError
        assert result.unwrap_err().data == "raw error"

    def test_with_args_returns_err(self):
        def method(args):
            return Err("raw error")

        w = JsonRpcMethodWrapper(name="m", method=method)
        result = asyncio.run(w(Some([1])))
        assert result.is_err()
        assert result.unwrap_err().code is JsonRpcErrorCode.ExecutionError
        assert result.unwrap_err().data == "raw error"


class TestDispatcherResponseHandler:
    def test_call_with_response_handler(self):
        handled = []

        def handler(resp):
            handled.append(resp)

        d = JsonRpcDispatcher(response_handler=handler)
        resp = JsonRpcResponse(id=1, result="ok")
        result = asyncio.run(d(resp))
        assert not result.is_some()
        assert len(handled) == 1
        assert handled[0].result == "ok"

    def test_call_with_response_handler_not_set(self):
        d = JsonRpcDispatcher()
        resp = JsonRpcResponse(id=1, result="ok")
        maybe_result = asyncio.run(d(resp))
        assert maybe_result.is_none()


class TestDispatcherResultErr:
    def test_call_with_result_err(self):
        d = JsonRpcDispatcher()
        err = JsonRpcError(code=JsonRpcErrorCode.InternalError, message="fail")
        maybe_result = asyncio.run(d(Result(error=err)))
        assert maybe_result.is_some()
        res = maybe_result.unwrap()
        assert res.is_err() and isinstance(res.unwrap_err(), JsonRpcError)
        inner = res.unwrap_err()
        assert inner.code is JsonRpcErrorCode.InternalError

    def test_call_with_result_ok(self):
        d = JsonRpcDispatcher()
        d.emplace_request_handler(name="m", method=lambda args: 42)
        result = asyncio.run(
            d(Result(value=JsonRpcRequest(method="m", params=[1], id=1)))
        )
        assert result.is_some()
        assert result.unwrap().is_ok()
        assert result.unwrap().unwrap().result == 42
