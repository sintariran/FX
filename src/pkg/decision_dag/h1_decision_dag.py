"""
H1（1時間足）判定DAG実装
中期トレード用の判定ロジック

階層範囲: 50-59
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass

from .m1_decision_dag import SignalType

logger = logging.getLogger(__name__)

@dataclass
class H1Signal:
    """H1信号データ"""
    timestamp: datetime
    signal_type: SignalType
    confidence: float
    components: Dict[str, Any]
    metadata: Dict[str, Any]
    trend_phase: str = ""       # トレンドフェーズ
    major_level: str = ""        # 主要レベル
    momentum_state: str = ""     # モメンタム状態

class H1DecisionDAG:
    """H1判定DAGクラス（中期判定）"""
    
    def __init__(self, currency_pair: str = "USDJPY"):
        self.currency_pair = currency_pair
        self.timeframe = "H1"
        self.currency_code = self._get_currency_code(currency_pair)
        
        # DAGノード定義
        self.nodes = self._define_nodes()
        self.execution_order = self._determine_execution_order()
        
        # 内部状態
        self.signal_history: List[H1Signal] = []
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
        
        # 階層50: 基本判定
        nodes["591^50-001"] = {
            "name": "trend_phase_analysis",
            "layer": 50,
            "inputs": ["feature_bundle"],
            "function": self._trend_phase_analysis,
            "description": "トレンドフェーズ分析"
        }
        
        nodes["591^50-002"] = {
            "name": "major_level_detection",
            "layer": 50,
            "inputs": ["feature_bundle"],
            "function": self._major_level_detection,
            "description": "主要レベル検出"
        }
        
        nodes["591^50-003"] = {
            "name": "momentum_analysis",
            "layer": 50,
            "inputs": ["feature_bundle"],
            "function": self._momentum_analysis,
            "description": "モメンタム分析"
        }
        
        # 階層51: 複合判定
        nodes["591^51-001"] = {
            "name": "swing_trade_signal",
            "layer": 51,
            "inputs": ["591^50-001", "591^50-002", "591^50-003"],
            "function": self._swing_trade_signal,
            "description": "スイングトレード信号"
        }
        
        nodes["591^51-002"] = {
            "name": "position_hold_signal",
            "layer": 51,
            "inputs": ["591^50-001", "591^50-003"],
            "function": self._position_hold_signal,
            "description": "ポジション保有判定"
        }
        
        # 階層52: 統合判定
        nodes["591^52-001"] = {
            "name": "integrated_h1_signal",
            "layer": 52,
            "inputs": ["591^51-001", "591^51-002"],
            "function": self._integrated_h1_signal,
            "description": "H1統合信号"
        }
        
        # 階層53: 最終判定
        nodes["591^53-001"] = {
            "name": "final_h1_signal",
            "layer": 53,
            "inputs": ["591^52-001"],
            "function": self._final_h1_signal,
            "description": "H1最終信号"
        }
        
        return nodes
    
    def _determine_execution_order(self) -> List[str]:
        """実行順序を決定"""
        return [
            "591^50-001", "591^50-002", "591^50-003",  # 階層50
            "591^51-001", "591^51-002",                # 階層51
            "591^52-001",                               # 階層52
            "591^53-001"                                # 階層53
        ]
    
    def process(self, feature_bundle: Dict[str, Any]) -> H1Signal:
        """特徴量バンドルを処理してH1信号を生成"""
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
        final_signal = self.node_cache.get("591^53-001")
        
        if final_signal:
            self.signal_history.append(final_signal)
            if len(self.signal_history) > 100:
                self.signal_history = self.signal_history[-100:]
            return final_signal
        else:
            return H1Signal(
                timestamp=datetime.now(),
                signal_type=SignalType.NEUTRAL,
                confidence=0.0,
                components={},
                metadata={"error": "Failed to generate signal"},
                trend_phase="",
                major_level="",
                momentum_state=""
            )
    
    # ===== 階層50: 基本判定関数 =====
    
    def _trend_phase_analysis(self, feature_bundle: Dict[str, Any]) -> Dict[str, Any]:
        """トレンドフェーズ分析"""
        features = feature_bundle.get("features", {})
        
        # トレンド安定性取得
        stability_key = f"{self.currency_pair}_{self.timeframe}_trend_stability"
        trend_stability = 0.5
        
        # 簡易実装
        if trend_stability > 0.7:
            phase = "established_trend"
            direction = SignalType.BUY
            strength = 0.8
        elif trend_stability < 0.3:
            phase = "trend_reversal"
            direction = SignalType.SELL
            strength = 0.6
        else:
            phase = "trend_formation"
            direction = SignalType.NEUTRAL
            strength = 0.4
        
        return {
            "phase": phase,
            "direction": direction,
            "strength": strength,
            "stability": trend_stability
        }
    
    def _major_level_detection(self, feature_bundle: Dict[str, Any]) -> Dict[str, Any]:
        """主要レベル検出"""
        features = feature_bundle.get("features", {})
        
        # 簡易的な主要レベル判定
        # 実際には日足・週足のサポート・レジスタンスを参照
        return {
            "level_type": "resistance",
            "distance_pips": 15,
            "strength": 0.7,
            "action": "watch_reversal"
        }
    
    def _momentum_analysis(self, feature_bundle: Dict[str, Any]) -> Dict[str, Any]:
        """モメンタム分析"""
        features = feature_bundle.get("features", {})
        
        # モメンタム強度と加速度から状態判定
        momentum_key = f"{self.currency_pair}_{self.timeframe}_momentum_strength"
        acceleration_key = f"{self.currency_pair}_{self.timeframe}_momentum_acceleration"
        
        momentum = 0.5  # デフォルト
        acceleration = 0.0
        
        if momentum > 0.6 and acceleration > 0:
            state = "accelerating"
            signal = SignalType.BUY
            confidence = 0.7
        elif momentum < 0.4 and acceleration < 0:
            state = "decelerating"
            signal = SignalType.SELL
            confidence = 0.6
        else:
            state = "stable"
            signal = SignalType.NEUTRAL
            confidence = 0.4
        
        return {
            "state": state,
            "direction": signal,
            "confidence": confidence,
            "momentum": momentum,
            "acceleration": acceleration
        }
    
    # ===== 階層51: 複合判定関数 =====
    
    def _swing_trade_signal(self, trend: Dict[str, Any],
                           level: Dict[str, Any],
                           momentum: Dict[str, Any]) -> Dict[str, Any]:
        """スイングトレード信号"""
        if not trend or not level or not momentum:
            return {"swing": False}
        
        phase = trend.get("phase", "")
        level_type = level.get("level_type", "")
        momentum_state = momentum.get("state", "")
        
        # スイングトレード条件
        if (phase == "established_trend" and 
            momentum_state == "accelerating" and
            level_type != "resistance"):
            return {
                "swing": True,
                "direction": trend.get("direction", SignalType.NEUTRAL),
                "confidence": 0.7,
                "hold_periods": 12,  # 12時間保有目安
                "type": "trend_continuation"
            }
        elif (phase == "trend_reversal" and
              level_type in ["support", "resistance"]):
            return {
                "swing": True,
                "direction": momentum.get("direction", SignalType.NEUTRAL),
                "confidence": 0.6,
                "hold_periods": 8,
                "type": "reversal_trade"
            }
        else:
            return {"swing": False}
    
    def _position_hold_signal(self, trend: Dict[str, Any],
                             momentum: Dict[str, Any]) -> Dict[str, Any]:
        """ポジション保有判定"""
        if not trend or not momentum:
            return {"hold": False}
        
        phase = trend.get("phase", "")
        momentum_state = momentum.get("state", "")
        
        if phase == "established_trend" and momentum_state != "decelerating":
            return {
                "hold": True,
                "action": "maintain_position",
                "trailing_stop": True,
                "confidence": 0.7
            }
        elif momentum_state == "decelerating":
            return {
                "hold": False,
                "action": "close_position",
                "trailing_stop": False,
                "confidence": 0.6
            }
        else:
            return {
                "hold": True,
                "action": "reduce_position",
                "trailing_stop": True,
                "confidence": 0.5
            }
    
    # ===== 階層52: 統合判定関数 =====
    
    def _integrated_h1_signal(self, swing: Dict[str, Any],
                             hold: Dict[str, Any]) -> Dict[str, Any]:
        """H1統合信号"""
        # スイング新規 > ポジション調整の優先順位
        if swing and swing.get("swing", False):
            return {
                "signal": swing.get("direction", SignalType.NEUTRAL),
                "confidence": swing.get("confidence", 0.5),
                "action": "new_swing",
                "hold_periods": swing.get("hold_periods", 8),
                "type": swing.get("type", "")
            }
        elif hold:
            action = hold.get("action", "maintain_position")
            if action == "close_position":
                return {
                    "signal": SignalType.NEUTRAL,
                    "confidence": hold.get("confidence", 0.5),
                    "action": action,
                    "hold_periods": 0,
                    "type": "exit"
                }
            else:
                return {
                    "signal": SignalType.NEUTRAL,
                    "confidence": hold.get("confidence", 0.5),
                    "action": action,
                    "hold_periods": 0,
                    "type": "position_management"
                }
        else:
            return {
                "signal": SignalType.NEUTRAL,
                "confidence": 0.0,
                "action": "wait",
                "hold_periods": 0,
                "type": "no_action"
            }
    
    # ===== 階層53: 最終判定関数 =====
    
    def _final_h1_signal(self, integrated: Dict[str, Any]) -> H1Signal:
        """最終H1信号"""
        signal_type = integrated.get("signal", SignalType.NEUTRAL)
        confidence = integrated.get("confidence", 0.0)
        
        # 中期トレードの信号強度調整
        if confidence > 0.7:
            if signal_type == SignalType.BUY:
                signal_type = SignalType.BUY_STRONG
            elif signal_type == SignalType.SELL:
                signal_type = SignalType.SELL_STRONG
        
        # キャッシュから追加情報取得
        trend_data = self.node_cache.get("591^50-001", {})
        level_data = self.node_cache.get("591^50-002", {})
        momentum_data = self.node_cache.get("591^50-003", {})
        
        return H1Signal(
            timestamp=datetime.now(),
            signal_type=signal_type,
            confidence=confidence,
            components={
                "action": integrated.get("action", "unknown"),
                "hold_periods": integrated.get("hold_periods", 0),
                "type": integrated.get("type", ""),
                "integrated": integrated
            },
            metadata={
                "timeframe": self.timeframe,
                "currency_pair": self.currency_pair,
                "strategy": "swing_trade"
            },
            trend_phase=trend_data.get("phase", ""),
            major_level=level_data.get("level_type", ""),
            momentum_state=momentum_data.get("state", "")
        )