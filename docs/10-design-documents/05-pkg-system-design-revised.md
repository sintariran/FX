# PKGシステム設計書（改訂版）
## 関数型DAGアーキテクチャ詳細設計

### 1. システム概要

PKG（Package）システムは、97個のメモファイルに記載された取引ロジックを関数型DAGとして実装したシステムです。各PKG IDは基本関数の組み合わせによる複合関数として定義され、階層的な依存関係を持ちます。

### 2. PKG ID体系

```
形式: [時間足][周期][通貨]^[階層]-[連番]
例: 191^2-126
```

#### 2.1 構成要素
- **時間足（1桁目）**
  - 1: 1分足（M1）
  - 2: 5分足（M5）
  - 3: 15分足（M15）
  - 4: 30分足（M30）
  - 5: 1時間足（H1）
  - 6: 4時間足（H4）

- **周期（2-3桁目）**
  - 09: 共通（周期なし）
  - 10, 15, 30, 45, 60, 90, 180: TSML周期

- **通貨（4桁目）**
  - 1: USDJPY
  - 2: EURUSD
  - 3: EURJPY

- **階層（^の後）**
  - 1: 基本演算層
  - 2: 複合演算層
  - 3: 統合判断層

### 3. 基本関数体系

#### 3.1 算術演算関数
```javascript
Z(2, a, b)  // 2項演算: a - b, a + b, a * b, a / b
Z(8, a, b, c, d, e, f, g, h)  // 8項演算: 複雑な算術演算
```

#### 3.2 論理・選択関数
```javascript
SL(condition, true_value, false_value)  // 条件選択
OR(a, b)   // 論理和
AND(a, b)  // 論理積
```

#### 3.3 集計・統計関数
```javascript
CO(array)  // カウント集計
SG(array)  // 合計集計
AS(array)  // 平均集計
MN(array)  // 最小値選択
```

### 4. PKG関数の内部構造

#### 4.1 複合関数の定義例

```javascript
// PKG: 191^1-1（同逆判定）
191^1-1 = SL(
    Z(2, 前々足終値, 現在足終値) > 0.003,  // 条件: 乖離率0.3%超
    1,                                       // 真: 上方向（同）
    SL(
        Z(2, 前々足終値, 現在足終値) < -0.003,  // 条件: 乖離率-0.3%未満
        -1,                                      // 真: 下方向（逆）
        0                                        // 偽: 中立
    )
)

// PKG: 191^1-2（行帰判定）
191^1-2 = AND(
    SL(平均足転換点 > 基準線, 1, 0),       // 条件1: 転換点位置
    SL(前足方向 == 今足方向, 1, 0)         // 条件2: 方向継続性
)

// PKG: 191^1-3（もみ判定）
191^1-3 = SL(
    MN([高値1-安値1, 高値2-安値2, ..., 高値n-安値n]) < 0.003,  // 3pips未満
    1,  // もみ状態
    0   // 非もみ状態
)
```

#### 4.2 階層間の依存関係

```javascript
// 階層2: 複合演算（階層1の結果を利用）
191^2-1 = OR(
    AND(191^1-1, 191^1-2),  // 同逆判定AND行帰判定
    191^1-3                  // もみ判定
)

// 階層3: 最終判断（階層2の結果を統合）
191^3-1 = SL(
    CO([191^2-1, 191^2-2, 191^2-3]) >= 2,  // 2つ以上の条件成立
    1,   // 取引実行
    0    // 待機
)
```

### 5. DAG実行フロー

```mermaid
graph TD
    A[入力データ] --> B[基本データ処理]
    
    B --> C1[Z(2)演算]
    B --> C2[Z(8)演算]
    B --> C3[統計計算]
    
    C1 --> D1[SL選択]
    C2 --> D2[AND/OR論理]
    C3 --> D3[MN/AS集計]
    
    D1 --> E1[191^1-1<br/>同逆判定]
    D2 --> E2[191^1-2<br/>行帰判定]
    D3 --> E3[191^1-3<br/>もみ判定]
    
    E1 --> F1[191^2-1<br/>時間結合]
    E2 --> F1
    E3 --> F2[191^2-2<br/>トレンド分析]
    
    F1 --> G[191^3-1<br/>最終判断]
    F2 --> G
```

### 6. 実装アーキテクチャ

#### 6.1 関数評価エンジン

```python
class FunctionEvaluator:
    """基本関数の評価エンジン"""
    
    def Z(self, n: int, *args) -> float:
        """n項算術演算"""
        if n == 2:
            return args[0] - args[1]  # または他の演算
        elif n == 8:
            # 8項の複雑な演算
            return self._complex_arithmetic(*args)
    
    def SL(self, condition: bool, true_val: float, false_val: float) -> float:
        """条件選択"""
        return true_val if condition else false_val
    
    def AND(self, a: bool, b: bool) -> bool:
        """論理積"""
        return a and b
    
    def OR(self, a: bool, b: bool) -> bool:
        """論理和"""
        return a or b
    
    def MN(self, values: List[float]) -> float:
        """最小値選択"""
        return min(values)
```

#### 6.2 PKG関数定義

```python
class PKGFunction:
    """PKG関数の定義と実行"""
    
    def __init__(self, pkg_id: str, formula: str, dependencies: List[str]):
        self.pkg_id = pkg_id
        self.formula = formula  # 関数式の文字列表現
        self.dependencies = dependencies  # 依存するPKG ID
        self.cache = {}
        
    def execute(self, context: Dict, evaluator: FunctionEvaluator) -> float:
        """関数式を評価"""
        # 依存関数の結果を取得
        dep_results = {
            dep: context.get(dep) 
            for dep in self.dependencies
        }
        
        # 式を評価（実際にはパーサーが必要）
        return self._evaluate_formula(
            self.formula, 
            dep_results, 
            evaluator
        )
```

#### 6.3 DAG実行マネージャー

```python
class PKGDAGManager:
    """PKG関数のDAG実行管理"""
    
    def __init__(self):
        self.functions = {}  # pkg_id -> PKGFunction
        self.evaluator = FunctionEvaluator()
        self.execution_order = []  # トポロジカルソート結果
        
    def register_function(self, pkg_function: PKGFunction):
        """PKG関数を登録"""
        self.functions[pkg_function.pkg_id] = pkg_function
        self._update_execution_order()
        
    def execute(self, input_data: Dict) -> Dict:
        """DAG全体を実行"""
        context = {'input': input_data}
        
        # トポロジカル順序で実行
        for pkg_id in self.execution_order:
            func = self.functions[pkg_id]
            result = func.execute(context, self.evaluator)
            context[pkg_id] = result
            
        return context
    
    def _update_execution_order(self):
        """トポロジカルソートで実行順序を決定"""
        # 依存関係グラフから実行順序を計算
        pass
```

### 7. メモファイルから抽出した関数定義例

#### 7.1 同逆判定（勝率55.7%～56.1%）
```python
PKGFunction(
    pkg_id="191^1-1",
    formula="""
    SL(
        Z(2, input.前々足終値, input.現在足終値) > 0.003,
        1,
        SL(Z(2, input.前々足終値, input.現在足終値) < -0.003, -1, 0)
    )
    """,
    dependencies=[]
)
```

#### 7.2 もみ判定（レンジ3pips）
```python
PKGFunction(
    pkg_id="191^1-3",
    formula="""
    SL(
        MN([
            Z(2, input.高値1, input.安値1),
            Z(2, input.高値2, input.安値2),
            Z(2, input.高値3, input.安値3)
        ]) < 0.003,
        1,
        0
    )
    """,
    dependencies=[]
)
```

#### 7.3 時間結合（マルチタイムフレーム）
```python
PKGFunction(
    pkg_id="191^2-1",
    formula="""
    SL(
        AND(
            191^1-1,  # M1の同逆判定
            291^1-1   # M5の同逆判定
        ),
        SL(
            AND(391^1-1, 491^1-1),  # M15とM30も一致
            2,  # 強いシグナル
            1   # 通常シグナル
        ),
        0  # シグナルなし
    )
    """,
    dependencies=["191^1-1", "291^1-1", "391^1-1", "491^1-1"]
)
```

### 8. パフォーマンス目標

メモファイル記載の実行時間目標：

| 処理 | 目標時間 | 備考 |
|------|----------|------|
| 全体システム | 19ms | 全PKG関数の実行 |
| もみ判定 | 77ms | レンジ計算含む |
| OP分岐 | 101.3ms | 条件分岐処理 |
| オーバーシュート | 550.6ms | 複雑な残足計算 |
| 時間結合 | 564.9ms | 6時間足の統合 |

### 9. 実装上の注意点

1. **純粋関数として実装**
   - 副作用なし
   - 同じ入力に対して常に同じ出力

2. **キャッシング戦略**
   - 階層1の結果は積極的にキャッシュ
   - 時間足ごとにキャッシュ管理

3. **並列実行**
   - 依存関係のない関数は並列実行可能
   - asyncioを活用した非同期処理

4. **エラーハンドリング**
   - 各関数で例外を適切に処理
   - デフォルト値の設定

### 10. テスト戦略

```python
def test_pkg_function():
    """PKG関数のユニットテスト例"""
    
    # テストデータ
    input_data = {
        '前々足終値': 110.00,
        '現在足終値': 110.05,
        '高値1': 110.10,
        '安値1': 110.00
    }
    
    # PKG関数実行
    manager = PKGDAGManager()
    manager.register_function(dokyaku_function)  # 191^1-1
    
    result = manager.execute(input_data)
    
    # 検証
    assert result['191^1-1'] == 1  # 上方向判定
    assert execution_time < 19.0  # パフォーマンス目標
```

### 11. まとめ

PKGシステムは、基本関数（Z, SL, AND, OR等）を組み合わせた複合関数として各PKG IDを定義し、それらをDAG構造で実行する関数型アーキテクチャです。メモファイルの取引ロジックを忠実に実装し、高速実行を実現します。