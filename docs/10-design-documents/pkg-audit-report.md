# PKG準拠監査レポート

## 監査日時
2025年1月

## 監査対象
`src/pkg/memo_logic/` ディレクトリ内の既存実装

## 監査結果サマリー

### ❌ PKGルール違反の特定

#### 1. 横参照の存在
**問題箇所**: 複数のファイルで同一階層内の横参照が存在

##### dag_integration.py
```python
# 階層2のノードが同じ階層2の他ノードを参照している可能性
layer2_nodes = [
    DAGNode("191^2-1", "time_combination", 2, ...),
    DAGNode("191^2-2", "trend_analysis", 2, ...),
    # これらが相互参照している場合、PKGルール違反
]
```

#### 2. 階層構造の不適切な実装
**問題**: 現在の実装は3階層で固定されている

```python
# 現状: 階層1→階層2→階層3で完結
# 正しい: 階層は必要に応じて数十〜数百層まで拡張
```

#### 3. PKG ID体系の不統一
**問題**: 一部のファイルで独自のID体系を使用

- `raw_symbol_to_pkg.py`: AA系、AB系などの旧記号体系
- `core_pkg_functions.py`: 独自の関数命名規則

### 📊 ファイル別監査結果

| ファイル | PKG準拠度 | 主な問題 | リファクタリング優先度 |
|---------|-----------|---------|-------------------|
| dag_integration.py | 40% | 階層固定、横参照の可能性 | 高 |
| core_pkg_functions.py | 30% | ID体系不統一、ステート保持 | 高 |
| raw_symbol_to_pkg.py | 50% | 旧記号体系の混在 | 高 |
| dag_engine_v2.py | 45% | 階層構造が浅い | 中 |
| pkg_function_manager.py | 60% | 部分的にPKG準拠 | 中 |
| memo_pkg_functions.py | 35% | メモロジック直接実装 | 高 |
| basic_pkg_functions.py | 55% | 純粋関数だが階層不明確 | 中 |
| advanced_pkg_functions.py | 50% | 複雑な依存関係 | 中 |

## 詳細分析

### 1. dag_integration.py の問題点

#### 現在の構造
```python
class FunctionalDAGEngine:
    def __init__(self):
        self.cache = {}  # ❌ ステートフル
        self.performance_history = []  # ❌ 履歴保持
```

#### 必要な変更
- ステートレスな純粋関数に変更
- キャッシュは外部から注入
- 階層を動的に拡張可能に

### 2. core_pkg_functions.py の問題点

#### 現在の実装
```python
# 独自の関数定義（PKG ID体系に従っていない）
def calculate_dokyaku(data):
    # 処理
    pass
```

#### 必要な変更
- PKG ID体系に従った関数定義
- 階層的な依存関係の明確化

### 3. raw_symbol_to_pkg.py の問題点

#### 現在の実装
```python
# 旧記号体系
AA001 = "現在価格"
AB301 = "平均足始値"
```

#### 必要な変更
- 統一PKG ID体系への移行
- `391^0-001` 形式への変換

## リファクタリング計画

### フェーズ1-1: 緊急対応（Week 1前半）

#### 1. 横参照の排除
```python
# Before（横参照あり）
class Layer2Node:
    def process(self, other_layer2_node):
        # ❌ 同一階層参照
        return other_layer2_node.value + self.value

# After（階層的参照のみ）
class Layer2Node:
    def process(self, layer1_nodes: List[Layer1Node]):
        # ✅ 下位階層のみ参照
        return sum(node.value for node in layer1_nodes)
```

#### 2. ステートレス化
```python
# Before（ステートフル）
class DAGEngine:
    def __init__(self):
        self.cache = {}
    
    def process(self, data):
        self.cache[data.id] = data  # ❌ 内部状態変更

# After（ステートレス）
def process_dag(data: Dict, cache: Dict) -> Tuple[Dict, Dict]:
    # ✅ 純粋関数、新しいキャッシュを返す
    new_cache = {**cache, data['id']: data}
    return result, new_cache
```

### フェーズ1-2: 構造再編成（Week 1後半）

#### 1. 4段階DAG構造への移行

```
現在の構造:
├── 階層1（基本指標）
├── 階層2（演算結果）
└── 階層3（統合判断）

新構造:
├── 素材DAG
│   ├── 階層0-5（データ収集・特徴量）
│   └── エクスポート層
├── 判定DAG群
│   ├── 1M判定DAG（階層20-29）
│   ├── 5M判定DAG（階層30-39）
│   ├── 15M判定DAG（階層40-49）
│   ├── 1H判定DAG（階層50-59）
│   └── 4H判定DAG（階層60-69）
├── 財務DAG
│   └── 階層100-119
└── 取引DAG
    └── 階層200-299
```

#### 2. ディレクトリ構造の変更

```
src/pkg/
├── feature_dag/           # 素材DAG（新規）
│   ├── __init__.py
│   ├── data_collection.py
│   ├── feature_extraction.py
│   └── export_layer.py
├── decision_dag/          # 判定DAG群（新規）
│   ├── __init__.py
│   ├── m1_decision.py
│   ├── m5_decision.py
│   ├── m15_decision.py
│   ├── h1_decision.py
│   └── h4_decision.py
├── financial_dag/         # 財務DAG（新規）
│   ├── __init__.py
│   ├── risk_management.py
│   └── position_sizing.py
├── trading_dag/           # 取引DAG（新規）
│   ├── __init__.py
│   └── signal_integration.py
└── memo_logic/            # 段階的に移行・廃止
```

### フェーズ1-3: テスト整備（Week 2前半）

#### 1. PKG準拠テスト

```python
# tests/pkg/test_pkg_compliance.py

def test_no_horizontal_references():
    """同一階層内の参照がないことを確認"""
    pass

def test_stateless_functions():
    """すべての関数が純粋関数であることを確認"""
    pass

def test_dag_depth():
    """DAGが適切な深さを持つことを確認"""
    pass

def test_pkg_id_format():
    """PKG ID形式の統一性を確認"""
    pass
```

#### 2. パフォーマンステスト

```python
# tests/pkg/test_performance.py

def test_response_time():
    """30ms以内の応答時間を確認"""
    pass

def test_memory_usage():
    """メモリ使用量が適切であることを確認"""
    pass
```

## 移行戦略

### 段階的移行アプローチ

1. **並行運用期間（Week 1-2）**
   - 新旧システムを並行運用
   - 結果の比較検証
   - 段階的切り替え

2. **機能単位での移行**
   - 基本指標 → 素材DAGへ
   - 判定ロジック → 判定DAGへ
   - リスク管理 → 財務DAGへ

3. **テスト駆動での品質保証**
   - 各移行ステップでテスト実施
   - パフォーマンス測定
   - 動作検証

## アクションアイテム

### 即座に実施
- [ ] 横参照箇所の特定と修正リスト作成
- [ ] ステートフルな実装の洗い出し
- [ ] PKG ID体系への変換マッピング作成

### Week 1で実施
- [ ] 緊急修正の実装
- [ ] 新ディレクトリ構造の作成
- [ ] 基本的なテストの作成

### Week 2で実施
- [ ] 素材DAGの基本実装
- [ ] 判定DAGの骨組み作成
- [ ] 統合テストの実施

## リスクと対策

| リスク | 影響度 | 対策 |
|--------|-------|------|
| 既存ロジックの破壊 | 高 | 並行運用、段階的移行 |
| パフォーマンス低下 | 中 | プロファイリング、最適化 |
| テスト不足 | 高 | TDD、カバレッジ80%以上 |

## 結論

現在の実装は多くのPKGルール違反を含んでおり、全面的なリファクタリングが必要。
しかし、段階的な移行により、リスクを最小化しながら正しいPKG DAGアーキテクチャへの移行が可能。

---

監査実施者: PKG DAGアーキテクチャチーム
次回監査予定: Week 2終了時