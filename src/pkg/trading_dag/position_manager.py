"""
ポジション管理DAG
既存ポジションの管理と調整を行う取引層

階層範囲: 85-89（ポジション管理）
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class PositionStatus(Enum):
    """ポジション状態定義"""
    OPEN = "open"           # オープン中
    CLOSED = "closed"       # クローズ済み
    PENDING = "pending"     # 待機中
    PARTIAL = "partial"     # 部分決済済み

class AdjustmentType(Enum):
    """調整タイプ定義"""
    TRAIL_STOP = "trail_stop"       # トレーリングストップ
    BREAKEVEN = "breakeven"         # ブレークイーブン
    PARTIAL_CLOSE = "partial_close" # 部分決済
    ADD_POSITION = "add_position"   # ポジション追加
    HEDGE = "hedge"                 # ヘッジ

@dataclass
class Position:
    """ポジションデータ"""
    position_id: str
    order_id: str
    timestamp: datetime
    currency_pair: str
    side: str                      # buy/sell
    units: int
    entry_price: float
    current_price: float
    stop_loss: Optional[float]
    take_profit: Optional[float]
    unrealized_pnl: float
    realized_pnl: float
    status: PositionStatus
    metadata: Dict[str, Any]

@dataclass
class PositionAdjustment:
    """ポジション調整データ"""
    adjustment_id: str
    position_id: str
    timestamp: datetime
    adjustment_type: AdjustmentType
    old_values: Dict[str, Any]
    new_values: Dict[str, Any]
    reason: str
    success: bool

class PositionManagerDAG:
    """ポジション管理DAGクラス"""
    
    def __init__(self, currency_pair: str = "USDJPY"):
        self.currency_pair = currency_pair
        self.currency_code = self._get_currency_code(currency_pair)
        
        # DAGノード定義
        self.nodes = self._define_nodes()
        self.execution_order = self._determine_execution_order()
        
        # 内部状態
        self.positions: Dict[str, Position] = {}
        self.adjustment_history: List[PositionAdjustment] = []
        self.node_cache: Dict[str, Any] = {}
        
    def _get_currency_code(self, currency: str) -> str:
        """通貨コードを取得"""
        mapping = {
            "USDJPY": "1",
            "EURUSD": "2",
            "EURJPY": "3"
        }
        return mapping.get(currency, "1")
    
    def _define_nodes(self) -> Dict[str, Dict[str, Any]]:
        """DAGノード定義"""
        nodes = {}
        
        # 階層85: ポジション評価
        nodes["191^85-001"] = {
            "name": "position_evaluation",
            "layer": 85,
            "inputs": ["positions", "market_data"],
            "function": self._evaluate_positions,
            "description": "ポジション評価"
        }
        
        nodes["191^85-002"] = {
            "name": "pnl_calculation",
            "layer": 85,
            "inputs": ["positions", "current_prices"],
            "function": self._calculate_pnl,
            "description": "損益計算"
        }
        
        nodes["191^85-003"] = {
            "name": "risk_assessment",
            "layer": 85,
            "inputs": ["positions", "risk_metrics"],
            "function": self._assess_position_risk,
            "description": "ポジションリスク評価"
        }
        
        # 階層86: 調整判定
        nodes["191^86-001"] = {
            "name": "trailing_stop_check",
            "layer": 86,
            "inputs": ["191^85-001", "191^85-002"],
            "function": self._check_trailing_stop,
            "description": "トレーリングストップ判定"
        }
        
        nodes["191^86-002"] = {
            "name": "breakeven_check",
            "layer": 86,
            "inputs": ["191^85-002", "191^85-003"],
            "function": self._check_breakeven,
            "description": "ブレークイーブン判定"
        }
        
        nodes["191^86-003"] = {
            "name": "partial_close_check",
            "layer": 86,
            "inputs": ["191^85-001", "191^85-002"],
            "function": self._check_partial_close,
            "description": "部分決済判定"
        }
        
        # 階層87: 調整計画
        nodes["191^87-001"] = {
            "name": "adjustment_planning",
            "layer": 87,
            "inputs": ["191^86-001", "191^86-002", "191^86-003"],
            "function": self._plan_adjustments,
            "description": "調整計画立案"
        }
        
        nodes["191^87-002"] = {
            "name": "priority_sorting",
            "layer": 87,
            "inputs": ["191^86-001", "191^86-002", "191^86-003"],  # 階層86から入力
            "function": self._prioritize_adjustments,
            "description": "調整優先順位付け"
        }
        
        # 階層88: 調整実行
        nodes["191^88-001"] = {
            "name": "adjustment_execution",
            "layer": 88,
            "inputs": ["191^87-002", "positions"],
            "function": self._execute_adjustments,
            "description": "調整実行"
        }
        
        nodes["191^88-002"] = {
            "name": "adjustment_verification",
            "layer": 88,
            "inputs": ["191^87-002", "positions"],  # 階層87から入力
            "function": self._verify_adjustments,
            "description": "調整検証"
        }
        
        # 階層89: 最終管理
        nodes["191^89-001"] = {
            "name": "position_update",
            "layer": 89,
            "inputs": ["191^88-002"],
            "function": self._update_positions,
            "description": "ポジション更新"
        }
        
        return nodes
    
    def _determine_execution_order(self) -> List[str]:
        """実行順序を決定（トポロジカルソート）"""
        return [
            "191^85-001", "191^85-002", "191^85-003",  # 階層85
            "191^86-001", "191^86-002", "191^86-003",  # 階層86
            "191^87-001", "191^87-002",                # 階層87
            "191^88-001", "191^88-002",                # 階層88
            "191^89-001"                               # 階層89
        ]
    
    def process(self, positions: List[Position], market_data: Dict[str, Any],
                current_prices: Dict[str, float], 
                risk_metrics: Dict[str, Any]) -> List[PositionAdjustment]:
        """ポジション管理を実行"""
        # コンテキスト初期化
        context = {
            "positions": positions,
            "market_data": market_data,
            "current_prices": current_prices,
            "risk_metrics": risk_metrics
        }
        self.node_cache.clear()
        
        # DAG実行
        for node_id in self.execution_order:
            node = self.nodes[node_id]
            
            # 入力データ準備
            inputs = []
            for input_id in node["inputs"]:
                if input_id in context:
                    inputs.append(context[input_id])
                elif input_id in self.node_cache:
                    inputs.append(self.node_cache[input_id])
                else:
                    logger.warning(f"Missing input {input_id} for node {node_id}")
                    inputs.append(None)
            
            # ノード実行
            try:
                result = node["function"](*inputs)
                self.node_cache[node_id] = result
                
            except Exception as e:
                logger.error(f"Error executing node {node_id}: {e}")
                self.node_cache[node_id] = None
        
        # 最終調整リスト取得
        adjustments = self.node_cache.get("191^89-001", [])
        
        # 履歴に追加
        for adj in adjustments:
            self.adjustment_history.append(adj)
        
        # 履歴サイズ制限
        if len(self.adjustment_history) > 1000:
            self.adjustment_history = self.adjustment_history[-1000:]
        
        return adjustments
    
    # ===== 階層85: ポジション評価関数 =====
    
    def _evaluate_positions(self, positions: List[Position],
                          market_data: Dict[str, Any]) -> Dict[str, Any]:
        """ポジションを評価"""
        if not positions:
            return {"total_positions": 0, "evaluation": "no_positions"}
        
        evaluation = {
            "total_positions": len(positions),
            "open_positions": 0,
            "profitable_positions": 0,
            "losing_positions": 0,
            "position_details": []
        }
        
        for pos in positions:
            if pos.status == PositionStatus.OPEN:
                evaluation["open_positions"] += 1
                
                # 損益状態を評価
                if pos.unrealized_pnl > 0:
                    evaluation["profitable_positions"] += 1
                elif pos.unrealized_pnl < 0:
                    evaluation["losing_positions"] += 1
                
                evaluation["position_details"].append({
                    "id": pos.position_id,
                    "pnl": pos.unrealized_pnl,
                    "duration": (datetime.now() - pos.timestamp).total_seconds() / 3600
                })
        
        return evaluation
    
    def _calculate_pnl(self, positions: List[Position],
                      current_prices: Dict[str, float]) -> Dict[str, Any]:
        """損益を計算"""
        total_unrealized = 0.0
        total_realized = 0.0
        position_pnls = []
        
        for pos in positions:
            if pos.status == PositionStatus.OPEN:
                # 現在価格取得
                current = current_prices.get(pos.currency_pair, pos.current_price)
                
                # 損益計算（簡易版）
                if pos.side == "buy":
                    pnl = (current - pos.entry_price) * pos.units
                else:
                    pnl = (pos.entry_price - current) * pos.units
                
                pos.unrealized_pnl = pnl
                pos.current_price = current
                total_unrealized += pnl
                
                position_pnls.append({
                    "position_id": pos.position_id,
                    "unrealized_pnl": pnl,
                    "pnl_pct": (pnl / (pos.entry_price * pos.units)) * 100 if pos.units > 0 else 0
                })
            
            total_realized += pos.realized_pnl
        
        return {
            "total_unrealized": total_unrealized,
            "total_realized": total_realized,
            "total_pnl": total_unrealized + total_realized,
            "position_pnls": position_pnls
        }
    
    def _assess_position_risk(self, positions: List[Position],
                            risk_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """ポジションリスクを評価"""
        risk_assessment = {
            "total_exposure": 0,
            "max_position_risk": 0,
            "correlation_risk": 0,
            "high_risk_positions": []
        }
        
        for pos in positions:
            if pos.status == PositionStatus.OPEN:
                # エクスポージャー計算
                exposure = pos.units * pos.current_price
                risk_assessment["total_exposure"] += exposure
                
                # 個別ポジションリスク
                if pos.stop_loss:
                    position_risk = abs(pos.current_price - pos.stop_loss) * pos.units
                else:
                    position_risk = exposure * 0.02  # SLなしは2%リスクと仮定
                
                risk_assessment["max_position_risk"] = max(
                    risk_assessment["max_position_risk"], position_risk
                )
                
                # 高リスクポジション識別
                if position_risk > exposure * 0.05:  # 5%以上のリスク
                    risk_assessment["high_risk_positions"].append(pos.position_id)
        
        return risk_assessment
    
    # ===== 階層86: 調整判定関数 =====
    
    def _check_trailing_stop(self, evaluation: Dict[str, Any],
                            pnl_info: Dict[str, Any]) -> Dict[str, Any]:
        """トレーリングストップの必要性を判定"""
        trailing_candidates = []
        
        for pnl_detail in pnl_info.get("position_pnls", []):
            # 10%以上の利益があるポジション
            if pnl_detail["pnl_pct"] > 10:
                trailing_candidates.append({
                    "position_id": pnl_detail["position_id"],
                    "current_pnl_pct": pnl_detail["pnl_pct"],
                    "adjustment_type": AdjustmentType.TRAIL_STOP,
                    "new_stop_distance": pnl_detail["pnl_pct"] * 0.5  # 利益の50%を確保
                })
        
        return {
            "should_trail": len(trailing_candidates) > 0,
            "candidates": trailing_candidates
        }
    
    def _check_breakeven(self, pnl_info: Dict[str, Any],
                        risk_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """ブレークイーブンの必要性を判定"""
        breakeven_candidates = []
        
        for pnl_detail in pnl_info.get("position_pnls", []):
            # 5%以上の利益でブレークイーブン検討
            if 5 <= pnl_detail["pnl_pct"] < 10:
                breakeven_candidates.append({
                    "position_id": pnl_detail["position_id"],
                    "adjustment_type": AdjustmentType.BREAKEVEN,
                    "reason": "Protect small profit"
                })
        
        return {
            "should_breakeven": len(breakeven_candidates) > 0,
            "candidates": breakeven_candidates
        }
    
    def _check_partial_close(self, evaluation: Dict[str, Any],
                           pnl_info: Dict[str, Any]) -> Dict[str, Any]:
        """部分決済の必要性を判定"""
        partial_candidates = []
        
        for pnl_detail in pnl_info.get("position_pnls", []):
            # 20%以上の利益で部分決済検討
            if pnl_detail["pnl_pct"] > 20:
                partial_candidates.append({
                    "position_id": pnl_detail["position_id"],
                    "adjustment_type": AdjustmentType.PARTIAL_CLOSE,
                    "close_percentage": 50,  # 50%を決済
                    "reason": "Take partial profit"
                })
        
        return {
            "should_partial_close": len(partial_candidates) > 0,
            "candidates": partial_candidates
        }
    
    # ===== 階層87: 調整計画関数 =====
    
    def _plan_adjustments(self, trailing_info: Dict[str, Any],
                         breakeven_info: Dict[str, Any],
                         partial_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """調整計画を立案"""
        all_adjustments = []
        
        # 各調整タイプの候補を統合
        if trailing_info.get("should_trail"):
            all_adjustments.extend(trailing_info["candidates"])
        
        if breakeven_info.get("should_breakeven"):
            all_adjustments.extend(breakeven_info["candidates"])
        
        if partial_info.get("should_partial_close"):
            all_adjustments.extend(partial_info["candidates"])
        
        return all_adjustments
    
    def _prioritize_adjustments(self, trailing_info: Dict[str, Any],
                               breakeven_info: Dict[str, Any],
                               partial_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """調整の優先順位付け"""
        # 前段階の計画結果を取得
        adjustments = self.node_cache.get("191^87-001", [])
        
        if not adjustments:
            return []
        
        # 優先度スコア計算
        priority_map = {
            AdjustmentType.TRAIL_STOP: 3,
            AdjustmentType.PARTIAL_CLOSE: 2,
            AdjustmentType.BREAKEVEN: 1
        }
        
        for adj in adjustments:
            adj["priority"] = priority_map.get(adj["adjustment_type"], 0)
        
        # 優先度でソート（高い順）
        sorted_adjustments = sorted(adjustments, key=lambda x: x["priority"], reverse=True)
        
        return sorted_adjustments
    
    # ===== 階層88: 調整実行関数 =====
    
    def _execute_adjustments(self, planned_adjustments: List[Dict[str, Any]],
                           positions: List[Position]) -> List[Dict[str, Any]]:
        """調整を実行"""
        executed_adjustments = []
        
        # ポジションマップ作成
        pos_map = {pos.position_id: pos for pos in positions}
        
        for plan in planned_adjustments:
            pos_id = plan["position_id"]
            if pos_id not in pos_map:
                continue
            
            pos = pos_map[pos_id]
            adjustment_result = {
                "position_id": pos_id,
                "adjustment_type": plan["adjustment_type"],
                "success": False,
                "old_values": {},
                "new_values": {}
            }
            
            # 調整タイプ別の実行
            if plan["adjustment_type"] == AdjustmentType.TRAIL_STOP:
                old_sl = pos.stop_loss
                new_sl = pos.current_price - (pos.current_price * 0.01)  # 1%下
                pos.stop_loss = new_sl
                
                adjustment_result["old_values"]["stop_loss"] = old_sl
                adjustment_result["new_values"]["stop_loss"] = new_sl
                adjustment_result["success"] = True
                
            elif plan["adjustment_type"] == AdjustmentType.BREAKEVEN:
                old_sl = pos.stop_loss
                pos.stop_loss = pos.entry_price
                
                adjustment_result["old_values"]["stop_loss"] = old_sl
                adjustment_result["new_values"]["stop_loss"] = pos.entry_price
                adjustment_result["success"] = True
                
            elif plan["adjustment_type"] == AdjustmentType.PARTIAL_CLOSE:
                old_units = pos.units
                close_units = int(pos.units * plan["close_percentage"] / 100)
                pos.units -= close_units
                
                adjustment_result["old_values"]["units"] = old_units
                adjustment_result["new_values"]["units"] = pos.units
                adjustment_result["success"] = True
            
            if adjustment_result["success"]:
                executed_adjustments.append(adjustment_result)
        
        return executed_adjustments
    
    def _verify_adjustments(self, planned_adjustments: List[Dict[str, Any]],
                          positions: List[Position]) -> List[Dict[str, Any]]:
        """調整を検証"""
        # 前段階の実行結果を取得
        executed = self.node_cache.get("191^88-001", [])
        
        verified = []
        
        for adj in executed:
            # 検証ロジック（簡易版）
            if adj.get("success", False):
                adj["verified"] = True
                adj["verification_time"] = datetime.now()
                verified.append(adj)
            else:
                logger.warning(f"Adjustment verification failed for position {adj.get('position_id')}")
        
        return verified
    
    # ===== 階層89: 最終管理関数 =====
    
    def _update_positions(self, verified_adjustments: List[Dict[str, Any]]) -> List[PositionAdjustment]:
        """ポジションを更新して調整履歴を作成"""
        adjustments = []
        
        for vadj in verified_adjustments:
            adj = PositionAdjustment(
                adjustment_id=f"ADJ_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
                position_id=vadj["position_id"],
                timestamp=vadj.get("verification_time", datetime.now()),
                adjustment_type=vadj["adjustment_type"],
                old_values=vadj["old_values"],
                new_values=vadj["new_values"],
                reason=vadj.get("reason", "Automatic adjustment"),
                success=vadj.get("verified", False)
            )
            adjustments.append(adj)
        
        return adjustments
    
    def get_adjustment_history(self, limit: int = 10) -> List[PositionAdjustment]:
        """調整履歴を取得"""
        return self.adjustment_history[-limit:] if self.adjustment_history else []