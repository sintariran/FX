"""
H4（4時間足）判定DAG実装
長期トレード用の判定ロジック

階層範囲: 60-69
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass

from .m1_decision_dag import SignalType

logger = logging.getLogger(__name__)

@dataclass
class H4Signal:
    """H4信号データ"""
    timestamp: datetime
    signal_type: SignalType
    confidence: float
    components: Dict[str, Any]
    metadata: Dict[str, Any]
    macro_trend: str = ""        # マクロトレンド
    position_bias: str = ""      # ポジションバイアス
    risk_environment: str = ""   # リスク環境

class H4DecisionDAG:
    """H4判定DAGクラス（長期判定）"""
    
    def __init__(self, currency_pair: str = "USDJPY"):
        self.currency_pair = currency_pair
        self.timeframe = "H4"
        self.currency_code = self._get_currency_code(currency_pair)
        
        # DAGノード定義
        self.nodes = self._define_nodes()
        self.execution_order = self._determine_execution_order()
        
        # 内部状態
        self.signal_history: List[H4Signal] = []
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
        
        # 階層60: 基本判定
        nodes["691^60-001"] = {
            "name": "macro_trend_analysis",
            "layer": 60,
            "inputs": ["feature_bundle"],
            "function": self._macro_trend_analysis,
            "description": "マクロトレンド分析"
        }
        
        nodes["691^60-002"] = {
            "name": "position_bias_detection",
            "layer": 60,
            "inputs": ["feature_bundle"],
            "function": self._position_bias_detection,
            "description": "ポジションバイアス検出"
        }
        
        nodes["691^60-003"] = {
            "name": "risk_environment_assessment",
            "layer": 60,
            "inputs": ["feature_bundle"],
            "function": self._risk_environment_assessment,
            "description": "リスク環境評価"
        }
        
        # 階層61: 複合判定
        nodes["691^61-001"] = {
            "name": "position_sizing_signal",
            "layer": 61,
            "inputs": ["691^60-001", "691^60-003"],
            "function": self._position_sizing_signal,
            "description": "ポジションサイジング信号"
        }
        
        nodes["691^61-002"] = {
            "name": "directional_bias_signal",
            "layer": 61,
            "inputs": ["691^60-001", "691^60-002"],
            "function": self._directional_bias_signal,
            "description": "方向性バイアス信号"
        }
        
        # 階層62: 統合判定
        nodes["691^62-001"] = {
            "name": "integrated_h4_signal",
            "layer": 62,
            "inputs": ["691^61-001", "691^61-002"],
            "function": self._integrated_h4_signal,
            "description": "H4統合信号"
        }
        
        # 階層63: 最終判定
        nodes["691^63-001"] = {
            "name": "final_h4_signal",
            "layer": 63,
            "inputs": ["691^62-001"],
            "function": self._final_h4_signal,
            "description": "H4最終信号"
        }
        
        return nodes
    
    def _determine_execution_order(self) -> List[str]:
        """実行順序を決定"""
        return [
            "691^60-001", "691^60-002", "691^60-003",  # 階層60
            "691^61-001", "691^61-002",                # 階層61
            "691^62-001",                               # 階層62
            "691^63-001"                                # 階層63
        ]
    
    def process(self, feature_bundle: Dict[str, Any]) -> H4Signal:
        """特徴量バンドルを処理してH4信号を生成"""
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
        final_signal = self.node_cache.get("691^63-001")
        
        if final_signal:
            self.signal_history.append(final_signal)
            if len(self.signal_history) > 100:
                self.signal_history = self.signal_history[-100:]
            return final_signal
        else:
            return H4Signal(
                timestamp=datetime.now(),
                signal_type=SignalType.NEUTRAL,
                confidence=0.0,
                components={},
                metadata={"error": "Failed to generate signal"},
                macro_trend="",
                position_bias="",
                risk_environment=""
            )
    
    # ===== 階層60: 基本判定関数 =====
    
    def _macro_trend_analysis(self, feature_bundle: Dict[str, Any]) -> Dict[str, Any]:
        """マクロトレンド分析"""
        features = feature_bundle.get("features", {})
        
        # 長期トレンド判定（簡易版）
        # 実際には週足・月足データも参照
        unified_signal_key = f"{self.currency_pair}_{self.timeframe}_unified_signal"
        unified_signal = 0.5
        
        if unified_signal > 0.6:
            macro_trend = "bullish"
            strength = unified_signal
            duration_days = 10
        elif unified_signal < 0.4:
            macro_trend = "bearish"
            strength = 1.0 - unified_signal
            duration_days = 10
        else:
            macro_trend = "neutral"
            strength = 0.0
            duration_days = 0
        
        return {
            "macro_trend": macro_trend,
            "strength": strength,
            "expected_duration_days": duration_days,
            "confidence": 0.6
        }
    
    def _position_bias_detection(self, feature_bundle: Dict[str, Any]) -> Dict[str, Any]:
        """ポジションバイアス検出"""
        # 市場のポジション偏りを検出（簡易版）
        # 実際にはセンチメント指標やポジション比率を使用
        
        return {
            "bias": "long_heavy",  # long_heavy, short_heavy, balanced
            "ratio": 0.65,  # ロング比率
            "extreme_level": False,
            "reversal_risk": 0.3
        }
    
    def _risk_environment_assessment(self, feature_bundle: Dict[str, Any]) -> Dict[str, Any]:
        """リスク環境評価"""
        quality_metrics = feature_bundle.get("quality_summary", {})
        overall_quality = quality_metrics.get("overall_quality", 0.5)
        
        # ボラティリティとスプレッドから環境評価
        if overall_quality > 0.7:
            environment = "low_risk"
            max_position_ratio = 1.0
            recommended_leverage = 2.0
        elif overall_quality > 0.4:
            environment = "medium_risk"
            max_position_ratio = 0.7
            recommended_leverage = 1.0
        else:
            environment = "high_risk"
            max_position_ratio = 0.3
            recommended_leverage = 0.5
        
        return {
            "environment": environment,
            "max_position_ratio": max_position_ratio,
            "recommended_leverage": recommended_leverage,
            "quality_score": overall_quality
        }
    
    # ===== 階層61: 複合判定関数 =====
    
    def _position_sizing_signal(self, macro: Dict[str, Any],
                               risk: Dict[str, Any]) -> Dict[str, Any]:
        """ポジションサイジング信号"""
        if not macro or not risk:
            return {"size_recommendation": 0.0}
        
        trend_strength = macro.get("strength", 0.0)
        max_position = risk.get("max_position_ratio", 0.5)
        
        # トレンド強度とリスク環境からサイズ決定
        base_size = trend_strength * max_position
        
        return {
            "size_recommendation": base_size,
            "max_size": max_position,
            "leverage": risk.get("recommended_leverage", 1.0),
            "risk_adjusted": True
        }
    
    def _directional_bias_signal(self, macro: Dict[str, Any],
                                position: Dict[str, Any]) -> Dict[str, Any]:
        """方向性バイアス信号"""
        if not macro or not position:
            return {"bias": SignalType.NEUTRAL}
        
        macro_trend = macro.get("macro_trend", "neutral")
        position_bias = position.get("bias", "balanced")
        reversal_risk = position.get("reversal_risk", 0.0)
        
        # マクロトレンドとポジション偏りから方向性決定
        if macro_trend == "bullish":
            if position_bias == "short_heavy" or reversal_risk < 0.3:
                # ショート過多またはリバーサルリスク低 → 買い
                return {
                    "bias": SignalType.BUY,
                    "strength": 0.7,
                    "rationale": "trend_continuation"
                }
            else:
                # ロング過多 → 様子見
                return {
                    "bias": SignalType.NEUTRAL,
                    "strength": 0.3,
                    "rationale": "crowded_long"
                }
        elif macro_trend == "bearish":
            if position_bias == "long_heavy" or reversal_risk < 0.3:
                return {
                    "bias": SignalType.SELL,
                    "strength": 0.7,
                    "rationale": "trend_continuation"
                }
            else:
                return {
                    "bias": SignalType.NEUTRAL,
                    "strength": 0.3,
                    "rationale": "crowded_short"
                }
        else:
            return {
                "bias": SignalType.NEUTRAL,
                "strength": 0.0,
                "rationale": "no_clear_trend"
            }
    
    # ===== 階層62: 統合判定関数 =====
    
    def _integrated_h4_signal(self, sizing: Dict[str, Any],
                             direction: Dict[str, Any]) -> Dict[str, Any]:
        """H4統合信号"""
        if not sizing or not direction:
            return {"signal": SignalType.NEUTRAL, "confidence": 0.0}
        
        bias = direction.get("bias", SignalType.NEUTRAL)
        strength = direction.get("strength", 0.0)
        size = sizing.get("size_recommendation", 0.0)
        
        # サイズがゼロなら取引なし
        if size < 0.1:
            return {
                "signal": SignalType.NEUTRAL,
                "confidence": 0.0,
                "position_size": 0.0,
                "reason": "insufficient_size"
            }
        
        return {
            "signal": bias,
            "confidence": strength,
            "position_size": size,
            "leverage": sizing.get("leverage", 1.0),
            "rationale": direction.get("rationale", ""),
            "hold_days": 3  # 3日間保有目安
        }
    
    # ===== 階層63: 最終判定関数 =====
    
    def _final_h4_signal(self, integrated: Dict[str, Any]) -> H4Signal:
        """最終H4信号"""
        signal_type = integrated.get("signal", SignalType.NEUTRAL)
        confidence = integrated.get("confidence", 0.0)
        
        # 長期トレードは慎重に（強い信号のみ）
        if confidence < 0.6:
            signal_type = SignalType.NEUTRAL
        elif confidence > 0.8:
            if signal_type == SignalType.BUY:
                signal_type = SignalType.BUY_STRONG
            elif signal_type == SignalType.SELL:
                signal_type = SignalType.SELL_STRONG
        
        # キャッシュから追加情報取得
        macro_data = self.node_cache.get("691^60-001", {})
        position_data = self.node_cache.get("691^60-002", {})
        risk_data = self.node_cache.get("691^60-003", {})
        
        return H4Signal(
            timestamp=datetime.now(),
            signal_type=signal_type,
            confidence=confidence,
            components={
                "position_size": integrated.get("position_size", 0.0),
                "leverage": integrated.get("leverage", 1.0),
                "hold_days": integrated.get("hold_days", 0),
                "rationale": integrated.get("rationale", ""),
                "integrated": integrated
            },
            metadata={
                "timeframe": self.timeframe,
                "currency_pair": self.currency_pair,
                "strategy": "position_trade"
            },
            macro_trend=macro_data.get("macro_trend", ""),
            position_bias=position_data.get("bias", ""),
            risk_environment=risk_data.get("environment", "")
        )