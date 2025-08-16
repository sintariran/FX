"""
M1（1分足）判定DAG実装
スキャルピング用の高速判定ロジック

階層範囲: 20-29
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class SignalType(Enum):
    """信号タイプ定義"""
    BUY_STRONG = 5      # 強い買い
    BUY = 4             # 買い
    BUY_WEAK = 3        # 弱い買い
    NEUTRAL = 0         # 中立
    SELL_WEAK = -3      # 弱い売り
    SELL = -4           # 売り
    SELL_STRONG = -5    # 強い売り

@dataclass
class M1Signal:
    """M1信号データ"""
    timestamp: datetime
    signal_type: SignalType
    confidence: float
    components: Dict[str, Any]
    metadata: Dict[str, Any]

class M1DecisionDAG:
    """M1判定DAGクラス"""
    
    def __init__(self, currency_pair: str = "USDJPY"):
        self.currency_pair = currency_pair
        self.timeframe = "M1"
        self.currency_code = self._get_currency_code(currency_pair)
        
        # DAGノード定義
        self.nodes = self._define_nodes()
        self.execution_order = self._determine_execution_order()
        
        # 内部状態
        self.signal_history: List[M1Signal] = []
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
        
        # 階層20: 基本信号判定
        nodes["191^20-001"] = {
            "name": "price_momentum_signal",
            "layer": 20,
            "inputs": ["feature_bundle"],
            "function": self._price_momentum_signal,
            "description": "価格モメンタム信号"
        }
        
        nodes["191^20-002"] = {
            "name": "volume_spike_signal",
            "layer": 20,
            "inputs": ["feature_bundle"],
            "function": self._volume_spike_signal,
            "description": "出来高スパイク信号"
        }
        
        nodes["191^20-003"] = {
            "name": "spread_quality_signal",
            "layer": 20,
            "inputs": ["feature_bundle"],
            "function": self._spread_quality_signal,
            "description": "スプレッド品質信号"
        }
        
        # 階層21: 複合信号判定
        nodes["191^21-001"] = {
            "name": "scalping_entry_signal",
            "layer": 21,
            "inputs": ["191^20-001", "191^20-002", "191^20-003"],
            "function": self._scalping_entry_signal,
            "description": "スキャルピングエントリー信号"
        }
        
        nodes["191^21-002"] = {
            "name": "quick_reversal_signal",
            "layer": 21,
            "inputs": ["191^20-001", "191^20-002"],
            "function": self._quick_reversal_signal,
            "description": "急速反転信号"
        }
        
        # 階層22: リスク調整
        nodes["191^22-001"] = {
            "name": "risk_adjusted_signal",
            "layer": 22,
            "inputs": ["191^21-001", "191^21-002"],
            "function": self._risk_adjusted_signal,
            "description": "リスク調整済み信号"
        }
        
        # 階層23: 最終判定
        nodes["191^23-001"] = {
            "name": "final_m1_signal",
            "layer": 23,
            "inputs": ["191^22-001"],
            "function": self._final_m1_signal,
            "description": "M1最終信号"
        }
        
        return nodes
    
    def _determine_execution_order(self) -> List[str]:
        """実行順序を決定（トポロジカルソート）"""
        return [
            "191^20-001", "191^20-002", "191^20-003",  # 階層20
            "191^21-001", "191^21-002",                # 階層21
            "191^22-001",                               # 階層22
            "191^23-001"                                # 階層23
        ]
    
    def process(self, feature_bundle: Dict[str, Any]) -> M1Signal:
        """特徴量バンドルを処理してM1信号を生成"""
        # コンテキスト初期化
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
                    logger.warning(f"Missing input {input_id} for node {node_id}")
                    inputs.append(None)
            
            # ノード実行
            try:
                result = node["function"](*inputs)
                self.node_cache[node_id] = result
                
            except Exception as e:
                logger.error(f"Error executing node {node_id}: {e}")
                self.node_cache[node_id] = None
        
        # 最終信号取得
        final_signal = self.node_cache.get("191^23-001")
        
        if final_signal:
            # 履歴に追加
            self.signal_history.append(final_signal)
            
            # 履歴サイズ制限
            if len(self.signal_history) > 100:
                self.signal_history = self.signal_history[-100:]
            
            return final_signal
        else:
            # デフォルト信号
            return M1Signal(
                timestamp=datetime.now(),
                signal_type=SignalType.NEUTRAL,
                confidence=0.0,
                components={},
                metadata={"error": "Failed to generate signal"}
            )
    
    # ===== 階層20: 基本信号判定関数 =====
    
    def _price_momentum_signal(self, feature_bundle: Dict[str, Any]) -> Dict[str, Any]:
        """価格モメンタム信号を生成"""
        features = feature_bundle.get("features", {})
        
        # モメンタム値取得
        momentum_key = f"{self.currency_pair}_{self.timeframe}_price_momentum"
        momentum = features.get(momentum_key, {}).get("value", 0.0) if momentum_key in features else 0.0
        
        # 信号判定
        if momentum > 0.001:  # 0.1%以上の上昇
            signal_strength = min(momentum * 100, 1.0)  # 正規化
            return {
                "signal": SignalType.BUY,
                "strength": signal_strength,
                "momentum": momentum
            }
        elif momentum < -0.001:  # 0.1%以上の下落
            signal_strength = min(abs(momentum) * 100, 1.0)
            return {
                "signal": SignalType.SELL,
                "strength": signal_strength,
                "momentum": momentum
            }
        else:
            return {
                "signal": SignalType.NEUTRAL,
                "strength": 0.0,
                "momentum": momentum
            }
    
    def _volume_spike_signal(self, feature_bundle: Dict[str, Any]) -> Dict[str, Any]:
        """出来高スパイク信号を生成"""
        features = feature_bundle.get("features", {})
        
        # 簡易実装（実際にはvolume_spike_ratioを使用）
        volume_spike = 1.0  # デフォルト値
        
        if volume_spike > 2.0:  # 2倍以上のスパイク
            return {
                "spike_detected": True,
                "spike_ratio": volume_spike,
                "signal_boost": 0.3  # 信号強化
            }
        else:
            return {
                "spike_detected": False,
                "spike_ratio": volume_spike,
                "signal_boost": 0.0
            }
    
    def _spread_quality_signal(self, feature_bundle: Dict[str, Any]) -> Dict[str, Any]:
        """スプレッド品質信号を生成"""
        quality_metrics = feature_bundle.get("quality_summary", {})
        overall_quality = quality_metrics.get("overall_quality", 0.5)
        
        if overall_quality > 0.8:
            return {
                "quality": "excellent",
                "score": overall_quality,
                "trade_allowed": True
            }
        elif overall_quality > 0.6:
            return {
                "quality": "good",
                "score": overall_quality,
                "trade_allowed": True
            }
        else:
            return {
                "quality": "poor",
                "score": overall_quality,
                "trade_allowed": False
            }
    
    # ===== 階層21: 複合信号判定関数 =====
    
    def _scalping_entry_signal(self, momentum_signal: Dict[str, Any], 
                              volume_signal: Dict[str, Any],
                              spread_signal: Dict[str, Any]) -> Dict[str, Any]:
        """スキャルピングエントリー信号を生成"""
        if not momentum_signal or not volume_signal or not spread_signal:
            return {"entry": False, "reason": "Missing signals"}
        
        # エントリー条件判定
        entry_conditions = [
            spread_signal.get("trade_allowed", False),
            momentum_signal.get("signal") != SignalType.NEUTRAL,
            momentum_signal.get("strength", 0) > 0.3
        ]
        
        if all(entry_conditions):
            # 信号強度計算
            base_strength = momentum_signal.get("strength", 0)
            volume_boost = volume_signal.get("signal_boost", 0)
            final_strength = min(base_strength + volume_boost, 1.0)
            
            return {
                "entry": True,
                "direction": momentum_signal.get("signal"),
                "strength": final_strength,
                "type": "scalping"
            }
        else:
            return {
                "entry": False,
                "reason": "Conditions not met"
            }
    
    def _quick_reversal_signal(self, momentum_signal: Dict[str, Any],
                              volume_signal: Dict[str, Any]) -> Dict[str, Any]:
        """急速反転信号を生成"""
        if not momentum_signal or not volume_signal:
            return {"reversal": False}
        
        # 反転条件判定（簡易版）
        if (abs(momentum_signal.get("momentum", 0)) > 0.002 and 
            volume_signal.get("spike_detected", False)):
            
            return {
                "reversal": True,
                "direction": momentum_signal.get("signal"),
                "confidence": 0.7
            }
        else:
            return {"reversal": False}
    
    # ===== 階層22: リスク調整関数 =====
    
    def _risk_adjusted_signal(self, entry_signal: Dict[str, Any],
                             reversal_signal: Dict[str, Any]) -> Dict[str, Any]:
        """リスク調整済み信号を生成"""
        if not entry_signal and not reversal_signal:
            return {"adjusted_signal": SignalType.NEUTRAL, "confidence": 0.0}
        
        # 優先順位判定
        if reversal_signal and reversal_signal.get("reversal", False):
            # 反転信号優先
            return {
                "adjusted_signal": reversal_signal.get("direction", SignalType.NEUTRAL),
                "confidence": reversal_signal.get("confidence", 0.5),
                "source": "reversal"
            }
        elif entry_signal and entry_signal.get("entry", False):
            # エントリー信号
            return {
                "adjusted_signal": entry_signal.get("direction", SignalType.NEUTRAL),
                "confidence": entry_signal.get("strength", 0.5),
                "source": "scalping"
            }
        else:
            return {
                "adjusted_signal": SignalType.NEUTRAL,
                "confidence": 0.0,
                "source": "none"
            }
    
    # ===== 階層23: 最終判定関数 =====
    
    def _final_m1_signal(self, risk_adjusted: Dict[str, Any]) -> M1Signal:
        """最終M1信号を生成"""
        if not risk_adjusted:
            signal_type = SignalType.NEUTRAL
            confidence = 0.0
        else:
            signal_type = risk_adjusted.get("adjusted_signal", SignalType.NEUTRAL)
            confidence = risk_adjusted.get("confidence", 0.0)
        
        # 信号強度による分類
        if signal_type in [SignalType.BUY, SignalType.SELL]:
            if confidence > 0.8:
                if signal_type == SignalType.BUY:
                    signal_type = SignalType.BUY_STRONG
                else:
                    signal_type = SignalType.SELL_STRONG
            elif confidence < 0.4:
                if signal_type == SignalType.BUY:
                    signal_type = SignalType.BUY_WEAK
                else:
                    signal_type = SignalType.SELL_WEAK
        
        return M1Signal(
            timestamp=datetime.now(),
            signal_type=signal_type,
            confidence=confidence,
            components={
                "source": risk_adjusted.get("source", "unknown"),
                "risk_adjusted": risk_adjusted
            },
            metadata={
                "timeframe": self.timeframe,
                "currency_pair": self.currency_pair,
                "node_count": len(self.nodes)
            }
        )
    
    def get_signal_history(self, limit: int = 10) -> List[M1Signal]:
        """信号履歴を取得"""
        return self.signal_history[-limit:] if self.signal_history else []
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """パフォーマンスメトリクスを取得"""
        if not self.signal_history:
            return {}
        
        # 信号タイプ別カウント
        signal_counts = {}
        for signal in self.signal_history:
            signal_type = signal.signal_type.value
            signal_counts[signal_type] = signal_counts.get(signal_type, 0) + 1
        
        # 平均信頼度
        confidences = [s.confidence for s in self.signal_history]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        return {
            "total_signals": len(self.signal_history),
            "signal_distribution": signal_counts,
            "average_confidence": avg_confidence,
            "last_signal": self.signal_history[-1].signal_type.name if self.signal_history else None
        }