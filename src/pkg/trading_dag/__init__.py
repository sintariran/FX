"""
取引DAG (Trading DAG)
全体統合と最終執行判断を行う

階層範囲: 200-299
- 階層200: シグナル収集
- 階層201: 整合性チェック
- 階層202: 優先順位判定
- 階層203: 財務制約適用
- 階層204: 執行可否判定
- 階層205: 最終執行指示
"""

from typing import Dict, Any, Tuple

__version__ = "1.0.0"
__description__ = "PKG Trading DAG - 取引DAG実装"

# エクスポートする主要クラス
__all__ = [
    "SignalIntegrationLayer",
    "TradingDAGManager"
]