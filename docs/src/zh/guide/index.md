# 什么是 jrpc-core？

**jrpc-core** 是一个轻量级的 Python 库，实现了 [JSON-RPC 2.0 规范](https://www.jsonrpc.org/specification)，包含两个核心层：

| 层 | 模块 | 用途 |
|---|---|---|
| **消息** | `jrpc_core.messages` | 用于请求、响应、通知和错误的 Pydantic 模型 |
| **调度器** | `jrpc_core.dispatcher` | 基于注册表的传入消息到处理程序的路由 |

## 设计原则

- **类型安全** — 每个模型都是 Pydantic 的 `BaseModel`，具有显式的字段类型和验证器。
- **函数式** — 错误处理使用 [pyfplib](https://pypi.org/project/pyfplib/) 的 `Result` 和 `Option` 类型，而非异常。
- **轻量级** — 仅依赖 `pydantic` 和 `pyfplib`，无需异步运行时。
- **可序列化** — 可在 Python 对象和 JSON 字符串之间干净地往返转换。

## 架构

```
传入的 JSON 字符串
        │
        ▼
   try_parse()
        │
   ┌────┴────┐
   │         │
  请求     通知
   │         │
   ▼         ▼
JsonRpcDispatcher.__call__()
   │
   ├──► 处理程序注册表查找
   │
   ▼
JsonRpcResponse
```

## 下一步

- [快速开始](/zh/guide/getting-started) — 安装并运行您的第一个请求
- [消息 API](/zh/guide/messages) — 所有消息模型的完整参考
- [调度器 API](/zh/guide/dispatcher) — 路由和处理程序注册的完整参考
