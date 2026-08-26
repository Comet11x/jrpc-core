import asyncio
from typing import Any

from jrpc_core import (
    JsonRpcDispatcher,
    JsonRpcError,
    JsonRpcMethodWrapper,
    JsonRpcRequest,
    JsonRpcResponse,
    JsonRpcResponseCtorWrapper,
)
from pyfplib import Option, Result, Err, Ok, Some, Nothing
from dataclasses import dataclass
from pydantic import field_serializer


class ApplicationError(Exception):
    def __init__(self, code: int, message: str):
        super().__init__(message)
        self._code = code


class UserDataError(ApplicationError):
    def __init__(self):
        super().__init__(1, "User data error")


class UserNotFound(ApplicationError):
    def __init__(self, name):
        super().__init__(2, f"User with name '{name}' not found")


class UserAlreadyExists(ApplicationError):
    def __init__(self, name):
        super().__init__(3, f"User with name '{name}' already exists")


@dataclass
class User:
    name: str
    age: int

    @staticmethod
    def try_from(data: dict[str, str | int]) -> Result["User", ApplicationError]:
        if (
            not isinstance(data, dict)
            or not isinstance(data.get("name"), str)
            or not isinstance(data.get("age"), int)
        ):
            return Err(UserDataError())
        return User(name=data["name"], age=data["age"])


class UserRegistry:
    def __init__(self):
        self._reg: dict[str, User] = {}

    def try_get(self, name: str) -> Result[User, ApplicationError]:
        user = self._reg.get(name)
        if user is not None:
            return Ok(user)
        else:
            return Err(UserNotFound(name))

    def try_add(self, user: User) -> Option[ApplicationError]:
        if self._reg.get(user.name) is None:
            self._reg[user.name] = user
            return Nothing()
        else:
            raise UserAlreadyExists(user.name)

    def try_remove(self, name: str) -> Result[User, ApplicationError]:
        if self._reg.get(name) is not None:
            user = self._reg[name]
            del self._reg[name]
            return Ok(user)
        else:
            return Err(UserNotFound(name))


def foo(args: list[str]) -> str:
    return "-".join(args)


def bar(args: list[int]) -> int:
    print("Call bar")
    return sum(args)


def make_request_to_add_user(name: str = "Foo") -> JsonRpcRequest:
    return JsonRpcRequest(method="add", params={"name": name, "age": 30})


def make_request_to_get_user(name: str = "Foo") -> JsonRpcRequest:
    return JsonRpcRequest(method="get", params={"name": name})


def make_request_to_remove_user(name: str = "Foo") -> JsonRpcRequest:
    return JsonRpcRequest(method="remove", params={"name": name})


def handle_response(maybe_res: Option[Result[JsonRpcResponse, JsonRpcError]]):
    if maybe_res.is_some():
        res1 = maybe_res.unwrap()
        if res1.is_ok():
            print(res1.unwrap().model_dump_json())
            # print(res1.unwrap())
        else:
            print(res1.unwrap_err())
    else:
        print("Error: option is empty")


class JsonRpcResponseForUserAdding(JsonRpcResponse):
    @field_serializer("result")
    def serialize_result(self, value: Any):
        return "Everything is OK" if value is not None else value

    @field_serializer("error")
    def serialize_error(self, value: JsonRpcError | None):
        if value is not None:
            value.data = str(value.data)
        return value


def ctor(**kwargs) -> JsonRpcResponse:
    print("<<<< ", kwargs)
    return JsonRpcResponse(id=kwargs["id"], result="Everything is OK")


def ctor_for_err(**kwargs) -> JsonRpcResponse:
    print("<<<< ERROR: ", kwargs)
    err = kwargs["error"]
    err.data = str(err.data)
    return JsonRpcResponse(id=kwargs["id"], error=err)


async def async_main():
    reg = UserRegistry()
    dispatcher = JsonRpcDispatcher()

    dispatcher.emplace_custom_response_ctor("add", JsonRpcResponseForUserAdding)

    dispatcher.emplace_request_handler(
        name="add", method=reg.try_add, converter=lambda data: User.try_from(data)
    )
    dispatcher.emplace_request_handler(
        name="get", method=reg.try_get, converter=lambda data: data["name"]
    )
    dispatcher.emplace_request_handler(
        name="remove", method=reg.try_remove, converter=lambda data: data["name"]
    )

    handle_response(await dispatcher(make_request_to_add_user()))
    handle_response(await dispatcher(make_request_to_add_user()))
    handle_response(await dispatcher(make_request_to_get_user()))
    handle_response(await dispatcher(make_request_to_remove_user("Foo")))


def main():
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
