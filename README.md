# jrpc-core

[![PyPI - Version](https://img.shields.io/pypi/v/jrpc-core.svg)](https://pypi.org/project/jrpc-core)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/jrpc-core.svg)](https://pypi.org/project/jrpc-core)
[![Tests](https://github.com/comet11x/jrpc-core/actions/workflows/test.yml/badge.svg)](https://github.com/comet11x/jrpc-core/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/comet11x/jrpc-core/branch/main/graph/badge.svg)](https://codecov.io/gh/comet11x/jrpc-core)

-----

A lightweight, type-safe Python implementation of the [JSON-RPC 2.0 specification](https://www.jsonrpc.org/specification).

**jrpc-core** provides two core layers:

| Layer          | Module                 | Purpose                                                                |
|----------------|------------------------|------------------------------------------------------------------------|
| **Messages**   | `jrpc_core.messages`   | Pydantic models for requests, responses, notifications, and errors     |
| **Dispatcher** | `jrpc_core.dispatcher` | Async registry-based routing of incoming messages to handler callables |

## Table of Contents

- [jrpc-core](#jrpc-core)
  - [Table of Contents](#table-of-contents)
  - [Features](#features)
  - [Quick Start](#quick-start)
  - [Documentation](#documentation)
  - [Installation](#installation)
  - [License](#license)

## Features

- **Type-safe** — every model is a Pydantic `BaseModel` with explicit field types and validators.
- **Functional** — error handling uses `Result` and `Option` from [pyfplib](https://pypi.org/project/pyfplib/) instead of exceptions.
- **Lightweight** — only depends on `pydantic` and `pyfplib`, no async runtime required.
- **Serialisable** — round-trips cleanly between Python objects and JSON strings.
- **Extensible** — custom response constructors, parameter validators, and converters.

## Quick Start

```python
import asyncio
from jrpc_core import JsonRpcRequest, JsonRpcDispatcher, JsonRpcMethodWrapper

# Create a request
request = JsonRpcRequest(method="add", params=[1, 2])
print(request.to_json())
# {"jsonrpc":"2.0","method":"add","params":[1,2],"id":"<uuid>"}

# Parse incoming JSON-RPC message
from jrpc_core import try_parse
result = try_parse('{"jsonrpc":"2.0","method":"add","params":[1,2],"id":"1"}')

# Use the dispatcher
async def main():
    dispatcher = JsonRpcDispatcher()
    dispatcher.request_handler_registry.add(
        JsonRpcMethodWrapper(name="add", method=lambda args: args[0] + args[1])
    )
    response = await dispatcher(JsonRpcRequest(method="add", params=[1, 2], id=1))
    print(response.unwrap().unwrap().result)  # 3

asyncio.run(main())
```

## Documentation

[Documentation pages](https://comet11x.github.io/jrpc-core/).

## Installation

```console
pip install jrpc-core
```

## License

`jrpc-core` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
