"""
判定DAG群 (Decision DAG)
各時間足での取引判定を行う探索層

時間足別階層範囲:
- 1分足: 階層20-29（スキャルピング）
- 5分足: 階層30-39（短期トレード）
- 15分足: 階層40-49（メイン取引）
- 1時間足: 階層50-59（中期トレード）
- 4時間足: 階層60-69（長期トレード）

Phase 3実装内容:
- 5つの時間足別判定DAG
- メモファイル核心概念実装（同逆、行帰、もみ合い）
- PKG準拠の階層構造
"""

from typing import Dict, Any, Tuple, List, Optional

from .m1_decision_dag import M1DecisionDAG, M1Signal, SignalType
from .m5_decision_dag import M5DecisionDAG, M5Signal
from .m15_decision_dag import M15DecisionDAG, M15Signal
from .h1_decision_dag import H1DecisionDAG, H1Signal
from .h4_decision_dag import H4DecisionDAG, H4Signal
from .unified_decision_system import UnifiedDecisionSystem, UnifiedSignal, TradingStrategy

__version__ = "3.0.0"
__description__ = "PKG Decision DAG - 判定DAG群実装 (Phase 3)"

# 時間足別階層定義
TIMEFRAME_LAYER_RANGES = {
    "M1": (20, 29),
    "M5": (30, 39), 
    "M15": (40, 49),
    "H1": (50, 59),
    "H4": (60, 69)
}

# エクスポートする主要クラス
__all__ = [
    # 個別時間足DAG
    "M1DecisionDAG",
    "M5DecisionDAG",
    "M15DecisionDAG",
    "H1DecisionDAG",
    "H4DecisionDAG",
    
    # 信号データクラス
    "M1Signal",
    "M5Signal",
    "M15Signal",
    "H1Signal",
    "H4Signal",
    
    # 統合システム
    "UnifiedDecisionSystem",
    "UnifiedSignal",
    "TradingStrategy",
    
    # 共通定義
    "SignalType",
    "TIMEFRAME_LAYER_RANGES"
]