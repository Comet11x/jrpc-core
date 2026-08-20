---
layout: home

hero:
  name: jrpc-core
  text: Python 的 JSON-RPC 2.0
  tagline: 基于 Pydantic 的轻量级、类型安全的消息传递、调度和验证。
  actions:
    - theme: brand
      text: 快速开始
      link: /zh/guide/getting-started
    - theme: alt
      text: 消息 API
      link: /zh/guide/messages

features:
  - title: Pydantic 模型
    details: 请求、响应、通知和错误模型，支持完整的验证和序列化。
  - title: 类型安全的调度
    details: 将传入的 JSON-RPC 消息路由到已注册的处理程序，并自动验证参数。
  - title: 函数式错误处理
    details: 基于 pyfplib 的 Result 和 Option 类型，实现显式的、可组合的错误流程。
---
