"""
財務DAG (Financial DAG)
リスク管理とポジションサイジングを行う

階層範囲: 100-119
- 階層100: ポートフォリオ状態
- 階層101: リスク評価
- 階層102: ポジションサイジング
- 階層103: 執行パラメータ
"""

from typing import Dict, Any, Tuple

__version__ = "1.0.0"
__description__ = "PKG Financial DAG - 財務DAG実装"

# エクスポートする主要クラス
__all__ = [
    "RiskManagementLayer",
    "PositionSizingLayer", 
    "FinancialDAGManager"
]