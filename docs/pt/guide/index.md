# O que é jrpc-core?

**jrpc-core** é uma biblioteca Python leve que implementa a [especificação JSON-RPC 2.0](https://www.jsonrpc.org/specification) com duas camadas principais:

| Camada | Módulo | Finalidade |
|---|---|---|
| **Mensagens** | `jrpc_core.messages` | Modelos Pydantic para requisições, respostas, notificações e erros |
| **Dispatcher** | `jrpc_core.dispatcher` | Roteamento baseado em registro de mensagens recebidas para chamadas de handler |

## Princípios de Design

- **Type-safe** — cada modelo é um `BaseModel` do Pydantic com tipos de campo e validadores explícitos.
- **Funcional** — tratamento de erros usa `Result` e `Option` do [pyfplib](https://pypi.org/project/pyfplib/) em vez de exceções.
- **Leve** — depende apenas de `pydantic` e `pyfplib`, não requer runtime async.
- **Serializável** — ida e volta limpa entre objetos Python e strings JSON.

## Arquitetura

```
String JSON recebida
        │
        ▼
   try_parse()
        │
   ┌────┴────┐
   │         │
Requisição  Notificação
   │         │
   ▼         ▼
JsonRpcDispatcher.__call__()
   │
   ├──► busca no registro de handlers
   │
   ▼
JsonRpcResponse
```

## Próximos Passos

- [Primeiros Passos](/pt/guide/getting-started) — instalação e primeira requisição
- [API de Mensagens](/pt/guide/messages) — referência completa para todos os modelos de mensagem
- [API de Dispatcher](/pt/guide/dispatcher) — referência completa para roteamento e registro de handlers
