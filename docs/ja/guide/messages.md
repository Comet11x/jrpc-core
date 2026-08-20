# メッセージ API

すべてのメッセージプリミティブは `jrpc_core.messages` モジュールに含まれています。

```python
from jrpc_core.messages import (
    JsonRpcRequest,
    JsonRpcNotification,
    JsonRpcResponse,
    JsonRpcError,
    JsonRpcErrorCode,
    JsonRpcVersion,
    try_parse,
)
```

---

## 型エイリアス

### `JsonRpcId`

```python
JsonRpcId = str | int | float | None
```

JSON-RPC メッセージ識別子の型エイリアス。有効な識別子は `str`、`int`、`float`、または `None` です。`None` は通知でのみ許可されます。

### `JsonRpcParams`

```python
JsonRpcParams = dict[str, Any] | list[Any] | None
```

JSON-RPC の `params` 値の型エイリアス。パラメータは名前付きマッピング（`dict`）、位置付きリスト（`list`）、または省略された場合は `None` です。

---

## `JsonRpcErrorCode`

```python
class JsonRpcErrorCode(Enum)
```

標準的な JSON-RPC 2.0 エラーコードの列挙型。各メンバーは、仕様または一般的な拡張で定義された整数コード（`-32xxx` は予約済み、`-320xx` はサーバー定義）にマッピングされます。

### メンバー

| メンバー | 値 | 説明 |
|---|---|---|
| `ParseError` | `-32700` | サーバーが無効な JSON を受信しました。 |
| `InternalError` | `-32603` | 内部 JSON-RPC エラーが発生しました。 |
| `InvalidParams` | `-32602` | メソッドに送信されたパラメータが無効です。 |
| `MethodNotFound` | `-32601` | メソッドが存在しないか、利用できません。 |
| `InvalidRequest` | `-32600` | 送信された JSON は有効なリクエストオブジェクトではありません。 |
| `ExecutionError` | `-32000` | サーバー定義の実行エラーが発生しました。 |

### メソッド

#### `__int__() -> int`

このエラーコードの整数値を返します。

```python
>>> int(JsonRpcErrorCode.ParseError)
-32700
```

#### `description() -> str`

このエラーコードの人間が読める説明を返します。

```python
>>> JsonRpcErrorCode.ParseError.description()
'Parse error'
```

#### `default() -> JsonRpcErrorCode` *(static)*

他のコードが適切でない場合に使用されるデフォルトのエラーコードを返します。`InternalError` を返します。

```python
>>> JsonRpcErrorCode.default()
<JsonRpcErrorCode.InternalError: -32603>
```

#### `into(data: Any = None) -> JsonRpcError`

このコードから `JsonRpcError` を作成します。

| パラメータ | 型 | デフォルト | 説明 |
|---|---|---|---|
| `data` | `Any` | `None` | エラーに添付されるオプションの追加ペイロード。 |

**戻り値：** このコードとその説明を持つ新しい `JsonRpcError`。

```python
>>> err = JsonRpcErrorCode.ParseError.into()
>>> err.code
<JsonRpcErrorCode.ParseError: -32700>
>>> err.message
'Parse error'
```

---

## `JsonRpcVersion`

```python
class JsonRpcVersion(StrEnum)
```

サポートされている JSON-RPC プロトコルバージョン。

| メンバー | 値 |
|---|---|
| `Version1` | `"1.0"` |
| `Version2` | `"2.0"` |

---

## `JsonRpcError`

```python
class JsonRpcError(BaseModel)
```

JSON-RPC 2.0 エラーオブジェクト。

### 属性

| 属性 | 型 | デフォルト | 説明 |
|---|---|---|---|
| `code` | `JsonRpcErrorCode \| int` | `JsonRpcErrorCode.InternalError` | 整数エラーコード。 |
| `message` | `str` | `"Something went wrong"` | 短い人間が読める説明。 |
| `data` | `Any \| None` | `None` | エラーに関するオプションの追加情報。 |

### メソッド

#### `default() -> JsonRpcError` *(static)*

`JsonRpcErrorCode.InternalError` を持つデフォルトのエラーを返します。

```python
>>> JsonRpcError.default()
JsonRpcError(code=<JsonRpcErrorCode.InternalError: -32603>, message='Something went wrong', data=None)
```

#### `from_error(error: JsonRpcError | Any) -> JsonRpcError` *(static)*

任意の値を `JsonRpcError` に変換します。*error* がすでに `JsonRpcError` の場合はそのまま返されます。それ以外の場合、関数は `code` 属性の抽出を試み、それを基にエラーを構築し、フォールバックとして `JsonRpcErrorCode.InternalError` を使用します。

| パラメータ | 型 | 説明 |
|---|---|---|
| `error` | `JsonRpcError \| Any` | 変換する値。 |

**戻り値：** `JsonRpcError` インスタンス。

```python
>>> JsonRpcError.from_error(RuntimeError("oops"))
JsonRpcError(code=<JsonRpcErrorCode.InternalError: -32603>, message='Internal error', data=RuntimeError('oops'))
```

#### `try_from(value: Option[JsonRpcError | Any]) -> Option[JsonRpcError]` *(static)*

`Option` をエラーに変換しようします。

| パラメータ | 型 | 説明 |
|---|---|---|
| `value` | `Option[JsonRpcError \| Any]` | 変換する値を含む可能性のある `Option`。 |

**戻り値：** *value* が `Some` であれば `Some(JsonRpcError)`、それ以外は `Nothing`。

```python
>>> from pyfplib import Some, Nothing
>>> JsonRpcError.try_from(Some(RuntimeError("x"))).is_some()
True
>>> JsonRpcError.try_from(Nothing()).is_some()
False
```

---

## `JsonRpcRequest`

```python
class JsonRpcRequest(BaseModel)
```

JSON-RPC 2.0 リクエストオブジェクト。`method` 名、オプションの `params` ペイロード、クライアントがレスポンスを関連付けるために使用する `id` を含みます。

### 属性

| 属性 | 型 | デフォルト | 説明 |
|---|---|---|---|
| `method` | `str` | *（必須）* | 呼び出すリモートプロシージャの名前。空でない文字列である必要があります。 |
| `id` | `JsonRpcId` | `str(uuid4())` | このリクエストの一意の識別子（デフォルトは自動生成の UUID）。 |
| `params` | `JsonRpcParams` | `None` | メソッドのオプションの位置付きまたは名前付き引数。 |
| `jsonrpc` | `JsonRpcVersion` | `Version2` | プロトコルバージョン。 |

### メソッド

#### `try_from_dict(data: dict) -> Result[JsonRpcRequest, Exception]` *(classmethod)*

プレーンな辞書からリクエストを構築しようします。

| パラメータ | 型 | 説明 |
|---|---|---|
| `data` | `dict[str, Any]` | JSON-RPC リクエストフィールドを持つ辞書。 |

**戻り値：** 成功時は `Ok(request)`、バリデーション失敗時は `Err(exception)`。

```python
>>> JsonRpcRequest.try_from_dict({"method": "add", "id": 1}).is_ok()
True
```

#### `try_from_json(data: str) -> Result[JsonRpcRequest, Exception]` *(classmethod)*

JSON 文字列からリクエストを構築しようします。

| パラメータ | 型 | 説明 |
|---|---|---|
| `data` | `str` | リクエストを表す JSON エンコード文字列。 |

**戻り値：** 成功時は `Ok(request)`、パース/バリデーション失敗時は `Err(exception)`。

```python
>>> JsonRpcRequest.try_from_json('{"method":"add","id":1}').is_ok()
True
```

#### `to_dict() -> dict[str, Any]`

リクエストをプレーンな辞書にシリアライズします。`params` が `None` の場合、`params` キーは省略されます。

**戻り値：** JSON シリアライズに適した辞書。

```python
>>> JsonRpcRequest(method="add", params=[1, 2]).to_dict()
{'method': 'add', 'id': '<uuid>', 'params': [1, 2], 'jsonrpc': '2.0'}
```

#### `to_json() -> str`

リクエストを JSON 文字列にシリアライズします。

**戻り値：** このリクエストのコンパクトな JSON 表現。

#### `into(result: Result[Any, JsonRpcError]) -> JsonRpcResponse`

ハンドラの結果から `JsonRpcResponse` を作成します。`Result`、`JsonRpcError`、または生の値を受け付けます。

| パラメータ | 型 | 説明 |
|---|---|---|
| `result` | `Result[Any, JsonRpcError]` | このリクエストを処理した結果。 |

**戻り値：** エラーを返すレスポンス。

```python
>>> from pyfplib import Result
>>> req = JsonRpcRequest(method="add", id=1)
>>> req.into(Result.ok(3))
JsonRpcResponse(id=1, result=3, error=None, ...)
```

---

## `JsonRpcNotification`

```python
class JsonRpcNotification(BaseModel)
```

JSON-RPC 2.0 通知オブジェクト。リクエストと同様ですが、`id` フィールドを省略しており、サーバーからのレスポンスが期待されないことを示します。

### 属性

| 属性 | 型 | デフォルト | 説明 |
|---|---|---|---|
| `method` | `str` | *（必須）* | 宣言されているイベントまたはプロシージャの名前。空でない文字列である必要があります。 |
| `params` | `JsonRpcParams` | `None` | オプションの位置付きまたは名前付き引数。 |
| `jsonrpc` | `JsonRpcVersion` | `Version2` | プロトコルバージョン。 |

::: warning
通知は `id` フィールドを**含んではいけません**。`id` を持つ通知を構築しようとすると、バリデーションエラーが発生します。
:::

### メソッド

#### `try_from_dict(data: dict) -> Result[JsonRpcNotification, Exception]` *(classmethod)*

プレーンな辞書から通知を構築しようします。

| パラメータ | 型 | 説明 |
|---|---|---|
| `data` | `dict[str, Any]` | JSON-RPC 通知フィールドを持つ辞書。 |

**戻り値：** 成功時は `Ok(notification)`、バリデーション失敗時は `Err(exception)`。

#### `try_from_json(data: str) -> Result[JsonRpcNotification, Exception]` *(classmethod)*

JSON 文字列から通知を構築しようします。

| パラメータ | 型 | 説明 |
|---|---|---|
| `data` | `str` | 通知を表す JSON エンコード文字列。 |

**戻り値：** 成功時は `Ok(notification)`、パース/バリデーション失敗時は `Err(exception)`。

#### `to_dict() -> dict[str, Any]`

通知をプレーンな辞書にシリアライズします。`params` が `None` の場合、`params` キーは省略されます。

**戻り値：** JSON シリアライズに適した辞書。

#### `to_json() -> str`

通知を JSON 文字列にシリアライズします。

**戻り値：** この通知のコンパクトな JSON 表現。

---

## `JsonRpcResponse`

```python
class JsonRpcResponse(BaseModel)
```

JSON-RPC 2.0 レスポンスオブジェクト。`result` と `error` の**いずれか一方のみ**が設定される必要があります。`id` は元のリクエストの `id` と一致します。

### 属性

| 属性 | 型 | デフォルト | 説明 |
|---|---|---|---|
| `id` | `JsonRpcId` | *（必須）* | このレスポンスが対応するリクエストの識別子。 |
| `result` | `Any` | `None` | メソッドが正常に実行された場合の戻り値。 |
| `error` | `JsonRpcError \| None` | `None` | メソッドが失敗した場合の `JsonRpcError`。 |
| `jsonrpc` | `JsonRpcVersion` | `Version2` | プロトコルバージョン。 |

::: warning
レスポンスは `result` と `error` の**いずれか一方**のみ持つ必要があります。両方同時には持てません。両方を設定しようとすると、バリデーションエラーが発生します。
:::

### メソッド

#### `from_result(id, result) -> JsonRpcResponse` *(static)*

`Result` からレスポンスを構築します。

| パラメータ | 型 | 説明 |
|---|---|---|
| `id` | `JsonRpcId` | エコーバックするリクエスト識別子。 |
| `result` | `Result[Any, JsonRpcError]` | ハンドラの結果。 |

**戻り値：** 完全に構築された `JsonRpcResponse`。

```python
>>> from pyfplib import Result
>>> JsonRpcResponse.from_result(1, Result.ok("data"))
JsonRpcResponse(id=1, result='data', error=None, ...)
>>> JsonRpcResponse.from_result(2, Result.err(JsonRpcError(code=JsonRpcErrorCode.InternalError)))
JsonRpcResponse(id=2, result=None, error=JsonRpcError(...), ...)
```

#### `from_jrpc_error(id, error) -> JsonRpcResponse` *(static)*

エラーレスポンスを構築します。

| パラメータ | 型 | 説明 |
|---|---|---|
| `id` | `JsonRpcId` | エコーバックするリクエスト識別子。 |
| `error` | `JsonRpcError` | 含めるエラー。 |

**戻り値：** `error` のみが設定された `JsonRpcResponse`。

#### `from_jrpc_result(id, result) -> JsonRpcResponse` *(static)*

成功レスポンスを構築します。

| パラメータ | 型 | 説明 |
|---|---|---|
| `id` | `JsonRpcId` | エコーバックするリクエスト識別子。 |
| `result` | `Any` | メソッドの戻り値。 |

**戻り値：** `result` のみが設定された `JsonRpcResponse`。

#### `try_from_dict(data: dict) -> Result[JsonRpcResponse, Exception]` *(static)*

プレーンな辞書からレスポンスを構築しようします。

| パラメータ | 型 | 説明 |
|---|---|---|
| `data` | `dict[str, Any]` | JSON-RPC レスポンスフィールドを持つ辞書。 |

**戻り値：** 成功時は `Ok(response)`、バリデーション失敗時は `Err(exception)`。

#### `try_from_json(data: str) -> Result[JsonRpcResponse, Exception]` *(static)*

JSON 文字列からレスポンスを構築しようします。

| パラメータ | 型 | 説明 |
|---|---|---|
| `data` | `str` | レスポンスを表す JSON エンコード文字列。 |

**戻り値：** 成功時は `Ok(response)`、パース/バリデーション失敗時は `Err(exception)`。

#### `to_dict() -> dict[str, Any]`

レスポンスをプレーンな辞書にシリアライズします。`error` が存在する場合、`result` キーは削除され、エラーコードは `int` に変換されます。`result` が存在する場合、`error` キーは削除されます。

**戻り値：** JSON シリアライズに適した辞書。

#### `to_json() -> str`

レスポンスを JSON 文字列にシリアライズします。

**戻り値：** このレスポンスのコンパクトな JSON 表現。

---

## `try_parse()`

```python
def try_parse(data: str) -> Result[JsonRpcRequest | JsonRpcNotification, JsonRpcError]
```

JSON 文字列を JSON-RPC メッセージとしてパースしようします。関数はまず `JsonRpcRequest` としてパースを試み、失敗した場合は `JsonRpcNotification` にフォールバックします。両方が失敗した場合、リクエストの試行からのパースエラーが返されます。

| パラメータ | 型 | 説明 |
|---|---|---|
| `data` | `str` | JSON エンコード文字列。 |

**戻り値：** 成功時は `Ok(request | notification)`、パース失敗を含む `Err(JsonRpcError)`。

::: warning
`JsonRpcRequest` は `id` を `uuid4()` でデフォルト設定するため、通知ペイロード（`id` なし）はリクエストとして成功します。通知形式を強制する場合は `JsonRpcNotification.try_from_json` を直接使用してください。
:::

```python
>>> try_parse('{"jsonrpc":"2.0","method":"add","id":1}')
Result.ok(JsonRpcRequest(method='add', id=1, ...))
```
