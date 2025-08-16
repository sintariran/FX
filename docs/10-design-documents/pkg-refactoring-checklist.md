# PKG準拠リファクタリングチェックリスト

## 🎯 目的
既存コードをPKG DAGアーキテクチャに準拠させるための詳細チェックリスト

## ✅ PKG準拠チェック項目

### 1. 階層参照ルール
- [ ] **横参照の完全排除**
  - [ ] 同じ階層内のノード間参照がないか確認
  - [ ] 各関数が下位階層のみを参照しているか確認
  - [ ] 依存関係グラフにサイクルがないか確認

- [ ] **階層の明確化**
  - [ ] 各ノードの階層レベルが明確に定義されているか
  - [ ] 階層0（生データ）から上位階層への流れが一方向か
  - [ ] 階層Nが階層N-1以下のみを参照しているか

### 2. ステートレス実装
- [ ] **純粋関数への変換**
  - [ ] クラスのインスタンス変数によるステート保持を排除
  - [ ] 関数の戻り値が入力のみに依存
  - [ ] 同じ入力で必ず同じ出力を生成

```python
# ❌ ステートフル（変更前）
class BadExample:
    def __init__(self):
        self.cache = {}
    
    def process(self, data):
        self.cache[data.id] = data  # 状態変更
        return self.some_calculation()

# ✅ ステートレス（変更後）
def good_example(data: Dict, cache: Dict) -> Tuple[Result, Dict]:
    new_cache = {**cache, data['id']: data}
    result = calculate_something(data)
    return result, new_cache
```

### 3. PKG ID体系の統一
- [ ] **ID形式の確認**
  - [ ] `[時間足][周期][通貨]^[階層]-[連番]` 形式に準拠
  - [ ] 旧記号体系（AA001, AB301等）からの移行完了
  - [ ] 全ノードのIDが一意で重複なし

```python
# ❌ 旧形式
AA001 = "現在価格"
AB301 = "平均足始値"

# ✅ 新形式
391^0-001 = "現在価格"
391^0-101 = "平均足始値"
```

### 4. 関数定義の標準化
- [ ] **関数シグネチャ**
  - [ ] 入力パラメータが明確に型定義されている
  - [ ] 戻り値の型が明確
  - [ ] ドキュメント文字列で機能説明

```python
# ✅ 標準化された関数定義
def pkg_node_391_1_001(
    raw_data: Dict[str, float],
    context: Dict[str, Any]
) -> Tuple[float, Dict[str, Any]]:
    """
    391^1-001: もみ判定ノード
    
    Args:
        raw_data: 生データ（レンジ幅等）
        context: 実行コンテキスト
        
    Returns:
        (判定結果, 更新されたコンテキスト)
    """
    pass
```

## 🗂️ ファイル別リファクタリング計画

### Priority 1: 緊急対応が必要

#### src/pkg/memo_logic/dag_integration.py
- [ ] **階層構造の修正**
  - [ ] 3階層固定から動的階層に変更
  - [ ] 階層1-3 → 素材DAG（階層0-5）
  - [ ] DAGNodeクラスの階層参照チェック機能追加

- [ ] **ステートレス化**
  - [ ] FunctionalDAGEngineクラスの解体
  - [ ] キャッシュを外部注入に変更
  - [ ] 履歴管理を外部に移譲

#### src/pkg/memo_logic/core_pkg_functions.py
- [ ] **関数定義の標準化**
  - [ ] 独自関数名をPKG ID形式に変更
  - [ ] 入出力の型安全性確保
  - [ ] 純粋関数への変換

#### src/pkg/memo_logic/raw_symbol_to_pkg.py
- [ ] **ID体系の統一**
  - [ ] AA/AB系記号の完全廃止
  - [ ] 統一PKG ID体系への移行
  - [ ] 変換テーブルの更新

### Priority 2: 段階的対応

#### src/pkg/memo_logic/pkg_function_manager.py
- [ ] **アーキテクチャ適合**
  - [ ] 4段階DAG構造に対応
  - [ ] 各DAG種別の管理機能追加
  - [ ] エクスポート/インポート契約の実装

#### src/pkg/memo_logic/dag_engine_v2.py
- [ ] **エンジンの分離**
  - [ ] 素材DAGエンジン
  - [ ] 判定DAGエンジン
  - [ ] 財務DAGエンジン
  - [ ] 取引DAGエンジン

### Priority 3: 段階的統合

#### その他のファイル
- [ ] テストファイルのPKG準拠化
- [ ] ユーティリティ関数の整理
- [ ] ドキュメントの更新

## 🏗️ 新ディレクトリ構造の構築

### Phase 1: ディレクトリ作成
```bash
mkdir -p src/pkg/feature_dag
mkdir -p src/pkg/decision_dag/timeframes
mkdir -p src/pkg/financial_dag
mkdir -p src/pkg/trading_dag
mkdir -p tests/pkg/{feature,decision,financial,trading}
```

### Phase 2: 基本ファイル作成
- [ ] **素材DAG**
  - [ ] `src/pkg/feature_dag/__init__.py`
  - [ ] `src/pkg/feature_dag/data_collection.py`
  - [ ] `src/pkg/feature_dag/feature_extraction.py`
  - [ ] `src/pkg/feature_dag/export_layer.py`

- [ ] **判定DAG群**
  - [ ] `src/pkg/decision_dag/timeframes/m1_decision.py`
  - [ ] `src/pkg/decision_dag/timeframes/m5_decision.py`
  - [ ] `src/pkg/decision_dag/timeframes/m15_decision.py`
  - [ ] `src/pkg/decision_dag/timeframes/h1_decision.py`
  - [ ] `src/pkg/decision_dag/timeframes/h4_decision.py`

- [ ] **財務DAG**
  - [ ] `src/pkg/financial_dag/risk_management.py`
  - [ ] `src/pkg/financial_dag/position_sizing.py`

- [ ] **取引DAG**
  - [ ] `src/pkg/trading_dag/signal_integration.py`

## 🧪 テスト戦略

### 1. PKG準拠テスト
```python
# tests/pkg/test_pkg_compliance.py

def test_no_horizontal_references():
    """横参照がないことを確認"""
    for node_id, node in dag.nodes.items():
        for dep in node.dependencies:
            dep_node = dag.nodes[dep]
            assert dep_node.hierarchy < node.hierarchy

def test_stateless_functions():
    """純粋関数であることを確認"""
    # 同じ入力で複数回実行して結果が同じか確認
    pass

def test_pkg_id_format():
    """PKG ID形式の正しさを確認"""
    import re
    pattern = r'^\d\d\d\^\d+-\d+$'
    for node_id in dag.nodes.keys():
        assert re.match(pattern, node_id)
```

### 2. 性能テスト
```python
# tests/pkg/test_performance.py

def test_response_time():
    """30ms以内の応答を確認"""
    start_time = time.time()
    result = execute_dag(test_data)
    execution_time = (time.time() - start_time) * 1000
    assert execution_time < 30  # 30ms
```

### 3. 統合テスト
```python
# tests/pkg/test_integration.py

def test_dag_pipeline():
    """4段階DAGの統合動作を確認"""
    # 素材DAG → 判定DAG → 財務DAG → 取引DAG
    pass
```

## 📝 移行手順

### Week 1: 緊急対応

#### Day 1-2: 横参照の排除
1. [ ] 横参照箇所の特定（dependency graph分析）
2. [ ] 修正計画の作成
3. [ ] 緊急修正の実装

#### Day 3-4: ステートレス化
1. [ ] ステートフル実装の特定
2. [ ] 純粋関数への変換
3. [ ] キャッシュ外部化

#### Day 5: 新構造準備
1. [ ] 新ディレクトリ構造の作成
2. [ ] 基本ファイルの作成
3. [ ] 移行計画の詳細化

### Week 2: 構造再編

#### Day 1-2: 素材DAG移行
1. [ ] データ収集層の実装
2. [ ] 特徴量抽出層の実装
3. [ ] エクスポート層の実装

#### Day 3-4: 判定DAG骨組み
1. [ ] 各時間足判定DAGの基本構造
2. [ ] メモロジックの分離
3. [ ] インターフェース定義

#### Day 5: 統合テスト
1. [ ] テスト実装
2. [ ] 統合動作確認
3. [ ] パフォーマンス測定

## 🚨 リスク対策

### 1. 機能破壊の防止
- [ ] **並行運用**
  - [ ] 新旧システムの並行実行
  - [ ] 結果の比較検証
  - [ ] 段階的切り替え

- [ ] **テスト駆動**
  - [ ] 既存機能のテスト作成
  - [ ] リファクタリング前後の動作比較
  - [ ] 回帰テストの実施

### 2. パフォーマンス保証
- [ ] **ベンチマーク**
  - [ ] 現在の性能測定
  - [ ] 目標性能の設定（30ms以内）
  - [ ] 継続的なモニタリング

### 3. 品質保証
- [ ] **コードレビュー**
  - [ ] PKG準拠性の確認
  - [ ] セキュリティ確認
  - [ ] 可読性確認

## ✅ 完了条件

### Phase 1完了の判定基準
- [ ] 横参照が完全に排除されている
- [ ] すべての関数がステートレス
- [ ] PKG ID体系が統一されている
- [ ] 基本的なテストが通過
- [ ] 新ディレクトリ構造が整備されている

### 次フェーズへの移行条件
- [ ] 全チェック項目の80%以上が完了
- [ ] パフォーマンステストが通過
- [ ] 統合テストが通過
- [ ] ステークホルダーの承認取得

---

最終更新: 2025年1月
チェックリスト責任者: PKG DAGチーム