"""
素材DAG (Feature DAG)
全時間足共通の特徴量抽出を行う安定層

階層構成:
- 階層0: 生データ収集
- 階層1-2: 基本特徴量計算
- 階層3-4: 複合特徴量計算
- 階層5: エクスポート層

Phase 2 実装内容（レビューフィードバック対応）:
- データ駆動ノード定義システム (YAML設定)
- 自動評価順序決定 (トポロジカルソート)
- AI エージェント対応パラメータ化
"""

from typing import Dict, Any, Tuple

from .data_collection import DataCollectionLayer, MarketTick, create_sample_tick
from .feature_extraction import FeatureExtractionLayer, MarketData, HeikinAshiData
from .dag_config_manager import DAGConfigManager, NodeDefinition, DAGStructure
from .export_contract import (
    StandardFeatureExporter, VersionedExportManager, FeatureBundle, 
    StandardizedFeature, FeatureMetadata, DataQuality, default_export_manager
)

__version__ = "2.0.0"
__description__ = "PKG Feature DAG - 素材DAG実装 (Phase 2)"

# エクスポートする主要クラス
__all__ = [
    # データ収集層
    "DataCollectionLayer",
    "MarketTick", 
    "create_sample_tick",
    
    # 特徴量抽出層
    "FeatureExtractionLayer",
    "MarketData",
    "HeikinAshiData",
    
    # DAG構成管理
    "DAGConfigManager",
    "NodeDefinition",
    "DAGStructure",
    
    # エクスポート契約
    "StandardFeatureExporter",
    "VersionedExportManager", 
    "FeatureBundle",
    "StandardizedFeature",
    "FeatureMetadata", 
    "DataQuality",
    "default_export_manager"
]