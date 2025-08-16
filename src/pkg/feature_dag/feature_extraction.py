"""
特徴量抽出層 (Feature Extraction Layer)
階層1-5: PKG準拠の特徴量計算とマルチタイムフレーム統合
"""

import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import math
import statistics

from .dag_config_manager import DAGConfigManager, NodeDefinition

logger = logging.getLogger(__name__)

@dataclass
class MarketData:
    """市場データ構造"""
    timestamp: datetime
    symbol: str
    bid: float
    ask: float
    volume: float
    spread: float

@dataclass
class HeikinAshiData:
    """平均足データ構造"""
    open: float
    high: float
    low: float
    close: float
    direction: int  # 1: 上昇, -1: 下降, 0: 横ばい

class FeatureExtractionLayer:
    """特徴量抽出層メインクラス"""
    
    def __init__(self, currency: str = "USDJPY"):
        self.currency = currency
        self.currency_code = self._get_currency_code(currency)
        self.config_manager = DAGConfigManager()
        self.config_manager.load_configuration()
        
        # データキャッシュ
        self.price_history: List[MarketData] = []
        self.heikin_ashi_history: List[HeikinAshiData] = []
        self.feature_cache: Dict[str, Any] = {}
        
        # パフォーマンス監視
        self.execution_times: Dict[str, List[float]] = {}
        
    def _get_currency_code(self, currency: str) -> str:
        """通貨コードを取得"""
        mapping = {
            "USDJPY": "1",
            "EURUSD": "2", 
            "EURJPY": "3"
        }
        return mapping.get(currency, "1")
    
    def process_market_data(self, market_data: MarketData) -> Dict[str, Any]:
        """市場データを処理してすべての特徴量を計算"""
        start_time = time.time()
        
        # データ履歴を更新
        self._update_data_history(market_data)
        
        # 実行順序に従って各ノードを処理
        execution_order = self.config_manager.get_execution_order()
        results = {}
        
        for node_id in execution_order:
            try:
                node_result = self._execute_node(node_id, results)
                results.update(node_result)
                
            except Exception as e:
                logger.error(f"Error executing node {node_id}: {e}")
                # エラー時はデフォルト値を設定
                results[node_id] = self._get_default_node_output(node_id)
        
        # 実行時間を記録
        execution_time = (time.time() - start_time) * 1000
        self._record_execution_time("process_market_data", execution_time)
        
        # 30ms制約のチェック
        if execution_time > 30:
            logger.warning(f"Execution time exceeded 30ms: {execution_time:.2f}ms")
        
        return results
    
    def _update_data_history(self, market_data: MarketData) -> None:
        """データ履歴を更新"""
        self.price_history.append(market_data)
        
        # 履歴サイズ制限（最新100件）
        if len(self.price_history) > 100:
            self.price_history = self.price_history[-100:]
    
    def _execute_node(self, node_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """個別ノードを実行"""
        node_def = self.config_manager.get_node_definition(node_id)
        
        # 入力データを準備
        input_data = self._prepare_input_data(node_def, context)
        
        # 対応する関数を実行
        function_name = node_def.function
        if hasattr(self, function_name):
            function = getattr(self, function_name)
            result = function(input_data, node_def.parameters)
        else:
            raise NotImplementedError(f"Function {function_name} not implemented")
        
        return {node_id: result}
    
    def _prepare_input_data(self, node_def: NodeDefinition, context: Dict[str, Any]) -> Dict[str, Any]:
        """ノード実行用の入力データを準備"""
        input_data = {}
        
        for input_id in node_def.inputs:
            if input_id in context:
                input_data[input_id] = context[input_id]
            else:
                logger.warning(f"Missing input {input_id} for node {node_def.id}")
        
        return input_data
    
    # 階層1: 基本指標計算関数群
    
    def calculate_heikin_ashi(self, input_data: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, float]:
        """平均足計算"""
        if not self.price_history:
            return self._get_default_heikin_ashi()
        
        current_data = self.price_history[-1]
        smoothing = parameters.get('smoothing_factor', 0.1)
        
        # 前回の平均足データを取得
        prev_ha = self.heikin_ashi_history[-1] if self.heikin_ashi_history else None
        
        if prev_ha is None:
            # 初回計算
            ha_close = (current_data.bid + current_data.ask) / 2
            ha_open = ha_close
            ha_high = max(current_data.bid, current_data.ask)
            ha_low = min(current_data.bid, current_data.ask)
        else:
            # 平均足計算
            ha_close = (current_data.bid + current_data.ask) / 2
            ha_open = (prev_ha.open + prev_ha.close) / 2
            ha_high = max(current_data.bid, current_data.ask, ha_open)
            ha_low = min(current_data.bid, current_data.ask, ha_open)
        
        # 方向判定
        direction = 1 if ha_close > ha_open else (-1 if ha_close < ha_open else 0)
        
        # 履歴に追加
        ha_data = HeikinAshiData(ha_open, ha_high, ha_low, ha_close, direction)
        self.heikin_ashi_history.append(ha_data)
        
        # 履歴サイズ制限
        if len(self.heikin_ashi_history) > 100:
            self.heikin_ashi_history = self.heikin_ashi_history[-100:]
        
        return {
            "ha_open": ha_open,
            "ha_high": ha_high,
            "ha_low": ha_low,
            "ha_close": ha_close,
            "ha_direction": direction
        }
    
    def calculate_price_changes(self, input_data: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, float]:
        """価格変化計算"""
        if len(self.price_history) < 2:
            return {"price_change": 0.0, "price_change_pct": 0.0, "price_momentum": 0.0}
        
        current = self.price_history[-1]
        previous = self.price_history[-2]
        current_price = (current.bid + current.ask) / 2
        previous_price = (previous.bid + previous.ask) / 2
        
        price_change = current_price - previous_price
        price_change_pct = price_change / previous_price if previous_price != 0 else 0.0
        
        # モメンタム計算（複数期間の変化率平均）
        periods = parameters.get('periods', [1, 5, 15])
        momentum_values = []
        
        for period in periods:
            if len(self.price_history) > period:
                past_data = self.price_history[-(period+1)]
                past_price = (past_data.bid + past_data.ask) / 2
                momentum = (current_price - past_price) / past_price if past_price != 0 else 0.0
                momentum_values.append(momentum)
        
        price_momentum = statistics.mean(momentum_values) if momentum_values else 0.0
        
        return {
            "price_change": price_change,
            "price_change_pct": price_change_pct,
            "price_momentum": price_momentum
        }
    
    def calculate_range_metrics(self, input_data: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, float]:
        """レンジ指標計算"""
        periods = parameters.get('range_periods', 20)
        
        if len(self.price_history) < periods:
            return {"range_width": 0.0, "range_position": 0.5, "volatility_index": 0.0}
        
        recent_data = self.price_history[-periods:]
        prices = [(d.bid + d.ask) / 2 for d in recent_data]
        
        range_high = max(prices)
        range_low = min(prices)
        range_width = range_high - range_low
        
        current_price = prices[-1]
        range_position = (current_price - range_low) / range_width if range_width > 0 else 0.5
        
        # ボラティリティ指標（標準偏差）
        volatility_index = statistics.stdev(prices) if len(prices) > 1 else 0.0
        
        return {
            "range_width": range_width,
            "range_position": range_position,
            "volatility_index": volatility_index
        }
    
    # 階層2: 複合指標計算関数群
    
    def calculate_deviation_metrics(self, input_data: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, float]:
        """乖離指標計算"""
        threshold = parameters.get('deviation_threshold', 0.02)
        lookback = parameters.get('lookback_periods', 50)
        
        if len(self.heikin_ashi_history) < 3:
            return {"deviation_score": 0.0, "deviation_direction": 0, "confidence_level": 0.0}
        
        # 前々足乖離による方向判断（同逆判定の核心概念）
        current_ha = self.heikin_ashi_history[-1]
        prev_ha = self.heikin_ashi_history[-2]
        prev_prev_ha = self.heikin_ashi_history[-3] if len(self.heikin_ashi_history) >= 3 else prev_ha
        
        # 乖離計算
        deviation_1 = abs(current_ha.close - prev_ha.close) / prev_ha.close if prev_ha.close != 0 else 0
        deviation_2 = abs(prev_ha.close - prev_prev_ha.close) / prev_prev_ha.close if prev_prev_ha.close != 0 else 0
        
        deviation_score = (deviation_1 + deviation_2) / 2
        
        # 方向一致性判定
        current_direction = current_ha.direction
        prev_direction = prev_ha.direction
        direction_agreement = 1 if current_direction == prev_direction else -1
        
        # 信頼度計算
        confidence_level = min(1.0, deviation_score / threshold) if threshold > 0 else 0.0
        
        return {
            "deviation_score": deviation_score,
            "deviation_direction": direction_agreement,
            "confidence_level": confidence_level
        }
    
    def calculate_momentum_indicators(self, input_data: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, float]:
        """モメンタム指標計算"""
        ma_periods = parameters.get('ma_periods', [5, 10, 20])
        
        if len(self.price_history) < max(ma_periods):
            return {"momentum_strength": 0.0, "momentum_acceleration": 0.0, "trend_stability": 0.0}
        
        prices = [(d.bid + d.ask) / 2 for d in self.price_history]
        
        # 移動平均計算
        mas = []
        for period in ma_periods:
            if len(prices) >= period:
                ma = statistics.mean(prices[-period:])
                mas.append(ma)
        
        if len(mas) < 2:
            return {"momentum_strength": 0.0, "momentum_acceleration": 0.0, "trend_stability": 0.0}
        
        # モメンタム強度（短期MAと長期MAの乖離）
        momentum_strength = (mas[0] - mas[-1]) / mas[-1] if mas[-1] != 0 else 0.0
        
        # モメンタム加速度（前回との比較）
        if len(self.feature_cache.get('momentum_history', [])) > 0:
            prev_momentum = self.feature_cache['momentum_history'][-1]
            momentum_acceleration = momentum_strength - prev_momentum
        else:
            momentum_acceleration = 0.0
        
        # トレンド安定性（移動平均の方向性一致度）
        trend_directions = []
        for i in range(len(mas) - 1):
            direction = 1 if mas[i] > mas[i+1] else -1
            trend_directions.append(direction)
        
        trend_stability = abs(statistics.mean(trend_directions)) if trend_directions else 0.0
        
        # 履歴更新
        if 'momentum_history' not in self.feature_cache:
            self.feature_cache['momentum_history'] = []
        self.feature_cache['momentum_history'].append(momentum_strength)
        if len(self.feature_cache['momentum_history']) > 50:
            self.feature_cache['momentum_history'] = self.feature_cache['momentum_history'][-50:]
        
        return {
            "momentum_strength": momentum_strength,
            "momentum_acceleration": momentum_acceleration,
            "trend_stability": trend_stability
        }
    
    # 階層3: パターン認識関数群
    
    def detect_momi_pattern(self, input_data: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, float]:
        """もみ合いパターン検出"""
        min_range = parameters.get('min_range_width', 3)
        max_range = parameters.get('max_range_width', 10)
        
        if len(self.price_history) < 10:
            return {"momi_score": 0.0, "momi_direction": 0, "pattern_confidence": 0.0}
        
        # 最近10期間の価格レンジを計算
        recent_prices = [(d.bid + d.ask) / 2 for d in self.price_history[-10:]]
        price_range = max(recent_prices) - min(recent_prices)
        
        # pipsに変換（USDJPY基準、0.01が1pip）
        price_range_pips = price_range * 100
        
        # もみ合い判定
        if min_range <= price_range_pips <= max_range:
            momi_score = 1.0 - abs(price_range_pips - (min_range + max_range) / 2) / (max_range - min_range)
        else:
            momi_score = 0.0
        
        # 方向判定（レンジ内での位置）
        current_price = recent_prices[-1]
        range_position = (current_price - min(recent_prices)) / (max(recent_prices) - min(recent_prices))
        momi_direction = 1 if range_position > 0.6 else (-1 if range_position < 0.4 else 0)
        
        # パターン信頼度
        pattern_confidence = momi_score * (1.0 - abs(range_position - 0.5) * 2)
        
        return {
            "momi_score": momi_score,
            "momi_direction": momi_direction,
            "pattern_confidence": pattern_confidence
        }
    
    def detect_dokyaku_pattern(self, input_data: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, float]:
        """同逆パターン検出"""
        agreement_threshold = parameters.get('agreement_threshold', 0.7)
        
        if len(self.heikin_ashi_history) < 3:
            return {"dokyaku_score": 0.0, "direction_agreement": False, "reliability_score": 0.0}
        
        # 最近3本の平均足方向を分析
        recent_ha = self.heikin_ashi_history[-3:]
        directions = [ha.direction for ha in recent_ha]
        
        # 方向一致性計算
        if len(set(directions)) == 1:
            # 全て同方向
            dokyaku_score = 1.0
            direction_agreement = True
        elif directions[-1] == directions[-2]:
            # 最近2本が同方向
            dokyaku_score = 0.7
            direction_agreement = True
        else:
            # 方向不一致
            dokyaku_score = 0.3
            direction_agreement = False
        
        # 信頼度計算（ボリュームと価格変化を考慮）
        if len(self.price_history) >= 3:
            volume_trend = []
            for i in range(3):
                volume_trend.append(self.price_history[-(i+1)].volume)
            
            volume_mean = statistics.mean(volume_trend) if volume_trend else 0.0
            volume_consistency = 1.0 - statistics.stdev(volume_trend) / volume_mean if volume_mean > 0 and len(volume_trend) > 1 else 0.0
            reliability_score = dokyaku_score * volume_consistency
        else:
            reliability_score = dokyaku_score
        
        return {
            "dokyaku_score": dokyaku_score,
            "direction_agreement": direction_agreement,
            "reliability_score": reliability_score
        }
    
    # 階層4: マルチタイムフレーム統合
    
    def integrate_timeframe_signals(self, input_data: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, float]:
        """マルチタイムフレーム信号統合"""
        timeframes = parameters.get('timeframes', ["M1", "M5", "M15"])
        weights = parameters.get('weight_factors', [0.3, 0.4, 0.3])
        
        # 現在は単一時間足のデータのみ使用（将来的にマルチタイムフレーム対応）
        unified_signal = 0.0
        signal_strength = 0.0
        timeframe_alignment = 0.0
        
        # 入力データから信号を統合
        signals = []
        for node_id, data in input_data.items():
            if isinstance(data, dict):
                # パターン信号の統合
                if 'momi_score' in data:
                    signals.append(data['momi_score'] * data.get('pattern_confidence', 1.0))
                if 'dokyaku_score' in data:
                    signals.append(data['dokyaku_score'] * data.get('reliability_score', 1.0))
        
        if signals:
            unified_signal = statistics.mean(signals)
            signal_strength = max(signals)
            signals_mean = statistics.mean(signals)
            timeframe_alignment = 1.0 - statistics.stdev(signals) / signals_mean if signals_mean > 0 and len(signals) > 1 else 0.0
        
        return {
            "unified_signal": unified_signal,
            "signal_strength": signal_strength,
            "timeframe_alignment": timeframe_alignment
        }
    
    # 階層5: エクスポート層
    
    def export_feature_summary(self, input_data: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """特徴量サマリーのエクスポート"""
        export_format = parameters.get('export_format', 'standardized')
        include_metadata = parameters.get('include_metadata', True)
        quality_threshold = parameters.get('quality_threshold', 0.8)
        
        # 特徴量ベクトルの構築
        feature_vector = []
        metadata = {}
        quality_metrics = {}
        
        for node_id, data in input_data.items():
            if isinstance(data, dict):
                # 数値データを特徴量ベクトルに追加
                for key, value in data.items():
                    if isinstance(value, (int, float)):
                        feature_vector.append(float(value))
                        
                        # メタデータ記録
                        if include_metadata:
                            metadata[f"{node_id}_{key}"] = {
                                "source_node": node_id,
                                "feature_name": key,
                                "timestamp": datetime.now().isoformat()
                            }
        
        # 品質メトリクス計算
        if feature_vector:
            quality_metrics = {
                "feature_count": len(feature_vector),
                "non_zero_ratio": sum(1 for v in feature_vector if v != 0) / len(feature_vector),
                "value_range": {
                    "min": min(feature_vector),
                    "max": max(feature_vector),
                    "mean": statistics.mean(feature_vector),
                    "std": statistics.stdev(feature_vector) if len(feature_vector) > 1 else 0.0
                },
                "quality_score": min(1.0, sum(1 for v in feature_vector if abs(v) > 0.001) / len(feature_vector))
            }
        
        return {
            "feature_vector": feature_vector,
            "metadata": metadata if include_metadata else {},
            "quality_metrics": quality_metrics
        }
    
    # ユーティリティ関数群
    
    def _get_default_node_output(self, node_id: str) -> Dict[str, Any]:
        """ノードのデフォルト出力を取得"""
        try:
            node_def = self.config_manager.get_node_definition(node_id)
            default_output = {}
            
            for key, value_type in node_def.outputs.items():
                if value_type == "float":
                    default_output[key] = 0.0
                elif value_type == "int":
                    default_output[key] = 0
                elif value_type == "bool":
                    default_output[key] = False
                elif value_type == "array":
                    default_output[key] = []
                elif value_type == "object":
                    default_output[key] = {}
                else:
                    default_output[key] = None
            
            return default_output
        except Exception:
            return {}
    
    def _get_default_heikin_ashi(self) -> Dict[str, float]:
        """デフォルト平均足データ"""
        return {
            "ha_open": 0.0,
            "ha_high": 0.0,
            "ha_low": 0.0,
            "ha_close": 0.0,
            "ha_direction": 0
        }
    
    def _record_execution_time(self, function_name: str, execution_time: float) -> None:
        """実行時間を記録"""
        if function_name not in self.execution_times:
            self.execution_times[function_name] = []
        
        self.execution_times[function_name].append(execution_time)
        
        # 最新50件のみ保持
        if len(self.execution_times[function_name]) > 50:
            self.execution_times[function_name] = self.execution_times[function_name][-50:]
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """パフォーマンスメトリクスを取得"""
        metrics = {}
        
        for function_name, times in self.execution_times.items():
            if times:
                metrics[function_name] = {
                    "avg_time_ms": statistics.mean(times),
                    "max_time_ms": max(times),
                    "min_time_ms": min(times),
                    "call_count": len(times)
                }
        
        return metrics