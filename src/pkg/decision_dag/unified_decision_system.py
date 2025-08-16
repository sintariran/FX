"""
統合判定システム (Unified Decision System)
全時間足の判定を統合して最終取引判断を行う
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from .m1_decision_dag import M1DecisionDAG, M1Signal, SignalType
from .m5_decision_dag import M5DecisionDAG, M5Signal
from .m15_decision_dag import M15DecisionDAG, M15Signal
from .h1_decision_dag import H1DecisionDAG, H1Signal
from .h4_decision_dag import H4DecisionDAG, H4Signal

logger = logging.getLogger(__name__)

class TradingStrategy(Enum):
    """取引戦略タイプ"""
    SCALPING = "scalping"          # スキャルピング（M1主導）
    DAY_TRADE = "day_trade"        # デイトレード（M5/M15主導）
    SWING_TRADE = "swing_trade"    # スイングトレード（H1主導）
    POSITION_TRADE = "position_trade"  # ポジショントレード（H4主導）
    MIXED = "mixed"                 # 混合戦略

@dataclass
class UnifiedSignal:
    """統合信号データ"""
    timestamp: datetime
    primary_signal: SignalType
    confidence: float
    strategy: TradingStrategy
    position_size: float
    timeframe_signals: Dict[str, SignalType]
    components: Dict[str, Any]
    metadata: Dict[str, Any]
    
    def get_action(self) -> str:
        """取引アクションを取得"""
        if self.primary_signal in [SignalType.BUY_STRONG, SignalType.BUY]:
            return "BUY"
        elif self.primary_signal in [SignalType.SELL_STRONG, SignalType.SELL]:
            return "SELL"
        elif self.primary_signal in [SignalType.BUY_WEAK, SignalType.SELL_WEAK]:
            return "WAIT"
        else:
            return "NEUTRAL"

class UnifiedDecisionSystem:
    """統合判定システムクラス"""
    
    def __init__(self, currency_pair: str = "USDJPY", 
                 active_timeframes: Optional[List[str]] = None):
        self.currency_pair = currency_pair
        
        # アクティブな時間足（デフォルトは全て）
        if active_timeframes is None:
            active_timeframes = ["M1", "M5", "M15", "H1", "H4"]
        self.active_timeframes = active_timeframes
        
        # 各時間足のDAGを初期化
        self.dags = {}
        if "M1" in active_timeframes:
            self.dags["M1"] = M1DecisionDAG(currency_pair)
        if "M5" in active_timeframes:
            self.dags["M5"] = M5DecisionDAG(currency_pair)
        if "M15" in active_timeframes:
            self.dags["M15"] = M15DecisionDAG(currency_pair)
        if "H1" in active_timeframes:
            self.dags["H1"] = H1DecisionDAG(currency_pair)
        if "H4" in active_timeframes:
            self.dags["H4"] = H4DecisionDAG(currency_pair)
        
        # 時間足の重み付け（戦略による）
        self.timeframe_weights = {
            TradingStrategy.SCALPING: {"M1": 0.5, "M5": 0.3, "M15": 0.2, "H1": 0.0, "H4": 0.0},
            TradingStrategy.DAY_TRADE: {"M1": 0.1, "M5": 0.3, "M15": 0.4, "H1": 0.2, "H4": 0.0},
            TradingStrategy.SWING_TRADE: {"M1": 0.0, "M5": 0.1, "M15": 0.2, "H1": 0.5, "H4": 0.2},
            TradingStrategy.POSITION_TRADE: {"M1": 0.0, "M5": 0.0, "M15": 0.1, "H1": 0.3, "H4": 0.6},
            TradingStrategy.MIXED: {"M1": 0.1, "M5": 0.2, "M15": 0.3, "H1": 0.25, "H4": 0.15}
        }
        
        # 内部状態
        self.signal_history: List[UnifiedSignal] = []
        self.current_strategy = TradingStrategy.MIXED
        
    def process(self, feature_bundles: Dict[str, Dict[str, Any]], 
                strategy: Optional[TradingStrategy] = None) -> UnifiedSignal:
        """
        全時間足の特徴量バンドルを処理して統合信号を生成
        
        Args:
            feature_bundles: 時間足別の特徴量バンドル {"M1": {...}, "M5": {...}, ...}
            strategy: 使用する取引戦略（Noneの場合は自動選択）
        """
        # 戦略を決定
        if strategy is None:
            strategy = self._determine_strategy(feature_bundles)
        self.current_strategy = strategy
        
        # 各時間足の信号を生成
        timeframe_signals = {}
        signal_objects = {}
        
        for timeframe, dag in self.dags.items():
            if timeframe in feature_bundles:
                try:
                    signal = dag.process(feature_bundles[timeframe])
                    timeframe_signals[timeframe] = signal.signal_type
                    signal_objects[timeframe] = signal
                except Exception as e:
                    logger.error(f"Error processing {timeframe}: {e}")
                    timeframe_signals[timeframe] = SignalType.NEUTRAL
                    signal_objects[timeframe] = None
        
        # 統合信号を生成
        unified_signal = self._integrate_signals(signal_objects, strategy)
        
        # 履歴に追加
        self.signal_history.append(unified_signal)
        if len(self.signal_history) > 100:
            self.signal_history = self.signal_history[-100:]
        
        return unified_signal
    
    def _determine_strategy(self, feature_bundles: Dict[str, Dict[str, Any]]) -> TradingStrategy:
        """市場状態から最適な戦略を決定"""
        # M15のもみ合い状態をチェック（メイン時間足）
        if "M15" in feature_bundles:
            features = feature_bundles["M15"].get("features", {})
            momi_key = f"{self.currency_pair}_M15_momi_score"
            
            if momi_key in features:
                momi_score = features[momi_key].get("value", 0.0)
                
                if momi_score > 0.8:
                    # 強いもみ合い → スキャルピング
                    return TradingStrategy.SCALPING
                elif momi_score < 0.3:
                    # トレンド相場 → スイングトレード
                    return TradingStrategy.SWING_TRADE
        
        # H4のマクロトレンドをチェック
        if "H4" in feature_bundles:
            quality = feature_bundles["H4"].get("quality_summary", {}).get("overall_quality", 0.5)
            if quality > 0.7:
                # 高品質データ → ポジショントレード
                return TradingStrategy.POSITION_TRADE
        
        # デフォルトはデイトレード
        return TradingStrategy.DAY_TRADE
    
    def _integrate_signals(self, signal_objects: Dict[str, Any], 
                          strategy: TradingStrategy) -> UnifiedSignal:
        """時間足別信号を統合"""
        weights = self.timeframe_weights[strategy]
        
        # 重み付け投票による統合
        vote_scores = {
            SignalType.BUY_STRONG: 0.0,
            SignalType.BUY: 0.0,
            SignalType.BUY_WEAK: 0.0,
            SignalType.NEUTRAL: 0.0,
            SignalType.SELL_WEAK: 0.0,
            SignalType.SELL: 0.0,
            SignalType.SELL_STRONG: 0.0
        }
        
        total_confidence = 0.0
        position_size = 1.0
        
        for timeframe, signal in signal_objects.items():
            if signal is None:
                continue
                
            weight = weights.get(timeframe, 0.0)
            if weight > 0:
                vote_scores[signal.signal_type] += weight * signal.confidence
                total_confidence += weight * signal.confidence
                
                # M15の特別処理（メイン時間足）
                if timeframe == "M15" and hasattr(signal, "components"):
                    size_adj = signal.components.get("size_adjustment", 1.0)
                    position_size = min(position_size, size_adj)
        
        # 最も強い信号を選択
        primary_signal = SignalType.NEUTRAL
        max_score = 0.0
        
        for signal_type, score in vote_scores.items():
            if score > max_score:
                max_score = score
                primary_signal = signal_type
        
        # 信頼度の正規化
        confidence = min(total_confidence, 1.0)
        
        # 弱い信号のフィルタリング
        if confidence < 0.3:
            primary_signal = SignalType.NEUTRAL
        
        # H4のポジションサイズ調整を適用
        if "H4" in signal_objects and signal_objects["H4"]:
            h4_signal = signal_objects["H4"]
            if hasattr(h4_signal, "components"):
                h4_size = h4_signal.components.get("position_size", 1.0)
                position_size = min(position_size, h4_size)
        
        # 統合信号を構築
        return UnifiedSignal(
            timestamp=datetime.now(),
            primary_signal=primary_signal,
            confidence=confidence,
            strategy=strategy,
            position_size=position_size,
            timeframe_signals={tf: (sig.signal_type if sig else SignalType.NEUTRAL) 
                              for tf, sig in signal_objects.items()},
            components={
                "vote_scores": vote_scores,
                "max_score": max_score,
                "weights_used": weights
            },
            metadata={
                "currency_pair": self.currency_pair,
                "active_timeframes": list(self.dags.keys()),
                "integration_method": "weighted_voting"
            }
        )
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """パフォーマンスメトリクスを取得"""
        if not self.signal_history:
            return {}
        
        # 戦略別の使用頻度
        strategy_counts = {}
        for signal in self.signal_history:
            strategy = signal.strategy.value
            strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
        
        # 信号タイプ別の頻度
        signal_counts = {}
        for signal in self.signal_history:
            signal_type = signal.primary_signal.name
            signal_counts[signal_type] = signal_counts.get(signal_type, 0) + 1
        
        # 平均信頼度
        confidences = [s.confidence for s in self.signal_history]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        # 平均ポジションサイズ
        sizes = [s.position_size for s in self.signal_history]
        avg_size = sum(sizes) / len(sizes) if sizes else 0
        
        return {
            "total_signals": len(self.signal_history),
            "strategy_distribution": strategy_counts,
            "signal_distribution": signal_counts,
            "average_confidence": avg_confidence,
            "average_position_size": avg_size,
            "current_strategy": self.current_strategy.value
        }
    
    def get_current_state(self) -> Dict[str, Any]:
        """現在の状態を取得"""
        latest_signal = self.signal_history[-1] if self.signal_history else None
        
        return {
            "latest_signal": {
                "type": latest_signal.primary_signal.name if latest_signal else "NONE",
                "confidence": latest_signal.confidence if latest_signal else 0.0,
                "strategy": latest_signal.strategy.value if latest_signal else "none",
                "action": latest_signal.get_action() if latest_signal else "NEUTRAL"
            } if latest_signal else None,
            "active_timeframes": self.active_timeframes,
            "current_strategy": self.current_strategy.value,
            "signal_count": len(self.signal_history)
        }