"""
取引DAG (Trading DAG)
注文執行とポジション管理を行う取引層

階層範囲: 80-89
- 80-84: 注文執行
- 85-89: ポジション管理

Phase 5実装内容:
- 注文生成・執行
- ポジション追跡
- トレーリングストップ
- 部分決済
"""

from typing import Dict, Any, List, Optional

from .order_executor import (
    OrderExecutorDAG, TradingOrder, OrderType, OrderSide, OrderStatus
)
from .position_manager import (
    PositionManagerDAG, Position, PositionAdjustment, 
    PositionStatus, AdjustmentType
)

__version__ = "5.0.0"
__description__ = "PKG Trading DAG - 取引DAG実装 (Phase 5)"

# 階層範囲定義
TRADING_LAYER_RANGES = {
    "order_execution": (80, 84),
    "position_management": (85, 89)
}

# エクスポートする主要クラス
__all__ = [
    # 注文執行
    "OrderExecutorDAG",
    "TradingOrder",
    "OrderType",
    "OrderSide",
    "OrderStatus",
    
    # ポジション管理
    "PositionManagerDAG",
    "Position",
    "PositionAdjustment",
    "PositionStatus",
    "AdjustmentType",
    
    # 定義
    "TRADING_LAYER_RANGES"
]