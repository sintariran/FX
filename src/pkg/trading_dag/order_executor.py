"""
注文執行DAG
実際の取引注文を生成・実行する取引層

階層範囲: 80-84（注文執行）
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class OrderType(Enum):
    """注文タイプ定義"""
    MARKET = "market"           # 成行注文
    LIMIT = "limit"             # 指値注文
    STOP = "stop"               # 逆指値注文
    STOP_LIMIT = "stop_limit"   # 逆指値指値注文

class OrderSide(Enum):
    """注文方向定義"""
    BUY = "buy"    # 買い注文
    SELL = "sell"  # 売り注文

class OrderStatus(Enum):
    """注文状態定義"""
    PENDING = "pending"       # 待機中
    SUBMITTED = "submitted"   # 送信済み
    FILLED = "filled"         # 約定済み
    PARTIAL = "partial"       # 部分約定
    CANCELLED = "cancelled"   # キャンセル済み
    REJECTED = "rejected"     # 拒否済み

@dataclass
class TradingOrder:
    """取引注文データ"""
    order_id: str
    timestamp: datetime
    currency_pair: str
    side: OrderSide
    order_type: OrderType
    units: int
    price: Optional[float]          # 指値価格
    stop_price: Optional[float]     # 逆指値価格
    take_profit: Optional[float]    # 利確価格
    stop_loss: Optional[float]      # 損切価格
    time_in_force: str              # 有効期限（GTC/IOC/FOK）
    status: OrderStatus
    metadata: Dict[str, Any]

class OrderExecutorDAG:
    """注文執行DAGクラス"""
    
    def __init__(self, currency_pair: str = "USDJPY"):
        self.currency_pair = currency_pair
        self.currency_code = self._get_currency_code(currency_pair)
        
        # DAGノード定義
        self.nodes = self._define_nodes()
        self.execution_order = self._determine_execution_order()
        
        # 内部状態
        self.order_history: List[TradingOrder] = []
        self.active_orders: Dict[str, TradingOrder] = {}
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
        
        # 階層80: 注文準備
        nodes["191^80-001"] = {
            "name": "order_validation",
            "layer": 80,
            "inputs": ["unified_signal", "position_size", "risk_metrics"],
            "function": self._validate_order,
            "description": "注文検証"
        }
        
        nodes["191^80-002"] = {
            "name": "order_timing",
            "layer": 80,
            "inputs": ["market_data", "signal_confidence"],
            "function": self._determine_timing,
            "description": "注文タイミング判定"
        }
        
        nodes["191^80-003"] = {
            "name": "order_type_selection",
            "layer": 80,
            "inputs": ["market_conditions", "strategy"],
            "function": self._select_order_type,
            "description": "注文タイプ選択"
        }
        
        # 階層81: 価格計算
        nodes["191^81-001"] = {
            "name": "entry_price_calculation",
            "layer": 81,
            "inputs": ["191^80-001", "191^80-002", "current_price"],
            "function": self._calculate_entry_price,
            "description": "エントリー価格計算"
        }
        
        nodes["191^81-002"] = {
            "name": "slippage_adjustment",
            "layer": 81,
            "inputs": ["191^80-003", "market_volatility"],
            "function": self._adjust_for_slippage,
            "description": "スリッページ調整"
        }
        
        # 階層82: 注文構築
        nodes["191^82-001"] = {
            "name": "order_construction",
            "layer": 82,
            "inputs": ["191^81-001", "191^81-002", "position_size"],
            "function": self._construct_order,
            "description": "注文構築"
        }
        
        nodes["191^82-002"] = {
            "name": "order_protection",
            "layer": 82,
            "inputs": ["191^81-001", "stop_loss_pips", "take_profit_pips"],
            "function": self._add_protection_levels,
            "description": "保護レベル設定"
        }
        
        # 階層83: 注文送信
        nodes["191^83-001"] = {
            "name": "order_submission",
            "layer": 83,
            "inputs": ["191^82-001", "191^82-002"],
            "function": self._submit_order,
            "description": "注文送信"
        }
        
        nodes["191^83-002"] = {
            "name": "order_confirmation",
            "layer": 83,
            "inputs": ["191^82-001", "191^82-002"],  # 階層82から入力
            "function": self._confirm_order,
            "description": "注文確認"
        }
        
        # 階層84: 注文管理
        nodes["191^84-001"] = {
            "name": "order_tracking",
            "layer": 84,
            "inputs": ["191^83-002"],
            "function": self._track_order,
            "description": "注文追跡"
        }
        
        return nodes
    
    def _determine_execution_order(self) -> List[str]:
        """実行順序を決定（トポロジカルソート）"""
        return [
            "191^80-001", "191^80-002", "191^80-003",  # 階層80
            "191^81-001", "191^81-002",                # 階層81
            "191^82-001", "191^82-002",                # 階層82
            "191^83-001", "191^83-002",                # 階層83
            "191^84-001"                               # 階層84
        ]
    
    def process(self, unified_signal: Any, position_size: Any,
                risk_metrics: Any, market_data: Dict[str, Any],
                signal_confidence: float, market_conditions: Dict[str, Any],
                strategy: str, current_price: float,
                market_volatility: float, stop_loss_pips: float,
                take_profit_pips: float) -> TradingOrder:
        """注文を生成・実行"""
        # コンテキスト初期化
        context = {
            "unified_signal": unified_signal,
            "position_size": position_size,
            "risk_metrics": risk_metrics,
            "market_data": market_data,
            "signal_confidence": signal_confidence,
            "market_conditions": market_conditions,
            "strategy": strategy,
            "current_price": current_price,
            "market_volatility": market_volatility,
            "stop_loss_pips": stop_loss_pips,
            "take_profit_pips": take_profit_pips
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
        
        # 最終注文取得
        final_order = self.node_cache.get("191^84-001")
        
        if final_order:
            # 履歴に追加
            self.order_history.append(final_order)
            
            # アクティブ注文として管理
            self.active_orders[final_order.order_id] = final_order
            
            # 履歴サイズ制限
            if len(self.order_history) > 1000:
                self.order_history = self.order_history[-1000:]
            
            return final_order
        else:
            # デフォルト注文（エラー時）
            return self._create_default_order()
    
    # ===== 階層80: 注文準備関数 =====
    
    def _validate_order(self, unified_signal: Any, position_size: Any,
                       risk_metrics: Any) -> Dict[str, Any]:
        """注文を検証"""
        validation_result = {
            "is_valid": True,
            "reasons": [],
            "signal_strength": 0.0,
            "position_units": 0
        }
        
        # 信号の有効性チェック
        if not unified_signal:
            validation_result["is_valid"] = False
            validation_result["reasons"].append("No signal")
            return validation_result
        
        # ポジションサイズチェック
        if not position_size or position_size.units <= 0:
            validation_result["is_valid"] = False
            validation_result["reasons"].append("Invalid position size")
            return validation_result
        
        # リスクレベルチェック
        if risk_metrics and hasattr(risk_metrics, "risk_level"):
            from src.pkg.financial_dag import RiskLevel
            if risk_metrics.risk_level == RiskLevel.EXTREME:
                validation_result["is_valid"] = False
                validation_result["reasons"].append("Risk too high")
                return validation_result
        
        # 有効な注文として詳細を設定
        validation_result["signal_strength"] = getattr(unified_signal, "confidence", 0.5)
        validation_result["position_units"] = position_size.units
        
        return validation_result
    
    def _determine_timing(self, market_data: Dict[str, Any],
                         signal_confidence: float) -> Dict[str, Any]:
        """注文タイミングを判定"""
        # スプレッドチェック
        spread = market_data.get("spread", 1.0)
        max_spread = 2.0  # 最大許容スプレッド
        
        # ボラティリティチェック
        volatility = market_data.get("volatility", 0.01)
        
        # タイミング判定
        timing_score = signal_confidence
        
        if spread > max_spread:
            timing_score *= 0.5  # スプレッドが広い場合はスコア減少
        
        if volatility > 0.03:  # 高ボラティリティ
            timing_score *= 0.8  # 少し慎重に
        
        return {
            "should_execute_now": timing_score > 0.5,
            "timing_score": timing_score,
            "spread": spread,
            "volatility": volatility
        }
    
    def _select_order_type(self, market_conditions: Dict[str, Any],
                          strategy: str) -> Dict[str, Any]:
        """注文タイプを選択"""
        # デフォルトは成行注文
        order_type = OrderType.MARKET
        
        # 市場条件による選択
        if market_conditions.get("is_ranging", False):
            # レンジ相場では指値注文を優先
            order_type = OrderType.LIMIT
        elif market_conditions.get("is_trending", False):
            # トレンド相場では成行注文
            order_type = OrderType.MARKET
        
        # 戦略による調整
        if strategy == "scalping":
            order_type = OrderType.MARKET  # スキャルピングは即座実行
        elif strategy == "swing":
            order_type = OrderType.LIMIT   # スイングは指値で待つ
        
        return {
            "order_type": order_type,
            "reason": f"Market: {market_conditions}, Strategy: {strategy}"
        }
    
    # ===== 階層81: 価格計算関数 =====
    
    def _calculate_entry_price(self, validation: Dict[str, Any],
                              timing: Dict[str, Any],
                              current_price: float) -> Dict[str, Any]:
        """エントリー価格を計算"""
        if not validation.get("is_valid", False):
            return {"entry_price": 0.0, "is_valid": False}
        
        # 基本はcurrent_price
        entry_price = current_price
        
        # タイミングによる調整
        if not timing.get("should_execute_now", False):
            # 待機する場合は少し有利な価格を狙う
            entry_price *= 0.999  # 0.1%有利な価格
        
        return {
            "entry_price": entry_price,
            "is_valid": True,
            "adjustment": "immediate" if timing.get("should_execute_now") else "wait"
        }
    
    def _adjust_for_slippage(self, order_type_info: Dict[str, Any],
                            market_volatility: float) -> Dict[str, Any]:
        """スリッページを調整"""
        order_type = order_type_info.get("order_type", OrderType.MARKET)
        
        # スリッページ推定
        base_slippage = 0.0001  # 0.01% (1pip)
        
        if order_type == OrderType.MARKET:
            # 成行注文はスリッページが発生しやすい
            slippage = base_slippage * (1 + market_volatility * 10)
        else:
            # 指値注文はスリッページなし
            slippage = 0.0
        
        return {
            "slippage": slippage,
            "slippage_pips": slippage * 10000,  # pip換算
            "volatility_factor": market_volatility
        }
    
    # ===== 階層82: 注文構築関数 =====
    
    def _construct_order(self, price_info: Dict[str, Any],
                        slippage_info: Dict[str, Any],
                        position_size: Any) -> Dict[str, Any]:
        """注文を構築"""
        if not price_info.get("is_valid", False):
            return {"order": None, "error": "Invalid price"}
        
        # 注文詳細を構築
        entry_price = price_info.get("entry_price", 0.0)
        slippage = slippage_info.get("slippage", 0.0)
        
        # スリッページ調整後の価格
        adjusted_price = entry_price * (1 + slippage)
        
        # 売買方向の決定（簡易版）
        side = OrderSide.BUY if position_size.units > 0 else OrderSide.SELL
        
        order_details = {
            "side": side,
            "units": abs(position_size.units),
            "price": adjusted_price,
            "original_price": entry_price,
            "slippage": slippage
        }
        
        return order_details
    
    def _add_protection_levels(self, price_info: Dict[str, Any],
                              stop_loss_pips: float,
                              take_profit_pips: float) -> Dict[str, Any]:
        """保護レベル（SL/TP）を設定"""
        entry_price = price_info.get("entry_price", 0.0)
        
        if entry_price <= 0:
            return {"stop_loss": 0.0, "take_profit": 0.0}
        
        # pip値の計算（JPY通貨ペアの場合）
        pip_value = 0.01 if "JPY" in self.currency_pair else 0.0001
        
        # SL/TP価格計算
        stop_loss = entry_price - (stop_loss_pips * pip_value)
        take_profit = entry_price + (take_profit_pips * pip_value)
        
        return {
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "stop_loss_pips": stop_loss_pips,
            "take_profit_pips": take_profit_pips
        }
    
    # ===== 階層83: 注文送信関数 =====
    
    def _submit_order(self, order_details: Dict[str, Any],
                     protection: Dict[str, Any]) -> Dict[str, Any]:
        """注文を送信"""
        if not order_details or "error" in order_details:
            return {"status": "failed", "error": order_details.get("error", "Unknown")}
        
        # 注文ID生成
        order_id = f"ORD_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        
        # 注文送信（シミュレーション）
        submission_result = {
            "order_id": order_id,
            "status": "submitted",
            "timestamp": datetime.now(),
            "details": order_details,
            "protection": protection
        }
        
        logger.info(f"Order submitted: {order_id}")
        
        return submission_result
    
    def _confirm_order(self, order_details: Dict[str, Any],
                      protection: Dict[str, Any]) -> Dict[str, Any]:
        """注文を確認"""
        # 前段階の送信結果を取得
        submission = self.node_cache.get("191^83-001", {})
        
        if submission.get("status") != "submitted":
            return {"confirmed": False, "reason": "Not submitted"}
        
        # 注文確認（シミュレーション）
        confirmation = {
            "confirmed": True,
            "order_id": submission.get("order_id"),
            "execution_status": "pending",
            "timestamp": datetime.now()
        }
        
        return confirmation
    
    # ===== 階層84: 注文管理関数 =====
    
    def _track_order(self, confirmation: Dict[str, Any]) -> TradingOrder:
        """注文を追跡"""
        if not confirmation.get("confirmed", False):
            return self._create_default_order()
        
        # 前段階のデータから注文オブジェクトを構築
        order_details = self.node_cache.get("191^82-001", {})
        protection = self.node_cache.get("191^82-002", {})
        
        order = TradingOrder(
            order_id=confirmation.get("order_id", ""),
            timestamp=confirmation.get("timestamp", datetime.now()),
            currency_pair=self.currency_pair,
            side=order_details.get("side", OrderSide.BUY),
            order_type=OrderType.MARKET,  # デフォルト
            units=order_details.get("units", 0),
            price=order_details.get("price"),
            stop_price=None,
            take_profit=protection.get("take_profit"),
            stop_loss=protection.get("stop_loss"),
            time_in_force="GTC",  # Good Till Cancelled
            status=OrderStatus.PENDING,
            metadata={
                "slippage": order_details.get("slippage", 0),
                "protection": protection
            }
        )
        
        return order
    
    def _create_default_order(self) -> TradingOrder:
        """デフォルト注文を作成（エラー時）"""
        return TradingOrder(
            order_id="ERROR_" + datetime.now().strftime("%Y%m%d%H%M%S"),
            timestamp=datetime.now(),
            currency_pair=self.currency_pair,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            units=0,
            price=None,
            stop_price=None,
            take_profit=None,
            stop_loss=None,
            time_in_force="GTC",
            status=OrderStatus.REJECTED,
            metadata={"error": "Failed to create order"}
        )
    
    def get_order_history(self, limit: int = 10) -> List[TradingOrder]:
        """注文履歴を取得"""
        return self.order_history[-limit:] if self.order_history else []
    
    def get_active_orders(self) -> Dict[str, TradingOrder]:
        """アクティブ注文を取得"""
        return dict(self.active_orders)
    
    def cancel_order(self, order_id: str) -> bool:
        """注文をキャンセル"""
        if order_id in self.active_orders:
            order = self.active_orders[order_id]
            order.status = OrderStatus.CANCELLED
            del self.active_orders[order_id]
            logger.info(f"Order cancelled: {order_id}")
            return True
        return False