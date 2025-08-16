# PKG DAGアーキテクチャレビュー対応

## レビュー日: 2025-08-16

## エグゼクティブサマリー

Phase 4のアーキテクチャレビューにて、PKG DAGアーキテクチャの原則が適切に実装されていることが確認されました。
本ドキュメントでは、レビューで提案された改善点への対応方針を記載します。

## 高評価を受けた実装

### 1. PKG原則の完全遵守
- ✅ 横参照の完全排除
- ✅ 下位階層のみへの依存
- ✅ テストによる自動検証

### 2. 階層構造の柔軟性
- ✅ 無限に深くなり得る階層設計
- ✅ ID形式での階層番号可変長対応（`\d+`）

### 3. 厳格なID体系
- ✅ `[時間足][周期][通貨]^[階層]-[連番]`形式の徹底
- ✅ 正規表現による形式検証
- ✅ ID生成ユーティリティの提供

### 4. DAG間の適切な分離
- ✅ 素材DAGと判定DAGのモジュール分離
- ✅ ディレクトリレベルでの責務分離
- ✅ エクスポート/インポート契約による疎結合

### 5. 設計との高い整合性
- ✅ 設計ドキュメントの原則をコードに反映
- ✅ テストケースによる設計ルールの検証
- ✅ 階層ごとの責務とコード実装の対応

## 改善提案への対応計画

### 1. DAGConfigManagerの自動検証強化（優先度: 高）

**現状の課題**
- 階層チェックがテスト頼り
- ロード時点での違反検知なし

**対応方針**
```python
class DAGConfigManager:
    def validate_hierarchy(self, nodes: Dict[str, NodeDefinition]):
        """YAML読み込み時に階層ルールを自動検証"""
        for node_id, node in nodes.items():
            # 横参照チェック
            for input_id in node.inputs:
                if input_id in nodes:
                    if nodes[input_id].layer >= node.layer:
                        raise ValueError(f"横参照違反: {node_id} → {input_id}")
            
            # ID形式と階層番号の一致チェック
            id_layer = int(node_id.split('^')[1].split('-')[0])
            if id_layer != node.layer:
                raise ValueError(f"ID-階層不一致: {node_id}")
```

**実装時期**: Phase 5開始前（即座に対応）

### 2. 階層上限値の動的拡張（優先度: 中）

**現状の課題**
- YAMLスキーマで階層5までに制限
- 判定DAGでは10-20層必要

**対応方針**
```yaml
# node_definitions_schema.yaml
layer:
  type: integer
  minimum: 0
  # maximum: 5  # この上限を撤廃
  description: "階層番号（上限なし）"
```

**実装時期**: Phase 5での判定DAG詳細実装時

### 3. レガシーコードのリファクタリング（優先度: 低）

**現状の課題**
- UnifiedPKGSystemが3層固定
- 品質ゲート層の未実装

**対応方針**
1. 新アーキテクチャへの段階的移行
2. TimeframeDecisionDAGクラスへの置き換え
3. 品質ゲート・リスク評価層の追加

**実装時期**: Phase 6-7で段階的に実施

### 4. エクスポートバージョン管理（優先度: 中）

**現状の課題**
- ID連番でのバージョン管理が不明確
- 設計例（391^5-126）と実装（391^5-001）の差異

**対応方針**
```python
class ExportVersionManager:
    """エクスポートバージョン管理"""
    
    def get_export_node_id(self, version: int) -> str:
        """バージョンに応じたノードID生成"""
        # v1: 391^5-001
        # v2: 391^5-101  # 100番台を使用
        # v3: 391^5-201  # 200番台を使用
        base = version - 1
        return f"391^5-{base*100 + 1:03d}"
```

**実装時期**: エクスポートv2が必要になった時点

### 5. 階層番号割り当ての拡張性（優先度: 低）

**現状の課題**
- 各時間足10層制限
- 将来の複雑化への対応

**対応方針**
```python
DYNAMIC_LAYER_RANGES = {
    "M1": (20, None),   # 上限なし
    "M5": (30, None),
    "M15": (40, None),
    "H1": (50, None),
    "H4": (60, None)
}

def allocate_layer(timeframe: str, layer_offset: int) -> int:
    """動的な階層番号割り当て"""
    base = DYNAMIC_LAYER_RANGES[timeframe][0]
    return base + layer_offset
```

**実装時期**: 10層を超える要求が発生した時点

### 6. ID自動採番ユーティリティ（優先度: 中）

**現状の課題**
- 手動でのID管理によるミスリスク
- ノード数増加への対応

**対応方針**
```python
class NodeIDGenerator:
    """ノードID自動採番"""
    
    def __init__(self, timeframe: str, period: str, currency: str):
        self.prefix = f"{timeframe}{period}{currency}"
        self.counters = {}  # 階層ごとのカウンタ
    
    def generate(self, layer: int) -> str:
        """次の利用可能なIDを生成"""
        if layer not in self.counters:
            self.counters[layer] = 0
        
        self.counters[layer] += 1
        return f"{self.prefix}^{layer}-{self.counters[layer]:03d}"
```

**実装時期**: Phase 5で実装・導入

## アクションプラン

### 即座に対応（〜1週間）
1. DAGConfigManagerへの階層チェック追加
2. YAMLスキーマの階層上限撤廃

### Phase 5で対応（〜2週間）
1. ID自動採番ユーティリティ実装
2. 動的階層割り当ての基盤整備

### Phase 6-7で対応（〜1ヶ月）
1. レガシーコードのリファクタリング
2. エクスポートバージョン管理の体系化
3. 階層番号の動的拡張実装

## まとめ

レビューで高い評価をいただいた実装品質を維持しつつ、提案された改善点を段階的に実装していきます。
特に、システムの拡張性と保守性を高める改善（自動検証、ID採番、動的階層）を優先的に進めます。

## 参照

- [PKG DAGアーキテクチャ設計書](../10-design-documents/00-pkg-dag-architecture-overview.md)
- [PKG実装ロードマップ](./pkg-implementation-roadmap.md)
- [Phase 4 PR #12](https://github.com/sintariran/FX/pull/12)