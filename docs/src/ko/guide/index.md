# jrpc-core란?

**jrpc-core**는 두 개의 핵심 레이어로 [JSON-RPC 2.0 사양](https://www.jsonrpc.org/specification)을 구현하는 가벼운 Python 라이브러리입니다:

| 레이어 | 모듈 | 목적 |
|---|---|---|
| **메시지** | `jrpc_core.messages` | 요청, 응답, 알림 및 오류를 위한 Pydantic 모델 |
| **디스패처** | `jrpc_core.dispatcher` | 등록된 핸들러로 들어오는 메시지의 레지스트리 기반 라우팅 |

## 설계 원칙

- **타입 안전** — 모든 모델은 명시적인 필드 타입과 검증기가 있는 Pydantic `BaseModel`입니다.
- **함수형** — 오류 처리는 예외 대신 [pyfplib](https://pypi.org/project/pyfplib/)의 `Result`와 `Option` 타입을 사용합니다.
- **가벼움** — `pydantic`과 `pyfplib`에만 의존하며, 비동기 런타임이 필요하지 않습니다.
- **직렬화 가능** — Python 객체와 JSON 문자열 간의 깔끔한 왕복.

## 아키텍처

```
들어오는 JSON 문자열
        │
        ▼
   try_parse()
        │
   ┌────┴────┐
   │         │
  요청    알림
   │         │
   ▼         ▼
JsonRpcDispatcher.__call__()
   │
   ├──► 핸들러 레지스트리 조회
   │
   ▼
JsonRpcResponse
```

## 다음 단계

- [시작하기](/ko/guide/getting-started) — 설치 및 첫 번째 요청 실행
- [메시지 API](/ko/guide/messages) — 모든 메시지 모델에 대한 전체 참조
- [디스패처 API](/ko/guide/dispatcher) — 라우팅 및 핸들러 등록에 대한 전체 참조
