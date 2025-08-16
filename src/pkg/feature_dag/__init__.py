"""
素材DAG (Feature DAG)
全時間足共通の特徴量抽出を行う安定層

階層構成:
- 階層0: 生データ収集
- 階層1-2: 基本特徴量計算
- 階層3-4: 複合特徴量計算
- 階層5: エクスポート層
"""

from typing import Dict, Any, Tuple

__version__ = "1.0.0"
__description__ = "PKG Feature DAG - 素材DAG実装"

# エクスポートする主要クラス
__all__ = [
    "DataCollectionLayer",
    "FeatureExtractionLayer", 
    "ExportLayer",
    "FeatureDAGManager"
]