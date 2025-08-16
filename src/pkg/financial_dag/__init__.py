"""
財務DAG (Financial DAG)
リスク計算とポジションサイジングを行う財務層

階層範囲: 70-79
- 70-74: リスク計算
- 75-79: ポジションサイジング

Phase 4実装内容:
- リスク評価システム
- ポジションサイジング
- 資金管理
- 損益計算
"""

from typing import Dict, Any, List, Optional

from .risk_calculator import RiskCalculatorDAG, RiskMetrics, RiskLevel
from .position_sizer import PositionSizerDAG, PositionSize, PositionType

__version__ = "4.0.0"
__description__ = "PKG Financial DAG - 財務DAG実装 (Phase 4)"

# 階層範囲定義
FINANCIAL_LAYER_RANGES = {
    "risk_calculation": (70, 74),
    "position_sizing": (75, 79)
}

# エクスポートする主要クラス
__all__ = [
    # リスク計算
    "RiskCalculatorDAG",
    "RiskMetrics",
    "RiskLevel",
    
    # ポジションサイジング
    "PositionSizerDAG",
    "PositionSize",
    "PositionType",
    
    # 定義
    "FINANCIAL_LAYER_RANGES"
]