# PKGシステム完全設計書
## 関数型DAGアーキテクチャによる階層的取引信号処理システム

### 1. システム概要

PKGシステムは、2700以上の生データ記号を基に、関数型DAGアーキテクチャで階層的に取引信号を生成するシステムです。各PKG IDは基本関数の組み合わせによる複合関数として定義され、生データ記号から段階的に高度な判断を構築します。

### 2. 生データ記号体系

#### 2.1 記号の種類（list.txt）
```
総数: 2700以上の記号

主要カテゴリ:
- 0ZZ002～0ZZ004: システム予約
- AA001～AA329: 基本価格データ
- AB301～AD312: 派生価格データ
- Asa～Asw: 時間足別データ（a=M1, b=M5, c=M15...）
- BA～BB: ボリューム・出来高データ
- CA001～CA142: 計算済み指標
- SU～SV: 統計データ
- ZA～ZB: 集計データ
```

#### 2.2 記号の命名規則
```
[カテゴリ][サブカテゴリ][連番]

例:
AA001: 基本価格(A) サブセットA 連番001
Asa003: 時系列(As) 1分足(a) 連番003
BA018: ボリューム(B) サブセットA 連番018
```

### 3. PKG ID体系

#### 3.1 ID構造
```
形式: [時間足][周期][通貨]^[階層]-[連番]
例: 191^2-126

構成要素:
- 時間足（1桁目）: 1=M1, 2=M5, 3=M15, 4=M30, 5=H1, 6=H4
- 周期（2-3桁目）: 09=共通, 10/15/30/45/60/90/180=TSML周期
- 通貨（4桁目）: 1=USDJPY, 2=EURUSD, 3=EURJPY
- 階層（^後）: 依存関係の深さ
- 連番（-後）: 同一階層内の識別番号
```

#### 3.2 階層ルール
```
階層1: 生データ記号のみ参照（他PKG参照不可）
階層2: 階層1のPKG結果を参照可能
階層3: 階層1,2のPKG結果を参照可能
階層n: 階層1～(n-1)のPKG結果を参照可能
```

### 4. 基本関数体系

#### 4.1 算術演算関数
```javascript
Z(n, param1, param2, ..., paramN)
// n: パラメータ数（2, 8など）
// 用途: 加減乗除、複雑な算術演算

例:
Z(2, AA001, AA002)  // AA001 - AA002
Z(8, a, b, c, d, e, f, g, h)  // 8項演算
```

#### 4.2 選択・論理関数
```javascript
SL(condition, true_value, false_value)  // 条件選択
OR(a, b)   // 論理和
AND(a, b)  // 論理積

例:
SL(AA001 > 110.0, 1, 0)  // 価格が110円超なら1
AND(191^1-1, 191^1-2)    // 2つのPKG結果のAND
```

#### 4.3 集計・統計関数
```javascript
CO(array)  // カウント（条件を満たす要素数）
SG(array)  // 合計
AS(array)  // 平均
MN(array)  // 最小値

例:
MN([AA001, AA002, AA003])  // 3つの値の最小
CO([191^1-1, 191^1-2, 191^1-3])  // 真の個数
```

### 5. PKG関数の実装構造

#### 5.1 階層1の例（生データのみ使用）
```javascript
// 191^1-1: 価格差分判定
191^1-1 = SL(
    Z(2, AA001, AA002) > 0.003,  // AA001-AA002が0.3%超
    1,   // 上昇
    SL(
        Z(2, AA001, AA002) < -0.003,  // -0.3%未満
        -1,  // 下降
        0    // 中立
    )
)

// 191^1-2: ボリューム判定
191^1-2 = SL(
    BA018 > AS([BA015, BA016, BA017]),  // 現在ボリュームが平均超
    1,
    0
)

// 191^1-3: レンジ判定
191^1-3 = SL(
    Z(2, CA001, CA002) < 0.003,  // 高値-安値が3pips未満
    1,  // もみ状態
    0
)
```

#### 5.2 階層2の例（階層1を参照）
```javascript
// 191^2-1: 複合条件判定
191^2-1 = AND(
    191^1-1,  // 価格差分判定
    191^1-2   // ボリューム判定
)

// 191^2-2: 複合演算（重み付きではない）
191^2-2 = Z(8,
    191^1-1,    // 価格判定結果
    191^1-2,    // ボリューム判定結果
    191^1-3,    // レンジ判定結果
    AA010,      // 追加の生データ（階層2でも生データ参照可能）
    0, 0, 0, 0  // パディング
)
```

#### 5.3 階層3の例（複数階層を参照）
```javascript
// 191^3-1: 最終判断
191^3-1 = SL(
    CO([191^2-1, 191^2-2]) >= 1,  // 階層2の条件が1つ以上成立
    SL(
        AND(191^2-1, 191^1-3),  // 複合条件ANDレンジ判定
        2,   // 強い買いシグナル
        1    // 通常買いシグナル
    ),
    SL(
        191^1-3,  // レンジ判定のみ
        0,        // 待機
        -1        // 売りシグナル
    )
)
```

### 6. DAG実行アーキテクチャ

#### 6.1 実行フロー
```mermaid
graph TD
    A[生データ記号<br/>AA001, BA018, CA001...] 
    
    A --> B1[階層1: PKG関数群<br/>生データのみ参照]
    B1 --> B1_1[191^1-1<br/>Z,SL使用]
    B1 --> B1_2[191^1-2<br/>SL,AS使用]
    B1 --> B1_3[191^1-3<br/>Z,SL使用]
    
    B1_1 --> C1[階層2: PKG関数群<br/>階層1を参照]
    B1_2 --> C1
    B1_3 --> C1
    C1 --> C1_1[191^2-1<br/>AND使用]
    C1 --> C1_2[191^2-2<br/>Z(8)使用]
    
    C1_1 --> D1[階層3: PKG関数群<br/>階層1,2を参照]
    C1_2 --> D1
    B1_3 --> D1
    D1 --> D1_1[191^3-1<br/>最終判断]
    
    D1_1 --> E[取引シグナル出力]
```

#### 6.2 実行順序の保証
```python
class PKGExecutor:
    def execute(self, market_data):
        # 生データ記号を読み込み
        raw_data = self.load_raw_symbols(market_data)
        context = {'raw': raw_data}
        
        # 階層順に実行
        max_layer = self.get_max_layer()
        for layer in range(1, max_layer + 1):
            # 同一階層は並列実行可能
            layer_pkgs = self.get_pkgs_by_layer(layer)
            results = parallel_execute(layer_pkgs, context)
            
            # 結果をコンテキストに保存
            for pkg_id, result in results.items():
                context[pkg_id] = result
                
        return context
```

### 7. パラメータ管理（initial_setting_list_os.xlsx）

#### 7.1 記号定義シート
| 記号 | 説明 | データソース | 更新頻度 |
|------|------|-------------|----------|
| AA001 | USDJPY現在価格 | OANDA | リアルタイム |
| AA002 | USDJPY前足終値 | OANDA | 足確定時 |
| BA018 | 現在足出来高 | OANDA | リアルタイム |
| CA001 | 現在足高値 | 計算値 | リアルタイム |

#### 7.2 PKG関数定義シート
| PKG ID | 関数式 | 依存記号/PKG | 説明 |
|--------|--------|--------------|------|
| 191^1-1 | SL(Z(2,AA001,AA002)>0.003,1,SL(Z(2,AA001,AA002)<-0.003,-1,0)) | AA001,AA002 | 価格差分判定 |
| 191^2-1 | AND(191^1-1,191^1-2) | 191^1-1,191^1-2 | 複合条件 |

#### 7.3 パラメータ設定シート
| パラメータ名 | 値 | 単位 | 説明 |
|-------------|-----|------|------|
| RANGE_THRESHOLD | 0.003 | 比率 | レンジ判定閾値 |
| VOLUME_MA_PERIOD | 20 | 本 | 出来高移動平均期間 |

### 8. 実装クラス設計

#### 8.1 生データ管理
```python
class RawSymbolManager:
    """生データ記号の管理"""
    
    def __init__(self, symbol_list_path: str):
        self.symbols = self._load_symbols(symbol_list_path)
        self.cache = {}
        
    def get_value(self, symbol: str, context: Dict) -> float:
        """記号の値を取得"""
        if symbol in self.cache:
            return self.cache[symbol]
            
        # データソースから取得
        value = self._fetch_from_source(symbol, context)
        self.cache[symbol] = value
        return value
```

#### 8.2 関数評価エンジン
```python
class FunctionEvaluator:
    """基本関数の評価"""
    
    def evaluate(self, func_name: str, args: List, context: Dict) -> float:
        """関数を評価"""
        if func_name == 'Z':
            return self._evaluate_z(args)
        elif func_name == 'SL':
            return self._evaluate_sl(args[0], args[1], args[2])
        elif func_name == 'AND':
            return self._evaluate_and(args[0], args[1])
        elif func_name == 'OR':
            return self._evaluate_or(args[0], args[1])
        elif func_name == 'MN':
            return min(args)
        elif func_name == 'CO':
            return sum(1 for x in args if x)
        # ... 他の関数
```

#### 8.3 PKG関数定義
```python
@dataclass
class PKGFunction:
    """PKG関数の定義"""
    pkg_id: str
    layer: int
    formula: str  # "SL(Z(2,AA001,AA002)>0.003,1,0)"
    dependencies: List[str]  # ["AA001", "AA002"] or ["191^1-1"]
    
    def execute(self, context: Dict, evaluator: FunctionEvaluator) -> float:
        """関数を実行"""
        # 依存データを収集
        dep_values = {}
        for dep in self.dependencies:
            if '^' in dep:  # PKG ID
                dep_values[dep] = context.get(dep, 0)
            else:  # 生データ記号
                dep_values[dep] = context['raw'].get(dep, 0)
                
        # 式を評価（パーサー実装が必要）
        return self._evaluate_formula(self.formula, dep_values, evaluator)
```

#### 8.4 DAG実行マネージャー
```python
class PKGDAGManager:
    """PKG関数のDAG実行管理"""
    
    def __init__(self, config_path: str):
        self.symbol_manager = RawSymbolManager('list.txt')
        self.evaluator = FunctionEvaluator()
        self.pkg_functions = self._load_pkg_definitions(config_path)
        self.execution_layers = self._organize_by_layer()
        
    def execute(self, market_data: Dict) -> Dict:
        """全PKG関数を階層順に実行"""
        # 生データ読み込み
        raw_data = self.symbol_manager.load_all(market_data)
        context = {'raw': raw_data}
        
        # 階層順実行
        for layer in sorted(self.execution_layers.keys()):
            # 同一階層は並列実行
            tasks = []
            for pkg_func in self.execution_layers[layer]:
                tasks.append(self._execute_pkg(pkg_func, context))
                
            # 結果収集
            results = asyncio.gather(*tasks)
            for pkg_func, result in zip(self.execution_layers[layer], results):
                context[pkg_func.pkg_id] = result
                
        return context
```

### 9. パフォーマンス最適化

#### 9.1 キャッシング戦略
```python
class CacheStrategy:
    """階層別キャッシュ戦略"""
    
    CACHE_TTL = {
        1: 1.0,    # 階層1: 1秒
        2: 5.0,    # 階層2: 5秒
        3: 10.0,   # 階層3: 10秒
    }
    
    def should_cache(self, pkg_id: str) -> bool:
        layer = self._extract_layer(pkg_id)
        return layer <= 3  # 階層3以下はキャッシュ
```

#### 9.2 並列実行
```python
async def parallel_execute_layer(layer_pkgs: List[PKGFunction], context: Dict):
    """同一階層の並列実行"""
    tasks = []
    for pkg in layer_pkgs:
        tasks.append(asyncio.create_task(
            pkg.execute_async(context)
        ))
    
    return await asyncio.gather(*tasks)
```

### 10. テスト戦略

#### 10.1 単体テスト
```python
def test_layer1_function():
    """階層1関数のテスト"""
    context = {
        'raw': {
            'AA001': 110.50,
            'AA002': 110.00,
        }
    }
    
    pkg = PKGFunction(
        pkg_id='191^1-1',
        layer=1,
        formula='SL(Z(2,AA001,AA002)>0.003,1,0)',
        dependencies=['AA001', 'AA002']
    )
    
    result = pkg.execute(context, FunctionEvaluator())
    assert result == 1  # 0.5/110 > 0.003
```

#### 10.2 統合テスト
```python
def test_dag_execution():
    """DAG全体の実行テスト"""
    manager = PKGDAGManager('initial_setting_list_os.xlsx')
    
    market_data = {
        'USDJPY': {'bid': 110.50, 'ask': 110.51},
        'volume': 1000
    }
    
    result = manager.execute(market_data)
    
    # 各階層の結果を検証
    assert '191^1-1' in result  # 階層1
    assert '191^2-1' in result  # 階層2
    assert '191^3-1' in result  # 階層3
    
    # 最終シグナル確認
    final_signal = result['191^3-1']
    assert final_signal in [-1, 0, 1, 2]
```

### 11. メモファイル記載の実行時間目標

| 処理 | 目標時間 | 実測値 | 達成状況 |
|------|----------|--------|----------|
| 全体システム | 19ms | - | - |
| もみ判定 | 77ms | - | - |
| OP分岐 | 101.3ms | - | - |
| オーバーシュート | 550.6ms | - | - |
| 時間結合 | 564.9ms | - | - |

### 12. まとめ

PKGシステムは、2700以上の生データ記号を基に、関数型DAGアーキテクチャで階層的に処理を行います：

1. **生データ記号（AA001等）** → 市場データの基本要素
2. **階層1 PKG** → 生データのみから基本判定
3. **階層2 PKG** → 階層1の結果を組み合わせ
4. **階層3+ PKG** → より高度な統合判断
5. **最終シグナル** → 取引実行判断

このアーキテクチャにより、97個のメモファイルに記載された取引ロジックを、体系的かつ高速に処理することが可能になります。