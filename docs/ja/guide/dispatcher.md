# ディスパッチャ API

ディスパッチャレイヤーは `jrpc_core.dispatcher` モジュールにあります。

```python
from jrpc_core.dispatcher import (
    JsonRpcDispatcher,
    JsonRpcMethodWrapper,
    JsonRpcHandlerCollection,
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
    validators: list[Callable[..., Option[JsonRpcError]]] | None = None,
)
```

| パラメータ | 型 | デフォルト | 説明 |
|---|---|---|---|
| `name` | `str` | *（必須）* | JSON-RPC メソッド名。 |
| `method` | `Callable[..., Any]` | *（必須）* | このメソッドがディスパッチされたときに呼び出されるコール可能な関数。 |
| `validators` | `list[Callable[..., Option[JsonRpcError]]] \| None` | `None` | パラメータのパラメータを解析し、拒否シグナルを返すコール可能な関数のオプションリスト。 |

### バリデータプロトコル

各バリデータはパラメータのパラメータを解析し、以下を返すことができます：

| 戻り値 | 動作 |
|---|---|
| `Some(JsonRpcError)` または `Some(Exception)` | `InvalidParams` でラップされたそのエラーで拒否 |
| `False` | 汎用の `InvalidParams` エラーで拒否 |
| `Exception` または `JsonRpcError` | そのエラーで直接拒否 |
| `True`、`None`、またはその他の真値 | 承認 — 次のバリデータまたはメソッド呼び出しに進む |

### 属性

| 属性 | 型 | 説明 |
|---|---|---|
| `name` | `str` | このラッパーが登録されている JSON-RPC メソッド名。 |

### メソッド

#### `__hash__() -> int`

メソッド名に基づいたハッシュを返します。同じ名前の2つのラッパーは同じハッシュを持ちます。

#### `__eq__(other) -> bool`

メソッド名で2つのラッパーを比較します。

#### `__call__(args: Option[Any]) -> Result[Any, JsonRpcError]`

オプションのパラメータ付きでラップされたメソッドを実行します。バリデータはメソッドの前に実行されます。バリデータがパラメータを拒否した場合、呼び出しは `Err` で短絡されます。

| パラメータ | 型 | 説明 |
|---|---|---|
| `args` | `Option[Any]` | メソッドパラメータを含む `Option`。`Some` はパラメータが提供されたことを意味し、`None` はパラメータがないことを意味します。 |

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
JsonRpcDispatcher()
```

空のハンドラレジストリでディスパッチャを初期化します。

### 属性

| 属性 | 型 | 説明 |
|---|---|---|
| `request_handler_registry` | `JsonRpcHandlerCollection` | リクエストハンドラのレジストリ。 |
| `notification_handler_registry` | `JsonRpcHandlerCollection` | 通知ハンドラのレジストリ。 |

### メソッド

#### `__call__(data: str | JsonRpcRequest | JsonRpcNotification) -> Option[Result[JsonRpcResponse, JsonRpcError]]`

JSON-RPC メッセージをディスパッチします。

| パラメータ | 型 | 説明 |
|---|---|---|
| `data` | `str \| JsonRpcRequest \| JsonRpcNotification` | JSON 文字列、`JsonRpcRequest`、または `JsonRpcNotification`。 |

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

#### `try_parse(data: str) -> Result[JsonRpcRequest | JsonRpcNotification, JsonRpcError]` *(classmethod)*

JSON 文字列をリクエストまたは通知にパースしようします。まず `JsonRpcRequest` を試み、失敗した場合は `JsonRpcNotification` にフォールバックします。

| パラメータ | 型 | 説明 |
|---|---|---|
| `data` | `str` | JSON エンコード文字列。 |

**戻り値：** 成功時は `Ok(request | notification)`、パース失敗時は `Err(JsonRpcError)`。
