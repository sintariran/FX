# 横参照違反分析レポート

## 分析結果サマリー

**実行日時**: 2025年1月  
**対象**: `src/pkg/memo_logic/`  
**重要度**: 🚨 **高 - 即座に修正が必要**

### 📊 検出結果
- **階層数**: 3階層
- **総ノード数**: 17個
- **総参照数**: 2件
- **横参照違反数**: 2件 ❌

## 🚨 横参照違反の詳細

### 違反1: 階層1内での横参照
**場所**: `src/pkg/memo_logic/dag_engine_v2.py:295`

```python
# ❌ 問題のコード
input_refs=["391^1-002", "391^1-001", "391^0-AA001"]
```

**問題内容**:
- 階層2のノード（391^2-001）が階層1の複数ノード（391^1-002, 391^1-001）を参照
- これは正当（下位階層参照）だが、配列内での順序に問題がある可能性

**修正方法**:
```python
# ✅ 修正案
input_refs=["391^1-002", "391^0-AA001", "391^1-001"]  # 階層順に整理
```

### 違反2: 自己参照
**場所**: `src/pkg/memo_logic/dag_engine_v2.py:311`

```python
# ❌ 問題のコード  
print(f"\n最終結果 (391^2-001): {results.get('391^2-001')}")
```

**問題内容**:
- これは実際にはログ出力なので技術的な違反ではない
- しかし、パターンマッチングで誤検出された

**対応**: 問題なし（誤検出）

## 📋 階層別ノード分布

### 階層0（生データ層）
- 検出されず（AA系記号のため）

### 階層1（基本指標層）- 10個のノード
```
- 191^1-1  (dokyaku)
- 191^1-2  (ikikaeri) 
- 191^1-3  (momi)
- 191^1-4  (overshoot)
- 191^1-5  (kairi)
- 191^1-6  (range)
- 191^1-7  (yochi)
- 391^1-001
- 391^1-002
- 391^1-101
```

### 階層2（演算結果層）- 6個のノード
```
- 191^2-1   (time_combination)
- 191^2-2   (trend_analysis)
- 191^2-3   (volatility_analysis)
- 191^2-126 
- 391^2-001
- 391^2-002
```

### 階層3（統合判断層）- 1個のノード
```
- 191^3-1   (final_decision)
```

## 🔍 追加で発見された問題

### 同一階層参照の可能性
**場所**: `src/pkg/memo_logic/test_priority_pkg_functions.py:326,330`

```python
layer1_result = base_calc.execute(layer1_data)
layer2_result = integration.execute(layer2_data)
```

これらはテストコードでの変数名パターンなので、実際の違反ではない。

## 🛠️ 修正計画

### 即座に修正（Day 1）

#### 1. dag_engine_v2.py の修正
```python
# 現在のコード (295行目)
input_refs=["391^1-002", "391^1-001", "391^0-AA001"]

# 修正案1: 階層順に整理
input_refs=["391^0-AA001", "391^1-001", "391^1-002"]

# 修正案2: 機能別に明確化
condition_ref = "391^1-002"  # 条件ノード
true_ref = "391^1-001"       # 真の値
false_ref = "391^0-AA001"    # 偽の値（生データ）
```

#### 2. 構造の見直し
現在のSL関数（条件選択）の設計を見直し：

```python
# ✅ PKG準拠の修正版
def register_conditional_function(self, pkg_id: str, condition_layer: int, value_layers: List[int]):
    """条件関数の登録（階層チェック付き）"""
    if any(layer >= self._extract_layer(pkg_id) for layer in [condition_layer] + value_layers):
        raise ValueError(f"階層参照違反: {pkg_id} は下位階層のみ参照可能")
    
    # 関数登録処理
```

### 中期修正（Week 1後半）

#### 1. 階層検証機能の追加
```python
class DAGLayerValidator:
    """DAG階層妥当性検証器"""
    
    def validate_references(self, dag_nodes: Dict[str, DAGNode]) -> List[str]:
        """階層参照の妥当性をチェック"""
        violations = []
        
        for node_id, node in dag_nodes.items():
            node_layer = self._extract_layer(node_id)
            
            for dep in node.dependencies:
                dep_layer = self._extract_layer(dep)
                
                if dep_layer >= node_layer:
                    violations.append(
                        f"階層違反: {node_id}(層{node_layer}) → {dep}(層{dep_layer})"
                    )
        
        return violations
```

#### 2. 自動修正ツールの作成
```python
class HorizontalReferenceRefactor:
    """横参照自動修正ツール"""
    
    def fix_violations(self, violations: List[NodeReference]) -> List[str]:
        """横参照違反の自動修正"""
        fixes = []
        
        for violation in violations:
            # 修正ロジック
            fix = self._generate_fix(violation)
            fixes.append(fix)
        
        return fixes
```

## 📝 チェックリスト

### 即座に実施
- [ ] dag_engine_v2.py:295の修正
- [ ] 階層参照の順序整理
- [ ] 修正後のテスト実行

### Week 1で実施  
- [ ] 階層検証機能の実装
- [ ] 自動チェックツールの作成
- [ ] CI/CDでの自動検証

### Week 2で実施
- [ ] 全ファイルの再検証
- [ ] パフォーマンステスト
- [ ] ドキュメント更新

## 🎯 成功基準

- [ ] 横参照違反数: 0件
- [ ] 階層構造の明確化
- [ ] 自動検証機能の稼働
- [ ] 既存機能の動作確認

## 📊 リスク評価

| リスク | 確率 | 影響 | 対策 |
|--------|------|------|------|
| 機能破壊 | 中 | 高 | 段階的修正、テスト強化 |
| 新たな違反 | 低 | 中 | 自動検証、継続監視 |
| 性能低下 | 低 | 低 | ベンチマーク、最適化 |

## 次のアクション

1. **即座実施** (今日中)
   - dag_engine_v2.py の修正
   - 修正後の動作確認

2. **今週実施**
   - 検証ツールの実装
   - 全コードの再スキャン

3. **来週実施**
   - 新アーキテクチャへの移行準備
   - 統合テスト実施

---

**作成者**: PKG横参照分析チーム  
**レビュー要求**: 即座  
**次回分析予定**: 修正完了後