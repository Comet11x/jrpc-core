# ディスパッチャ API

ディスパッチャレイヤーは `jrpc_core.dispatcher` モジュールにあります。

```python
from jrpc_core.dispatcher import (
    JsonRpcDispatcher,
    JsonRpcMethodWrapper,
    JsonRpcHandlerCollection,
    JsonRpcResponseCtorWrapper,
)
```

---

## `JsonRpcMethodWrapper`

```python
class JsonRpcMethodWrapper
```

コール可能なものを、オプションのパラメータバリデータを持つ JSON-RPC メソッドとしてラップします。

### コンストラクタ

```python
JsonRpcMethodWrapper(
    *,
    name: str,
    method: Callable[..., Any],
    validator: Callable[..., Option[JsonRpcError] | bool] | None = None,
    converter: Callable[..., Option[Any] | Result[Any, Exception | JsonRpcError] | Any] | None = None,
)
```

| パラメータ | 型 | デフォルト | 説明 |
|---|---|---|---|
| `name` | `str` | *（必須）* | JSON-RPC メソッド名。 |
| `method` | `Callable[..., Any]` | *（必須）* | このメソッドがディスパッチされたときに呼び出されるコール可能な関数。 |
| `validator` | `Callable[..., Option[JsonRpcError] \| bool] \| None` | `None` | 解析済みの `params` を受け取り、拒否シグナルを返すオプションのコール可能な関数。 |
| `converter` | `Callable[..., Option[Any] \| Result[Any, Exception \| JsonRpcError] \| Any] \| None` | `None` | メソッドが呼び出される前にパラメータを変換するオプションのコール可能な関数。 |

### バリデータプロトコル

各バリデータはパラメータのパラメータを解析し、以下を返すことができます：

| 戻り値 | 動作 |
|---|---|
| `Some(JsonRpcError)` または `Some(Exception)` | `InvalidParams` でラップされたそのエラーで拒否 |
| `False` | 汎用の `InvalidParams` エラーで拒否 |
| `Exception` または `JsonRpcError` | そのエラーで直接拒否 |
| `True`、`None`、またはその他の真値 | 承認 — 次のバリデータまたはメソッド呼び出しに進む |

### コンバータプロトコル

コンバータは生の `params` ペイロードを受け取り、以下を返すことができます：

| 戻り値 | 動作 |
|---|---|
| `Some(value)` | `value` をメソッド引数として使用 |
| `Nothing()` | `ConversionError` で拒否 |
| `Ok(value)` | `value` をメソッド引数として使用 |
| `Err(reason)` | `ConversionError` で拒否し、`reason` を `data` に添付 |
| その他の値 | その値を直接メソッド引数として使用 |
| `Exception` を送出 | `ConversionError` で拒否し、例外を `data` に添付 |

### 属性

| 属性 | 型 | 説明 |
|---|---|---|
| `name` | `str` | このラッパーが登録されている JSON-RPC メソッド名。 |

### メソッド

#### `__hash__() -> int`

メソッド名に基づいたハッシュを返します。同じ名前の2つのラッパーは同じハッシュを持ちます。

#### `__eq__(other) -> bool`

メソッド名で2つのラッパーを比較します。

#### `__call__(params: Option[Any]) -> Result[Any, JsonRpcError]`

オプションのパラメータ付きでラップされたメソッドを実行します。バリデーションが最初に実行され、次にコンバータが実行されます。どちらのステップでもパラメータが拒否された場合、呼び出しは `Err` で短絡されます。

| パラメータ | 型 | 説明 |
|---|---|---|
| `params` | `Option[Any]` | メソッドパラメータを含む `Option`。`Some` はパラメータが提供されたことを意味し、`Nothing` はパラメータがないことを意味します。 |

**戻り値：** 成功時は `Ok(result)`、失敗時は `Err(JsonRpcError)`。

```python
>>> from pyfplib import Some, Nothing, Result
>>> wrapper = JsonRpcMethodWrapper(name="add", method=lambda a: a[0] + a[1])
>>> wrapper(Some([1, 2]))
Result.ok(3)
>>> wrapper(Nothing())
Result.ok(...)  # 引数なしでメソッドを呼び出す
```

---

## `JsonRpcHandlerCollection`

```python
class JsonRpcHandlerCollection
```

メソッド名をキーとする `JsonRpcMethodWrapper` インスタンスのレジストリ。

### コンストラクタ

```python
JsonRpcHandlerCollection()
```

空のハンドラコレクションを初期化します。

### メソッド

#### `add(method: JsonRpcMethodWrapper) -> bool`

メソッドラッパーを登録します。同じ名前のメソッドがすでに存在する場合、呼び出しは何もしません。

| パラメータ | 型 | 説明 |
|---|---|---|
| `method` | `JsonRpcMethodWrapper` | 登録するラッパー。 |

**戻り値：** メソッドが新規に登録された場合は `True`、すでに存在した場合は `False`。

```python
>>> collection = JsonRpcHandlerCollection()
>>> wrapper = JsonRpcMethodWrapper(name="add", method=lambda a: a)
>>> collection.add(wrapper)
True
>>> collection.add(wrapper)  # 重複
False
```

#### `try_get(name: str) -> Option[JsonRpcMethodWrapper]`

名前でメソッドを検索します。

| パラメータ | 型 | 説明 |
|---|---|---|
| `name` | `str` | JSON-RPC メソッド名。 |

**戻り値：** 見つかった場合は `Some(wrapper)`、それ以外は `Nothing`。

#### `exists(name: str) -> bool`

メソッドが登録されているかどうかを確認します。

| パラメータ | 型 | 説明 |
|---|---|---|
| `name` | `str` | JSON-RPC メソッド名。 |

**戻り値：** その名前のラッパーが存在する場合は `True`。

#### `remove_by_name(name: str) -> bool`

名前でメソッドを削除します。

| パラメータ | 型 | 説明 |
|---|---|---|
| `name` | `str` | 削除する JSON-RPC メソッド名。 |

**戻り値：** メソッドが存在して削除された場合は `True`、それ以外は `False`。

#### `remove(method: str | JsonRpcMethodWrapper) -> bool`

名前またはラッパーインスタンスでメソッドを削除します。

| パラメータ | 型 | 説明 |
|---|---|---|
| `method` | `str \| JsonRpcMethodWrapper` | メソッド名の文字列または `JsonRpcMethodWrapper`。 |

**戻り値：** メソッドが存在して削除された場合は `True`、それ以外は `False`。

```python
>>> collection = JsonRpcHandlerCollection()
>>> wrapper = JsonRpcMethodWrapper(name="add", method=lambda a: a)
>>> collection.add(wrapper)
True
>>> collection.remove("add")
True
>>> collection.remove("add")
False
```

---

## `JsonRpcDispatcher`

```python
class JsonRpcDispatcher
```

受信 JSON-RPC メッセージを登録されたハンドラにルーティングします。レスポンスを期待するリクエストと、ファイアアンドフォーゲットの通知の別々のレジストリを維持します。

### コンストラクタ

```python
JsonRpcDispatcher(
    response_handler: Callable[[JsonRpcResponse], None] | None = None,
)
```

| パラメータ | 型 | デフォルト | 説明 |
|---|---|---|---|
| `response_handler` | `Callable[[JsonRpcResponse], None] \| None` | `None` | `JsonRpcResponse` が直接ディスパッチされたときに呼び出されるオプションのコールバック。 |

### クラス属性

| 属性 | 型 | 説明 |
|---|---|---|
| `ERROR_CASE` | `JsonRpcResponseCtorWrapper.State` | エラーレスポンスの結果セレクタ。 |
| `RESULT_CASE` | `JsonRpcResponseCtorWrapper.State` | 成功結果の結果セレクタ。 |
| `BOTH_CASES` | `JsonRpcResponseCtorWrapper._When` | 両方の結果に一致する結果セレクタ。 |

### 属性

| 属性 | 型 | 説明 |
|---|---|---|
| `request_handler_registry` | `JsonRpcHandlerCollection` | リクエストハンドラのレジストリ。 |
| `notification_handler_registry` | `JsonRpcHandlerCollection` | 通知ハンドラのレジストリ。 |

### メソッド

#### `emplace_request_handler(*, name, method, validator=None, converter=None) -> bool`

リクエストハンドラを1つの呼び出しで登録します。`request_handler_registry.add(JsonRpcMethodWrapper(...))` の便利なラッパーです。

| パラメータ | 型 | デフォルト | 説明 |
|---|---|---|---|
| `name` | `str` | *（必須）* | JSON-RPC メソッド名。 |
| `method` | `Callable[..., Any]` | *（必須）* | ディスパッチされたときに呼び出されるコール可能な関数。 |
| `validator` | `Callable[..., Option[JsonRpcError] \| bool] \| None` | `None` | オプションのパラメータバリデータ。 |
| `converter` | `Callable[..., Option[Any] \| Result[Any, Exception \| JsonRpcError] \| Any] \| None` | `None` | オプションのパラメータコンバータ。 |

**戻り値：** 新規に登録された場合は `True`、名前がすでに存在する場合は `False`。

#### `emplace_notification_handler(*, name, method, validator=None, converter=None) -> bool`

通知ハンドラを1つの呼び出しで登録します。`notification_handler_registry.add(JsonRpcMethodWrapper(...))` の便利なラッパーです。

| パラメータ | 型 | デフォルト | 説明 |
|---|---|---|---|
| `name` | `str` | *（必須）* | JSON-RPC メソッド名。 |
| `method` | `Callable[..., Any]` | *（必須）* | ディスパッチされたときに呼び出されるコール可能な関数。 |
| `validator` | `Callable[..., Option[JsonRpcError] \| bool] \| None` | `None` | オプションのパラメータバリデータ。 |
| `converter` | `Callable[..., Option[Any] \| Result[Any, Exception \| JsonRpcError] \| Any] \| None` | `None` | オプションのパラメータコンバータ。 |

**戻り値：** 新規に登録された場合は `True`、名前がすでに存在する場合は `False`。

#### `emplace_custom_response_ctor(method, ctor, *states)`

メソッドにカスタムレスポンスコンストラクタを登録します。

| パラメータ | 型 | 説明 |
|---|---|---|
| `method` | `str` | コンストラクタが適用される JSON-RPC メソッド名。 |
| `ctor` | `Callable[..., JsonRpcResponse]` | `JsonRpcResponse` を構築するコール可能な関数。 |
| `*states` | `JsonRpcResponseCtorWrapper.State` | コンストラクタが使用される状態を制限するオプションのステータスメンバー。 |

#### `add_custom_response_ctor(ctor: JsonRpcResponseCtorWrapper)`

事前に構築されたカスタムレスポンスコンストラクタを登録します。同じメソッドに以前に登録されたコンストラクタを置き換えます。

| パラメータ | 型 | 説明 |
|---|---|---|
| `ctor` | `JsonRpcResponseCtorWrapper` | コンストラクタをメソッド名にバインドするラッパー。 |

#### `__call__(data) -> Option[Result[JsonRpcResponse, JsonRpcError]]`

JSON-RPC メッセージをディスパッチします。

| パラメータ | 型 | 説明 |
|---|---|---|
| `data` | `str \| JsonRpcRequest \| JsonRpcNotification \| JsonRpcResponse \| Result[...]` | JSON 文字列、`JsonRpcRequest`、`JsonRpcNotification`、`JsonRpcResponse`、または `Result`。 |

**戻り値：**

| 入力 | ハンドラが見つかった | ハンドラが見つからない |
|---|---|---|
| `str`（パース成功） | リクエスト/通知処理に委譲 | — |
| `str`（パース失敗） | `Some(Err(ParseError))` | — |
| `JsonRpcRequest` | `Some(Ok(response))` | `Some(Err(MethodNotFound))` 経由レスポンス |
| `JsonRpcNotification` | `Nothing`（成功） | `Some(Err(MethodNotFound))` |
| 不明な型 | `Some(Err(InternalError))` | — |

```python
>>> from pyfplib import Some, Ok
>>> dispatcher = JsonRpcDispatcher()
>>> dispatcher.request_handler_registry.add(
...     JsonRpcMethodWrapper(name="add", method=lambda a: a[0] + a[1])
... )
True
>>> result = dispatcher(JsonRpcRequest(method="add", params=[1, 2], id=1))
>>> result.unwrap().unwrap().result
3
```

#### `try_parse(data: str) -> Result[JsonRpcResponse | JsonRpcNotification | JsonRpcRequest, JsonRpcError]` *(classmethod)*

JSON 文字列をレスポンス、リクエスト、または通知にパースしようします。まず `JsonRpcResponse` を試み、失敗した場合は `JsonRpcNotification` にフォールバックし、さらに失敗した場合は `JsonRpcRequest` にフォールバックします。

| パラメータ | 型 | 説明 |
|---|---|---|
| `data` | `str` | JSON エンコード文字列。 |

**戻り値：** 成功時は `Ok(response | notification | request)`、パース失敗時は `Err(JsonRpcError)`。

---

## `JsonRpcResponseCtorWrapper`

```python
class JsonRpcResponseCtorWrapper
```

カスタムの `JsonRpcResponse` コンストラクタをメソッド名にバインドします。ラッパーはコンストラクタがいつ適用されるかを記録します — 成功結果、エラー、または両方 — これによりディスパッチャは結果ごとに適切なレスポンスタイプを選択できます。

### コンストラクタ

```python
JsonRpcResponseCtorWrapper(
    method: str,
    ctor: Callable[..., JsonRpcResponse],
    *states: JsonRpcResponseCtorWrapper.State,
)
```

| パラメータ | 型 | デフォルト | 説明 |
|---|---|---|---|
| `method` | `str` | *（必須）* | このコンストラクタが適用される JSON-RPC メソッド名。 |
| `ctor` | `Callable[..., JsonRpcResponse]` | *（必須）* | キーワード引数（`id`、`result` または `error`、`jsonrpc`）を受け取り `JsonRpcResponse` を返すコール可能な関数。 |
| `*states` | `State` | 両方の結果 | コンストラクタが使用される場面を制限するオプションの `State` メンバー。 |

### 内部クラス: `State`

```python
class State(Enum)
```

コンストラクタが適用される場面を制御する結果セレクタ。

| メンバー | 値 | 説明 |
|---|---|---|
| `Result` | `1` | 成功結果を処理するコンストラクタ。 |
| `Error` | `2` | エラーレスポンスを処理するコンストラクタ。 |

### 属性

| 属性 | 型 | 説明 |
|---|---|---|
| `method` | `str` | このコンストラクタがバインドされている JSON-RPC メソッド名。 |
| `when` | `_When` | このコンストラクタの結果セレクタ。 |
