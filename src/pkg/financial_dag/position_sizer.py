"""
ポジションサイジングDAG
適切なポジションサイズを計算する財務層

階層範囲: 75-79（ポジションサイジング）
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class PositionType(Enum):
    """ポジションタイプ定義"""
    MICRO = 1000       # マイクロロット
    MINI = 10000       # ミニロット
    STANDARD = 100000  # スタンダードロット

@dataclass
class PositionSize:
    """ポジションサイズデータ"""
    timestamp: datetime
    units: int                    # 取引単位数
    lot_size: float               # ロットサイズ
    position_type: PositionType   # ポジションタイプ
    risk_amount: float            # リスク金額
    stop_loss_pips: float         # ストップロス幅（pips）
    take_profit_pips: float       # テイクプロフィット幅（pips）
    risk_reward_ratio: float      # リスクリワード比
    kelly_fraction: float         # ケリー基準
    components: Dict[str, Any]

class PositionSizerDAG:
    """ポジションサイジングDAGクラス"""
    
    def __init__(self, currency_pair: str = "USDJPY"):
        self.currency_pair = currency_pair
        self.currency_code = self._get_currency_code(currency_pair)
        
        # DAGノード定義
        self.nodes = self._define_nodes()
        self.execution_order = self._determine_execution_order()
        
        # 内部状態
        self.sizing_history: List[PositionSize] = []
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
        
        # 階層75: 基本サイズ計算
        nodes["191^75-001"] = {
            "name": "fixed_percentage_sizing",
            "layer": 75,
            "inputs": ["account_balance", "risk_percentage"],
            "function": self._fixed_percentage_sizing,
            "description": "固定パーセンテージサイジング"
        }
        
        nodes["191^75-002"] = {
            "name": "volatility_based_sizing",
            "layer": 75,
            "inputs": ["market_volatility", "account_balance"],
            "function": self._volatility_based_sizing,
            "description": "ボラティリティベースサイジング"
        }
        
        nodes["191^75-003"] = {
            "name": "atr_based_sizing",
            "layer": 75,
            "inputs": ["atr_value", "account_balance"],
            "function": self._atr_based_sizing,
            "description": "ATRベースサイジング"
        }
        
        # 階層76: ケリー基準計算
        nodes["191^76-001"] = {
            "name": "kelly_criterion",
            "layer": 76,
            "inputs": ["191^75-001", "win_rate", "avg_win_loss_ratio"],
            "function": self._kelly_criterion,
            "description": "ケリー基準計算"
        }
        
        nodes["191^76-002"] = {
            "name": "fractional_kelly",
            "layer": 76,
            "inputs": ["191^75-001", "kelly_fraction_multiplier", "win_rate", "avg_win_loss_ratio"],  # 階層75から入力
            "function": self._fractional_kelly,
            "description": "分数ケリー調整"
        }
        
        # 階層77: リスクリワード計算
        nodes["191^77-001"] = {
            "name": "stop_loss_calculation",
            "layer": 77,
            "inputs": ["191^75-002", "191^75-003", "support_resistance_levels"],
            "function": self._calculate_stop_loss,
            "description": "ストップロス計算"
        }
        
        nodes["191^77-002"] = {
            "name": "take_profit_calculation",
            "layer": 77,
            "inputs": ["191^75-002", "191^75-003", "risk_reward_target"],  # 階層75から入力
            "function": self._calculate_take_profit,
            "description": "テイクプロフィット計算"
        }
        
        # 階層78: ポジション調整
        nodes["191^78-001"] = {
            "name": "position_adjustment",
            "layer": 78,
            "inputs": ["191^76-002", "191^77-001", "191^77-002", "risk_metrics"],
            "function": self._adjust_position,
            "description": "ポジション調整"
        }
        
        nodes["191^78-002"] = {
            "name": "max_position_limits",
            "layer": 78,
            "inputs": ["191^76-002", "191^77-001", "191^77-002", "account_constraints"],  # 階層76,77から入力
            "function": self._apply_position_limits,
            "description": "最大ポジション制限"
        }
        
        # 階層79: 最終サイズ決定
        nodes["191^79-001"] = {
            "name": "final_position_size",
            "layer": 79,
            "inputs": ["191^78-002"],
            "function": self._final_position_size,
            "description": "最終ポジションサイズ"
        }
        
        return nodes
    
    def _determine_execution_order(self) -> List[str]:
        """実行順序を決定（トポロジカルソート）"""
        return [
            "191^75-001", "191^75-002", "191^75-003",  # 階層75
            "191^76-001", "191^76-002",                # 階層76
            "191^77-001", "191^77-002",                # 階層77
            "191^78-001", "191^78-002",                # 階層78
            "191^79-001"                               # 階層79
        ]
    
    def process(self, account_balance: float, risk_percentage: float = 0.02,
                market_volatility: float = 0.01, atr_value: float = 0.5,
                win_rate: float = 0.55, avg_win_loss_ratio: float = 1.5,
                kelly_fraction_multiplier: float = 0.25,
                support_resistance_levels: Dict[str, float] = None,
                risk_reward_target: float = 2.0,
                risk_metrics: Dict[str, Any] = None,
                account_constraints: Dict[str, Any] = None) -> PositionSize:
        """ポジションサイズを計算"""
        # コンテキスト初期化
        context = {
            "account_balance": account_balance,
            "risk_percentage": risk_percentage,
            "market_volatility": market_volatility,
            "atr_value": atr_value,
            "win_rate": win_rate,
            "avg_win_loss_ratio": avg_win_loss_ratio,
            "kelly_fraction_multiplier": kelly_fraction_multiplier,
            "support_resistance_levels": support_resistance_levels or {},
            "risk_reward_target": risk_reward_target,
            "risk_metrics": risk_metrics or {},
            "account_constraints": account_constraints or {}
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
        
        # 最終ポジションサイズ取得
        final_size = self.node_cache.get("191^79-001")
        
        if final_size:
            # 履歴に追加
            self.sizing_history.append(final_size)
            
            # 履歴サイズ制限
            if len(self.sizing_history) > 100:
                self.sizing_history = self.sizing_history[-100:]
            
            return final_size
        else:
            # デフォルトサイズ
            return PositionSize(
                timestamp=datetime.now(),
                units=1000,
                lot_size=0.01,
                position_type=PositionType.MICRO,
                risk_amount=account_balance * 0.01,
                stop_loss_pips=20,
                take_profit_pips=40,
                risk_reward_ratio=2.0,
                kelly_fraction=0.02,
                components={}
            )
    
    # ===== 階層75: 基本サイズ計算関数 =====
    
    def _fixed_percentage_sizing(self, account_balance: float, 
                                risk_percentage: float) -> Dict[str, Any]:
        """固定パーセンテージサイジング"""
        risk_amount = account_balance * risk_percentage
        
        # 基本ロットサイズ計算（1pip = 100円と仮定）
        pip_value = 100 if "JPY" in self.currency_pair else 10
        stop_loss_pips = 20  # デフォルト20pips
        
        lot_size = risk_amount / (stop_loss_pips * pip_value)
        
        return {
            "risk_amount": risk_amount,
            "lot_size": lot_size,
            "method": "fixed_percentage"
        }
    
    def _volatility_based_sizing(self, market_volatility: float,
                                account_balance: float) -> Dict[str, Any]:
        """ボラティリティベースサイジング"""
        # ボラティリティが高いほどポジションサイズを小さく
        volatility_factor = 1 / (1 + market_volatility * 10)
        base_size = account_balance * 0.02  # 基本2%リスク
        
        adjusted_risk = base_size * volatility_factor
        
        return {
            "adjusted_risk": adjusted_risk,
            "volatility_factor": volatility_factor,
            "method": "volatility_based"
        }
    
    def _atr_based_sizing(self, atr_value: float,
                        account_balance: float) -> Dict[str, Any]:
        """ATRベースサイジング"""
        # ATRの2倍をストップロスとして使用
        stop_distance = atr_value * 2
        risk_amount = account_balance * 0.01  # 1%リスク
        
        # ポジションサイズ計算
        if stop_distance > 0:
            position_size = risk_amount / stop_distance
        else:
            position_size = 1000  # デフォルト最小サイズ
        
        return {
            "position_size": position_size,
            "stop_distance": stop_distance,
            "atr_multiplier": 2,
            "method": "atr_based"
        }
    
    # ===== 階層76: ケリー基準計算関数 =====
    
    def _kelly_criterion(self, fixed_sizing: Dict[str, Any],
                        win_rate: float, avg_win_loss_ratio: float) -> Dict[str, Any]:
        """ケリー基準を計算"""
        # ケリー公式: f = (p*b - q) / b
        # p: 勝率, q: 負け率, b: 平均利益/平均損失
        p = win_rate
        q = 1 - win_rate
        b = avg_win_loss_ratio
        
        if b > 0:
            kelly_fraction = (p * b - q) / b
            kelly_fraction = max(0, min(kelly_fraction, 0.25))  # 0-25%に制限
        else:
            kelly_fraction = 0.01
        
        return {
            "kelly_fraction": kelly_fraction,
            "win_rate": win_rate,
            "avg_win_loss_ratio": avg_win_loss_ratio,
            "base_lot_size": fixed_sizing.get("lot_size", 0.01)
        }
    
    def _fractional_kelly(self, fixed_sizing: Dict[str, Any],
                         kelly_fraction_multiplier: float,
                         win_rate: float, avg_win_loss_ratio: float) -> Dict[str, Any]:
        """分数ケリー調整"""
        # ケリー基準を直接計算
        p = win_rate
        q = 1 - win_rate
        b = avg_win_loss_ratio
        
        if b > 0:
            full_kelly = (p * b - q) / b
            full_kelly = max(0, min(full_kelly, 0.25))
        else:
            full_kelly = 0.02
        
        # 分数ケリー（通常1/4を使用）
        fractional_kelly = full_kelly * kelly_fraction_multiplier
        
        # ロットサイズ調整
        base_lot = fixed_sizing.get("lot_size", 0.01)
        adjusted_lot = base_lot * (fractional_kelly / 0.02)  # 2%基準で調整
        
        return {
            "fractional_kelly": fractional_kelly,
            "adjusted_lot_size": adjusted_lot,
            "multiplier": kelly_fraction_multiplier
        }
    
    # ===== 階層77: リスクリワード計算関数 =====
    
    def _calculate_stop_loss(self, volatility_sizing: Dict[str, Any],
                            atr_sizing: Dict[str, Any],
                            support_resistance_levels: Dict[str, float]) -> Dict[str, Any]:
        """ストップロスを計算"""
        # ATRベースのストップ距離
        atr_stop = atr_sizing.get("stop_distance", 20)
        
        # サポート/レジスタンスレベル考慮
        if support_resistance_levels:
            current_price = support_resistance_levels.get("current", 100)
            nearest_support = support_resistance_levels.get("support", current_price - 20)
            technical_stop = abs(current_price - nearest_support)
        else:
            technical_stop = 20
        
        # 最終ストップロス（pips）
        stop_loss_pips = max(atr_stop, technical_stop)
        
        return {
            "stop_loss_pips": stop_loss_pips,
            "atr_based": atr_stop,
            "technical_based": technical_stop
        }
    
    def _calculate_take_profit(self, volatility_sizing: Dict[str, Any],
                              atr_sizing: Dict[str, Any],
                              risk_reward_target: float) -> Dict[str, Any]:
        """テイクプロフィットを計算"""
        # ATRベースのストップ距離から推定
        atr_stop = atr_sizing.get("stop_distance", 20)
        sl_pips = atr_stop  # ストップロスpips推定
        
        # リスクリワード比に基づくTP
        take_profit_pips = sl_pips * risk_reward_target
        
        return {
            "take_profit_pips": take_profit_pips,
            "risk_reward_ratio": risk_reward_target,
            "stop_loss_reference": sl_pips
        }
    
    # ===== 階層78: ポジション調整関数 =====
    
    def _adjust_position(self, fractional_kelly: Dict[str, Any],
                        stop_loss: Dict[str, Any],
                        take_profit: Dict[str, Any],
                        risk_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """リスクメトリクスに基づいてポジション調整"""
        base_lot = fractional_kelly.get("adjusted_lot_size", 0.01)
        
        # リスクレベルに応じた調整
        risk_level = risk_metrics.get("risk_level", 3)  # 1-5のスケール
        risk_adjustment = 1.0 - (risk_level - 3) * 0.2  # リスクが高いほど小さく
        
        adjusted_lot = base_lot * max(0.1, risk_adjustment)
        
        return {
            "adjusted_lot_size": adjusted_lot,
            "risk_adjustment_factor": risk_adjustment,
            "stop_loss_pips": stop_loss.get("stop_loss_pips", 20),
            "take_profit_pips": take_profit.get("take_profit_pips", 40)
        }
    
    def _apply_position_limits(self, fractional_kelly: Dict[str, Any],
                              stop_loss: Dict[str, Any],
                              take_profit: Dict[str, Any],
                              account_constraints: Dict[str, Any]) -> Dict[str, Any]:
        """最大ポジション制限を適用"""
        lot_size = fractional_kelly.get("adjusted_lot_size", 0.01)
        
        # 制約適用
        max_lot = account_constraints.get("max_lot_size", 10.0)
        min_lot = account_constraints.get("min_lot_size", 0.01)
        max_positions = account_constraints.get("max_positions", 5)
        current_positions = account_constraints.get("current_positions", 0)
        
        # 同時ポジション数考慮
        if current_positions >= max_positions:
            final_lot = 0
        else:
            position_factor = 1.0 - (current_positions / max_positions) * 0.5
            final_lot = lot_size * position_factor
            final_lot = max(min_lot, min(final_lot, max_lot))
        
        return {
            "final_lot_size": final_lot,
            "position_limited": current_positions >= max_positions,
            "constraints_applied": True,
            "stop_loss_pips": stop_loss.get("stop_loss_pips", 20),
            "take_profit_pips": take_profit.get("take_profit_pips", 40)
        }
    
    # ===== 階層79: 最終サイズ決定関数 =====
    
    def _final_position_size(self, limited_position: Dict[str, Any]) -> PositionSize:
        """最終ポジションサイズを決定"""
        lot_size = limited_position.get("final_lot_size", 0.01)
        
        # ユニット数計算
        if lot_size >= 1.0:
            units = int(lot_size * 100000)
            position_type = PositionType.STANDARD
        elif lot_size >= 0.1:
            units = int(lot_size * 100000)
            position_type = PositionType.MINI
        else:
            units = int(lot_size * 100000)
            position_type = PositionType.MICRO
        
        # リスク金額計算
        pip_value = 100 if "JPY" in self.currency_pair else 10
        sl_pips = limited_position.get("stop_loss_pips", 20)
        risk_amount = lot_size * sl_pips * pip_value
        
        # リスクリワード比
        tp_pips = limited_position.get("take_profit_pips", 40)
        rr_ratio = tp_pips / sl_pips if sl_pips > 0 else 2.0
        
        return PositionSize(
            timestamp=datetime.now(),
            units=units,
            lot_size=lot_size,
            position_type=position_type,
            risk_amount=risk_amount,
            stop_loss_pips=sl_pips,
            take_profit_pips=tp_pips,
            risk_reward_ratio=rr_ratio,
            kelly_fraction=limited_position.get("final_lot_size", 0.01) / 0.01 * 0.02,
            components=limited_position
        )
    
    def get_sizing_history(self, limit: int = 10) -> List[PositionSize]:
        """サイジング履歴を取得"""
        return self.sizing_history[-limit:] if self.sizing_history else []