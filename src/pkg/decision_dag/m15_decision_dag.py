"""
M15（15分足）判定DAG実装
メイン取引時間足の判定ロジック

階層範囲: 40-49
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass

from .m1_decision_dag import SignalType

logger = logging.getLogger(__name__)

@dataclass
class M15Signal:
    """M15信号データ"""
    timestamp: datetime
    signal_type: SignalType
    confidence: float
    components: Dict[str, Any]
    metadata: Dict[str, Any]
    dokyaku_score: float = 0.0  # 同逆スコア
    ikikaeri_pattern: str = ""  # 行帰パターン
    momi_state: str = ""         # もみ合い状態

class M15DecisionDAG:
    """M15判定DAGクラス（メインロジック）"""
    
    def __init__(self, currency_pair: str = "USDJPY"):
        self.currency_pair = currency_pair
        self.timeframe = "M15"
        self.currency_code = self._get_currency_code(currency_pair)
        
        # DAGノード定義
        self.nodes = self._define_nodes()
        self.execution_order = self._determine_execution_order()
        
        # 内部状態
        self.signal_history: List[M15Signal] = []
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
        """DAGノード定義（メモファイルのコア概念実装）"""
        nodes = {}
        
        # 階層40: 基本判定（メモファイル核心概念）
        nodes["391^40-001"] = {
            "name": "dokyaku_judgment",
            "layer": 40,
            "inputs": ["feature_bundle"],
            "function": self._dokyaku_judgment,
            "description": "同逆判定（前々足乖離による方向判断）"
        }
        
        nodes["391^40-002"] = {
            "name": "ikikaeri_judgment",
            "layer": 40,
            "inputs": ["feature_bundle"],
            "function": self._ikikaeri_judgment,
            "description": "行帰判定（前足の動きから今足の方向予測）"
        }
        
        nodes["391^40-003"] = {
            "name": "momi_judgment",
            "layer": 40,
            "inputs": ["feature_bundle"],
            "function": self._momi_judgment,
            "description": "もみ合い判定（レンジ幅3pips未満）"
        }
        
        nodes["391^40-004"] = {
            "name": "overshoot_detection",
            "layer": 40,
            "inputs": ["feature_bundle"],
            "function": self._overshoot_detection,
            "description": "オーバーシュート検出"
        }
        
        # 階層41: 複合判定
        nodes["391^41-001"] = {
            "name": "direction_consensus",
            "layer": 41,
            "inputs": ["391^40-001", "391^40-002"],
            "function": self._direction_consensus,
            "description": "方向性合意判定"
        }
        
        nodes["391^41-002"] = {
            "name": "market_state_analysis",
            "layer": 41,
            "inputs": ["391^40-003", "391^40-004"],
            "function": self._market_state_analysis,
            "description": "市場状態分析"
        }
        
        # 階層42: 統合判定
        nodes["391^42-001"] = {
            "name": "integrated_m15_signal",
            "layer": 42,
            "inputs": ["391^41-001", "391^41-002"],
            "function": self._integrated_m15_signal,
            "description": "M15統合信号（勝率55.7%目標）"
        }
        
        # 階層43: 最終判定
        nodes["391^43-001"] = {
            "name": "final_m15_signal",
            "layer": 43,
            "inputs": ["391^42-001"],
            "function": self._final_m15_signal,
            "description": "M15最終信号"
        }
        
        return nodes
    
    def _determine_execution_order(self) -> List[str]:
        """実行順序を決定"""
        return [
            "391^40-001", "391^40-002", "391^40-003", "391^40-004",  # 階層40
            "391^41-001", "391^41-002",                              # 階層41
            "391^42-001",                                             # 階層42
            "391^43-001"                                              # 階層43
        ]
    
    def process(self, feature_bundle: Dict[str, Any]) -> M15Signal:
        """特徴量バンドルを処理してM15信号を生成"""
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
        final_signal = self.node_cache.get("391^43-001")
        
        if final_signal:
            self.signal_history.append(final_signal)
            if len(self.signal_history) > 100:
                self.signal_history = self.signal_history[-100:]
            return final_signal
        else:
            return M15Signal(
                timestamp=datetime.now(),
                signal_type=SignalType.NEUTRAL,
                confidence=0.0,
                components={},
                metadata={"error": "Failed to generate signal"},
                dokyaku_score=0.0,
                ikikaeri_pattern="",
                momi_state=""
            )
    
    # ===== 階層40: 基本判定関数（メモファイル核心概念） =====
    
    def _dokyaku_judgment(self, feature_bundle: Dict[str, Any]) -> Dict[str, Any]:
        """同逆判定：前々足乖離による方向判断（勝率55.7%～56.1%）"""
        features = feature_bundle.get("features", {})
        
        # 同逆スコア取得
        dokyaku_key = f"{self.currency_pair}_{self.timeframe}_dokyaku_score"
        dokyaku_score = 0.0
        direction_agreement = False
        
        if dokyaku_key in features:
            feature = features[dokyaku_key]
            dokyaku_score = feature.get("value", 0.0)
            # メタデータから方向一致性も取得可能
        
        # MHIH/MJIH、MMHMH/MMJMHの方向一致性評価
        if dokyaku_score > 0.7:
            return {
                "judgment": "strong_agreement",
                "score": dokyaku_score,
                "direction": SignalType.BUY if direction_agreement else SignalType.SELL,
                "confidence": 0.557  # 勝率55.7%ベース
            }
        elif dokyaku_score > 0.3:
            return {
                "judgment": "weak_agreement",
                "score": dokyaku_score,
                "direction": SignalType.NEUTRAL,
                "confidence": 0.5
            }
        else:
            return {
                "judgment": "divergence",
                "score": dokyaku_score,
                "direction": SignalType.NEUTRAL,
                "confidence": 0.45
            }
    
    def _ikikaeri_judgment(self, feature_bundle: Dict[str, Any]) -> Dict[str, Any]:
        """行帰判定：前足の動きから今足の方向予測"""
        features = feature_bundle.get("features", {})
        
        # 平均足方向取得
        ha_direction_key = f"{self.currency_pair}_{self.timeframe}_ha_direction"
        ha_direction = 0
        
        if ha_direction_key in features:
            ha_direction = features[ha_direction_key].get("value", 0)
        
        # 行帰パターン分類
        # 行行：継続、行帰：一時的戻り、帰行：戻りから再進行、帰戻：完全転換
        if ha_direction > 0:
            pattern = "iki_iki"  # 行行（上昇継続）
            signal = SignalType.BUY
            confidence = 0.6
        elif ha_direction < 0:
            pattern = "kaeri_modori"  # 帰戻（下降転換）
            signal = SignalType.SELL
            confidence = 0.6
        else:
            pattern = "iki_kaeri"  # 行帰（一時的戻り）
            signal = SignalType.NEUTRAL
            confidence = 0.4
        
        return {
            "pattern": pattern,
            "direction": signal,
            "confidence": confidence,
            "ha_direction": ha_direction
        }
    
    def _momi_judgment(self, feature_bundle: Dict[str, Any]) -> Dict[str, Any]:
        """もみ合い判定：レンジ幅3pips未満"""
        features = feature_bundle.get("features", {})
        
        # もみスコア取得
        momi_key = f"{self.currency_pair}_{self.timeframe}_momi_score"
        momi_score = 0.0
        
        if momi_key in features:
            momi_score = features[momi_key].get("value", 0.0)
        
        # レンジ幅による判定
        if momi_score > 0.8:
            return {
                "state": "tight_range",
                "score": momi_score,
                "breakout_potential": 0.7,
                "trade_recommendation": "wait"
            }
        elif momi_score > 0.5:
            return {
                "state": "normal_range",
                "score": momi_score,
                "breakout_potential": 0.5,
                "trade_recommendation": "cautious"
            }
        else:
            return {
                "state": "trending",
                "score": momi_score,
                "breakout_potential": 0.2,
                "trade_recommendation": "active"
            }
    
    def _overshoot_detection(self, feature_bundle: Dict[str, Any]) -> Dict[str, Any]:
        """オーバーシュート検出：前足Os残足が今足換算で2以上"""
        features = feature_bundle.get("features", {})
        
        # 価格変化率から簡易的にオーバーシュート判定
        price_change_key = f"{self.currency_pair}_{self.timeframe}_price_change_pct"
        price_change_pct = 0.0
        
        if price_change_key in features:
            price_change_pct = abs(features[price_change_key].get("value", 0.0))
        
        # 2%以上の急激な変化をオーバーシュートと判定
        if price_change_pct > 0.02:
            return {
                "detected": True,
                "magnitude": price_change_pct,
                "reversal_probability": 0.7,
                "action": "counter_trend"
            }
        else:
            return {
                "detected": False,
                "magnitude": price_change_pct,
                "reversal_probability": 0.2,
                "action": "follow_trend"
            }
    
    # ===== 階層41: 複合判定関数 =====
    
    def _direction_consensus(self, dokyaku: Dict[str, Any],
                            ikikaeri: Dict[str, Any]) -> Dict[str, Any]:
        """方向性合意判定"""
        if not dokyaku or not ikikaeri:
            return {"consensus": False}
        
        dokyaku_dir = dokyaku.get("direction", SignalType.NEUTRAL)
        ikikaeri_dir = ikikaeri.get("direction", SignalType.NEUTRAL)
        
        # 方向一致性チェック
        if dokyaku_dir == ikikaeri_dir and dokyaku_dir != SignalType.NEUTRAL:
            combined_confidence = (dokyaku.get("confidence", 0) + 
                                  ikikaeri.get("confidence", 0)) / 2
            return {
                "consensus": True,
                "direction": dokyaku_dir,
                "confidence": min(combined_confidence * 1.2, 0.8),  # 合意時は信頼度上昇
                "type": "strong_consensus"
            }
        elif dokyaku.get("judgment") == "strong_agreement":
            # 同逆判定が強い場合は優先
            return {
                "consensus": True,
                "direction": dokyaku_dir,
                "confidence": dokyaku.get("confidence", 0.5),
                "type": "dokyaku_priority"
            }
        else:
            return {
                "consensus": False,
                "direction": SignalType.NEUTRAL,
                "confidence": 0.3,
                "type": "no_consensus"
            }
    
    def _market_state_analysis(self, momi: Dict[str, Any],
                              overshoot: Dict[str, Any]) -> Dict[str, Any]:
        """市場状態分析"""
        if not momi or not overshoot:
            return {"state": "unknown"}
        
        momi_state = momi.get("state", "unknown")
        overshoot_detected = overshoot.get("detected", False)
        
        if overshoot_detected:
            return {
                "state": "overshoot",
                "action": overshoot.get("action", "wait"),
                "risk_level": "high",
                "trade_size_adjustment": 0.5  # ポジションサイズ半減
            }
        elif momi_state == "tight_range":
            return {
                "state": "consolidation",
                "action": "wait_for_breakout",
                "risk_level": "low",
                "trade_size_adjustment": 0.3  # 小さめのポジション
            }
        elif momi_state == "trending":
            return {
                "state": "trending",
                "action": "follow_trend",
                "risk_level": "medium",
                "trade_size_adjustment": 1.0  # 通常ポジション
            }
        else:
            return {
                "state": "normal",
                "action": "standard",
                "risk_level": "medium",
                "trade_size_adjustment": 0.7
            }
    
    # ===== 階層42: 統合判定関数 =====
    
    def _integrated_m15_signal(self, direction: Dict[str, Any],
                              market_state: Dict[str, Any]) -> Dict[str, Any]:
        """M15統合信号（勝率55.7%目標）"""
        if not direction or not market_state:
            return {"signal": SignalType.NEUTRAL, "confidence": 0.0}
        
        consensus = direction.get("consensus", False)
        state = market_state.get("state", "unknown")
        
        # 市場状態による信号調整
        if state == "overshoot" and consensus:
            # オーバーシュート時は逆張り
            original_dir = direction.get("direction", SignalType.NEUTRAL)
            if original_dir == SignalType.BUY:
                adjusted_dir = SignalType.SELL
            elif original_dir == SignalType.SELL:
                adjusted_dir = SignalType.BUY
            else:
                adjusted_dir = SignalType.NEUTRAL
            
            return {
                "signal": adjusted_dir,
                "confidence": 0.6,
                "strategy": "counter_trend",
                "size_adjustment": market_state.get("trade_size_adjustment", 0.5)
            }
        elif state == "consolidation":
            # もみ合い時は様子見
            return {
                "signal": SignalType.NEUTRAL,
                "confidence": 0.2,
                "strategy": "wait",
                "size_adjustment": 0.0
            }
        elif consensus:
            # 通常の合意信号
            return {
                "signal": direction.get("direction", SignalType.NEUTRAL),
                "confidence": direction.get("confidence", 0.5),
                "strategy": "trend_follow",
                "size_adjustment": market_state.get("trade_size_adjustment", 0.7)
            }
        else:
            return {
                "signal": SignalType.NEUTRAL,
                "confidence": 0.0,
                "strategy": "no_trade",
                "size_adjustment": 0.0
            }
    
    # ===== 階層43: 最終判定関数 =====
    
    def _final_m15_signal(self, integrated: Dict[str, Any]) -> M15Signal:
        """最終M15信号"""
        signal_type = integrated.get("signal", SignalType.NEUTRAL)
        confidence = integrated.get("confidence", 0.0)
        
        # 勝率調整（55.7%目標）
        if confidence > 0.557:
            # 信頼度が目標勝率を超える場合のみ強い信号
            if confidence > 0.7:
                if signal_type == SignalType.BUY:
                    signal_type = SignalType.BUY_STRONG
                elif signal_type == SignalType.SELL:
                    signal_type = SignalType.SELL_STRONG
        elif confidence < 0.4:
            # 低信頼度は弱い信号に
            if signal_type == SignalType.BUY:
                signal_type = SignalType.BUY_WEAK
            elif signal_type == SignalType.SELL:
                signal_type = SignalType.SELL_WEAK
        
        # キャッシュから追加情報取得
        dokyaku_data = self.node_cache.get("391^40-001", {})
        ikikaeri_data = self.node_cache.get("391^40-002", {})
        momi_data = self.node_cache.get("391^40-003", {})
        
        return M15Signal(
            timestamp=datetime.now(),
            signal_type=signal_type,
            confidence=confidence,
            components={
                "strategy": integrated.get("strategy", "unknown"),
                "size_adjustment": integrated.get("size_adjustment", 1.0),
                "integrated": integrated
            },
            metadata={
                "timeframe": self.timeframe,
                "currency_pair": self.currency_pair,
                "target_win_rate": 0.557
            },
            dokyaku_score=dokyaku_data.get("score", 0.0),
            ikikaeri_pattern=ikikaeri_data.get("pattern", ""),
            momi_state=momi_data.get("state", "")
        )