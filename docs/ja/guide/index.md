# jrpc-core とは？

**jrpc-core** は、2つのコアレイヤーで [JSON-RPC 2.0 仕様](https://www.jsonrpc.org/specification) を実装する軽量な Python ライブラリです：

| レイヤー | モジュール | 目的 |
|---|---|---|
| **メッセージ** | `jrpc_core.messages` | リクエスト、レスポンス、通知、エラーの Pydantic モデル |
| **ディスパッチャ** | `jrpc_core.dispatcher` | 受信メッセージをハンドラ呼び出しにルーティングするレジストリベースの仕組み |

## 設計原則

- **型安全** — すべてのモデルは明示的なフィールド型とバリデータを持つ Pydantic の `BaseModel` です。
- **関数型** — エラー処理は例外ではなく、[pyfplib](https://pypi.org/project/pyfplib/) の `Result` と `Option` 型を使用します。
- **軽量** — `pydantic` と `pyfplib` にのみ依存し、非同期ランタイムは不要です。
- **シリアライズ可能** — Python オブジェクトと JSON 文字列の間でクリーンに往復します。

## アーキテクチャ

```
受信 JSON 文字列
        │
        ▼
   try_parse()
        │
   ┌────┴────┐
   │         │
リクエスト  通知
   │         │
   ▼         ▼
JsonRpcDispatcher.__call__()
   │
   ├──► ハンドラレジストリの検索
   │
   ▼
JsonRpcResponse
```

## 次のステップ

- [セットアップ](/ja/guide/getting-started) — インストールと最初のリクエスト
- [メッセージ API](/ja/guide/messages) — すべてのメッセージモデルの完全なリファレンス
- [ディスパッチャ API](/ja/guide/dispatcher) — ルーティングとハンドラ登録の完全なリファレンス
