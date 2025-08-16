"""
M5（5分足）判定DAG実装
短期トレード用の判定ロジック

階層範囲: 30-39
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass

from .m1_decision_dag import SignalType, M1Signal

logger = logging.getLogger(__name__)

@dataclass
class M5Signal(M1Signal):
    """M5信号データ（M1信号を継承）"""
    trend_strength: float = 0.0
    pattern_type: str = ""

class M5DecisionDAG:
    """M5判定DAGクラス"""
    
    def __init__(self, currency_pair: str = "USDJPY"):
        self.currency_pair = currency_pair
        self.timeframe = "M5"
        self.currency_code = self._get_currency_code(currency_pair)
        
        # DAGノード定義
        self.nodes = self._define_nodes()
        self.execution_order = self._determine_execution_order()
        
        # 内部状態
        self.signal_history: List[M5Signal] = []
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
        
        # 階層30: 基本信号判定
        nodes["291^30-001"] = {
            "name": "trend_detection",
            "layer": 30,
            "inputs": ["feature_bundle"],
            "function": self._trend_detection,
            "description": "トレンド検出"
        }
        
        nodes["291^30-002"] = {
            "name": "support_resistance",
            "layer": 30,
            "inputs": ["feature_bundle"],
            "function": self._support_resistance,
            "description": "サポート・レジスタンス判定"
        }
        
        nodes["291^30-003"] = {
            "name": "pattern_recognition",
            "layer": 30,
            "inputs": ["feature_bundle"],
            "function": self._pattern_recognition,
            "description": "パターン認識"
        }
        
        # 階層31: 複合信号判定
        nodes["291^31-001"] = {
            "name": "trend_follow_signal",
            "layer": 31,
            "inputs": ["291^30-001", "291^30-002"],
            "function": self._trend_follow_signal,
            "description": "トレンドフォロー信号"
        }
        
        nodes["291^31-002"] = {
            "name": "pattern_breakout_signal",
            "layer": 31,
            "inputs": ["291^30-002", "291^30-003"],
            "function": self._pattern_breakout_signal,
            "description": "パターンブレイクアウト信号"
        }
        
        # 階層32: 統合判定
        nodes["291^32-001"] = {
            "name": "integrated_m5_signal",
            "layer": 32,
            "inputs": ["291^31-001", "291^31-002"],
            "function": self._integrated_m5_signal,
            "description": "M5統合信号"
        }
        
        # 階層33: 最終判定
        nodes["291^33-001"] = {
            "name": "final_m5_signal",
            "layer": 33,
            "inputs": ["291^32-001"],
            "function": self._final_m5_signal,
            "description": "M5最終信号"
        }
        
        return nodes
    
    def _determine_execution_order(self) -> List[str]:
        """実行順序を決定"""
        return [
            "291^30-001", "291^30-002", "291^30-003",  # 階層30
            "291^31-001", "291^31-002",                # 階層31
            "291^32-001",                               # 階層32
            "291^33-001"                                # 階層33
        ]
    
    def process(self, feature_bundle: Dict[str, Any]) -> M5Signal:
        """特徴量バンドルを処理してM5信号を生成"""
        context = {"feature_bundle": feature_bundle}
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
                    inputs.append(None)
            
            # ノード実行
            try:
                result = node["function"](*inputs)
                self.node_cache[node_id] = result
            except Exception as e:
                logger.error(f"Error executing node {node_id}: {e}")
                self.node_cache[node_id] = None
        
        # 最終信号取得
        final_signal = self.node_cache.get("291^33-001")
        
        if final_signal:
            self.signal_history.append(final_signal)
            if len(self.signal_history) > 100:
                self.signal_history = self.signal_history[-100:]
            return final_signal
        else:
            return M5Signal(
                timestamp=datetime.now(),
                signal_type=SignalType.NEUTRAL,
                confidence=0.0,
                components={},
                metadata={"error": "Failed to generate signal"},
                trend_strength=0.0,
                pattern_type=""
            )
    
    # ===== 階層30: 基本信号判定関数 =====
    
    def _trend_detection(self, feature_bundle: Dict[str, Any]) -> Dict[str, Any]:
        """トレンド検出"""
        features = feature_bundle.get("features", {})
        
        # トレンド強度計算（簡易版）
        trend_strength = 0.5  # デフォルト
        
        # 信号強度取得
        signal_key = f"{self.currency_pair}_{self.timeframe}_signal_strength"
        if signal_key in features:
            trend_strength = features[signal_key].get("value", 0.5)
        
        if trend_strength > 0.6:
            return {
                "trend": "up",
                "strength": trend_strength,
                "confidence": 0.7
            }
        elif trend_strength < 0.4:
            return {
                "trend": "down",
                "strength": 1.0 - trend_strength,
                "confidence": 0.7
            }
        else:
            return {
                "trend": "sideways",
                "strength": 0.0,
                "confidence": 0.3
            }
    
    def _support_resistance(self, feature_bundle: Dict[str, Any]) -> Dict[str, Any]:
        """サポート・レジスタンス判定"""
        features = feature_bundle.get("features", {})
        
        # レンジ位置取得
        range_key = f"{self.currency_pair}_{self.timeframe}_range_position"
        range_position = 0.5
        if range_key in features:
            range_position = features[range_key].get("value", 0.5)
        
        if range_position > 0.8:
            return {
                "level": "resistance",
                "position": range_position,
                "action": "potential_reversal"
            }
        elif range_position < 0.2:
            return {
                "level": "support",
                "position": range_position,
                "action": "potential_bounce"
            }
        else:
            return {
                "level": "neutral",
                "position": range_position,
                "action": "none"
            }
    
    def _pattern_recognition(self, feature_bundle: Dict[str, Any]) -> Dict[str, Any]:
        """パターン認識"""
        features = feature_bundle.get("features", {})
        
        # もみ合いスコア取得
        momi_key = f"{self.currency_pair}_{self.timeframe}_momi_score"
        momi_score = 0.0
        if momi_key in features:
            momi_score = features[momi_key].get("value", 0.0)
        
        if momi_score > 0.7:
            return {
                "pattern": "consolidation",
                "score": momi_score,
                "breakout_potential": 0.6
            }
        else:
            return {
                "pattern": "trending",
                "score": 1.0 - momi_score,
                "breakout_potential": 0.2
            }
    
    # ===== 階層31: 複合信号判定関数 =====
    
    def _trend_follow_signal(self, trend_signal: Dict[str, Any],
                            sr_signal: Dict[str, Any]) -> Dict[str, Any]:
        """トレンドフォロー信号"""
        if not trend_signal or not sr_signal:
            return {"follow": False}
        
        trend = trend_signal.get("trend", "sideways")
        level = sr_signal.get("level", "neutral")
        
        # トレンドフォロー条件
        if trend == "up" and level != "resistance":
            return {
                "follow": True,
                "direction": SignalType.BUY,
                "strength": trend_signal.get("strength", 0.5),
                "type": "trend_follow"
            }
        elif trend == "down" and level != "support":
            return {
                "follow": True,
                "direction": SignalType.SELL,
                "strength": trend_signal.get("strength", 0.5),
                "type": "trend_follow"
            }
        else:
            return {"follow": False}
    
    def _pattern_breakout_signal(self, sr_signal: Dict[str, Any],
                                pattern_signal: Dict[str, Any]) -> Dict[str, Any]:
        """パターンブレイクアウト信号"""
        if not sr_signal or not pattern_signal:
            return {"breakout": False}
        
        pattern = pattern_signal.get("pattern", "")
        breakout_potential = pattern_signal.get("breakout_potential", 0.0)
        level = sr_signal.get("level", "neutral")
        
        if pattern == "consolidation" and breakout_potential > 0.5:
            if level == "resistance":
                return {
                    "breakout": True,
                    "direction": SignalType.BUY,
                    "confidence": breakout_potential,
                    "type": "breakout_up"
                }
            elif level == "support":
                return {
                    "breakout": True,
                    "direction": SignalType.SELL,
                    "confidence": breakout_potential,
                    "type": "breakout_down"
                }
        
        return {"breakout": False}
    
    # ===== 階層32: 統合判定関数 =====
    
    def _integrated_m5_signal(self, trend_signal: Dict[str, Any],
                             breakout_signal: Dict[str, Any]) -> Dict[str, Any]:
        """M5統合信号"""
        # 優先順位: ブレイクアウト > トレンドフォロー
        if breakout_signal and breakout_signal.get("breakout", False):
            return {
                "signal": breakout_signal.get("direction", SignalType.NEUTRAL),
                "confidence": breakout_signal.get("confidence", 0.5),
                "source": "breakout",
                "pattern_type": breakout_signal.get("type", "")
            }
        elif trend_signal and trend_signal.get("follow", False):
            return {
                "signal": trend_signal.get("direction", SignalType.NEUTRAL),
                "confidence": trend_signal.get("strength", 0.5),
                "source": "trend_follow",
                "pattern_type": trend_signal.get("type", "")
            }
        else:
            return {
                "signal": SignalType.NEUTRAL,
                "confidence": 0.0,
                "source": "none",
                "pattern_type": ""
            }
    
    # ===== 階層33: 最終判定関数 =====
    
    def _final_m5_signal(self, integrated: Dict[str, Any]) -> M5Signal:
        """最終M5信号"""
        signal_type = integrated.get("signal", SignalType.NEUTRAL)
        confidence = integrated.get("confidence", 0.0)
        pattern_type = integrated.get("pattern_type", "")
        
        # トレンド強度計算
        trend_strength = confidence if signal_type != SignalType.NEUTRAL else 0.0
        
        # 信号強度調整
        if confidence > 0.8:
            if signal_type == SignalType.BUY:
                signal_type = SignalType.BUY_STRONG
            elif signal_type == SignalType.SELL:
                signal_type = SignalType.SELL_STRONG
        elif confidence < 0.4:
            if signal_type == SignalType.BUY:
                signal_type = SignalType.BUY_WEAK
            elif signal_type == SignalType.SELL:
                signal_type = SignalType.SELL_WEAK
        
        return M5Signal(
            timestamp=datetime.now(),
            signal_type=signal_type,
            confidence=confidence,
            components={
                "source": integrated.get("source", "unknown"),
                "integrated": integrated
            },
            metadata={
                "timeframe": self.timeframe,
                "currency_pair": self.currency_pair
            },
            trend_strength=trend_strength,
            pattern_type=pattern_type
        )