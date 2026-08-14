import json

from jrpc_core import JsonRpcNotification, JsonRpcRequest, JsonRpcResponse


class TestJsonRpcRequest:
    def test_from_dict_with_params(self):
        result = JsonRpcRequest.from_dict(
            {"jsonrpc": "2.0", "method": "subtract", "params": [42, 23], "id": 1}
        )
        assert result.is_ok()
        assert result.value.to_dict() == {
            "jsonrpc": "2.0",
            "method": "subtract",
            "params": [42, 23],
            "id": 1,
        }

    def test_from_dict_defaults_version_and_omits_params(self):
        result = JsonRpcRequest.from_dict({"method": "ping", "id": "abc"})
        assert result.is_ok()
        assert result.value.to_dict() == {
            "jsonrpc": "2.0",
            "method": "ping",
            "id": "abc",
        }

    def test_from_dict_ignores_unknown_members(self):
        result = JsonRpcRequest.from_dict({"method": "ping", "id": 1, "extra": 42})
        assert result.is_ok()
        assert "extra" not in result.value.to_dict()

    def test_from_dict_missing_id_is_error(self):
        result = JsonRpcRequest.from_dict({"method": "ping"})
        assert result.is_err()

    def test_from_dict_bad_version_is_error(self):
        result = JsonRpcRequest.from_dict({"method": "ping", "id": 1, "jsonrpc": "1.0"})
        assert result.is_err()

    def test_from_dict_empty_method_is_error(self):
        result = JsonRpcRequest.from_dict({"method": "", "id": 1})
        assert result.is_err()

    def test_from_dict_non_string_method_is_error(self):
        result = JsonRpcRequest.from_dict({"method": 42, "id": 1})
        assert result.is_err()

    def test_from_json_round_trip(self):
        payload = json.dumps(
            {"jsonrpc": "2.0", "method": "ping", "params": [], "id": 1}
        )
        result = JsonRpcRequest.from_json(payload)
        assert result.is_ok()
        assert result.value.to_dict() == {
            "jsonrpc": "2.0",
            "method": "ping",
            "params": [],
            "id": 1,
        }

    def test_from_json_invalid_is_error(self):
        result = JsonRpcRequest.from_json('{"method": 42}')
        assert result.is_err()


class TestJsonRpcNotification:
    def test_from_dict_with_params(self):
        result = JsonRpcNotification.from_dict(
            {"method": "update", "params": [1, 2, 4, 8]}
        )
        assert result.is_ok()
        assert result.value.to_dict() == {
            "jsonrpc": "2.0",
            "method": "update",
            "params": [1, 2, 4, 8],
        }

    def test_from_dict_without_params(self):
        result = JsonRpcNotification.from_dict({"method": "notify"})
        assert result.is_ok()
        assert result.value.to_dict() == {"jsonrpc": "2.0", "method": "notify"}

    def test_from_dict_with_id_is_error(self):
        result = JsonRpcNotification.from_dict({"method": "notify", "id": 1})
        assert result.is_err()

    def test_from_dict_empty_method_is_error(self):
        result = JsonRpcNotification.from_dict({"method": ""})
        assert result.is_err()


class TestJsonRpcResponse:
    def test_from_result(self):
        response = JsonRpcResponse.from_result(id=1, result=19)
        assert response.to_dict() == {"jsonrpc": "2.0", "id": 1, "result": 19}

    def test_from_error(self):
        response = JsonRpcResponse.from_error(
            id=1, code=-32601, message="Method not found"
        )
        assert response.to_dict() == {
            "jsonrpc": "2.0",
            "id": 1,
            "error": {"code": -32601, "message": "Method not found"},
        }

    def test_from_error_with_data(self):
        response = JsonRpcResponse.from_error(
            id=None, code=-32700, message="Parse error", data={"detail": "bad json"}
        )
        assert response.to_dict()["error"] == {
            "code": -32700,
            "message": "Parse error",
            "data": {"detail": "bad json"},
        }

    def test_from_dict_with_result(self):
        result = JsonRpcResponse.from_dict({"jsonrpc": "2.0", "id": 1, "result": 19})
        assert result.is_ok()
        assert result.value.to_dict() == {"jsonrpc": "2.0", "id": 1, "result": 19}

    def test_from_dict_with_error(self):
        result = JsonRpcResponse.from_dict(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "error": {"code": -32601, "message": "Method not found"},
            }
        )
        assert result.is_ok()

    def test_from_dict_result_and_error_is_error(self):
        result = JsonRpcResponse.from_dict(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "result": 19,
                "error": {"code": -1, "message": "boom"},
            }
        )
        assert result.is_err()

    def test_from_dict_invalid_error_object_is_error(self):
        result = JsonRpcResponse.from_dict(
            {"jsonrpc": "2.0", "id": 1, "error": {"code": -1}}
        )
        assert result.is_err()

    def test_from_dict_bad_error_code_type_is_error(self):
        result = JsonRpcResponse.from_dict(
            {"jsonrpc": "2.0", "id": 1, "error": {"code": "x", "message": "boom"}}
        )
        assert result.is_err()

    def test_from_dict_missing_id_is_error(self):
        result = JsonRpcResponse.from_dict({"jsonrpc": "2.0", "result": 19})
        assert result.is_err()

    def test_from_json_round_trip(self):
        payload = json.dumps({"jsonrpc": "2.0", "id": 1, "result": None})
        result = JsonRpcResponse.from_json(payload)
        assert result.is_ok()
        assert result.value.to_dict() == {"jsonrpc": "2.0", "id": 1, "result": None}
