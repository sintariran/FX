"""
判定DAG群 (Decision DAG)
各時間足での取引判定を行う探索層

時間足別階層範囲:
- 1分足: 階層20-29
- 5分足: 階層30-39  
- 15分足: 階層40-49
- 1時間足: 階層50-59
- 4時間足: 階層60-69
"""

from typing import Dict, Any, Tuple

__version__ = "1.0.0"
__description__ = "PKG Decision DAG - 判定DAG群実装"

# 時間足別階層定義
TIMEFRAME_LAYER_RANGES = {
    "1M": (20, 29),
    "5M": (30, 39), 
    "15M": (40, 49),
    "1H": (50, 59),
    "4H": (60, 69)
}

# エクスポートする主要クラス
__all__ = [
    "TimeframeDecisionDAG",
    "DecisionDAGManager",
    "TIMEFRAME_LAYER_RANGES"
]