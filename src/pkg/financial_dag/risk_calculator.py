"""
リスク計算DAG
資金管理とリスク評価を行う財務層

階層範囲: 70-74（リスク計算）
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    """リスクレベル定義"""
    MINIMAL = 1      # 最小リスク
    LOW = 2          # 低リスク
    MODERATE = 3     # 中リスク
    HIGH = 4         # 高リスク
    EXTREME = 5      # 極高リスク

@dataclass
class RiskMetrics:
    """リスク指標データ"""
    timestamp: datetime
    risk_level: RiskLevel
    var_95: float           # 95% VaR
    max_drawdown: float     # 最大ドローダウン
    sharpe_ratio: float     # シャープレシオ
    position_risk: float    # ポジションリスク
    market_risk: float      # 市場リスク
    components: Dict[str, Any]

class RiskCalculatorDAG:
    """リスク計算DAGクラス"""
    
    def __init__(self, currency_pair: str = "USDJPY"):
        self.currency_pair = currency_pair
        self.currency_code = self._get_currency_code(currency_pair)
        
        # DAGノード定義
        self.nodes = self._define_nodes()
        self.execution_order = self._determine_execution_order()
        
        # 内部状態
        self.risk_history: List[RiskMetrics] = []
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
        
        # 階層70: 基本リスク計算
        nodes["191^70-001"] = {
            "name": "position_size_risk",
            "layer": 70,
            "inputs": ["unified_signal", "account_info"],
            "function": self._calculate_position_risk,
            "description": "ポジションサイズリスク計算"
        }
        
        nodes["191^70-002"] = {
            "name": "market_volatility_risk",
            "layer": 70,
            "inputs": ["market_data"],
            "function": self._calculate_market_risk,
            "description": "市場ボラティリティリスク"
        }
        
        nodes["191^70-003"] = {
            "name": "correlation_risk",
            "layer": 70,
            "inputs": ["portfolio_data"],
            "function": self._calculate_correlation_risk,
            "description": "相関リスク計算"
        }
        
        # 階層71: VaR計算
        nodes["191^71-001"] = {
            "name": "historical_var",
            "layer": 71,
            "inputs": ["191^70-001", "191^70-002", "historical_data"],
            "function": self._calculate_historical_var,
            "description": "ヒストリカルVaR計算"
        }
        
        nodes["191^71-002"] = {
            "name": "parametric_var",
            "layer": 71,
            "inputs": ["191^70-002", "191^70-003"],
            "function": self._calculate_parametric_var,
            "description": "パラメトリックVaR計算"
        }
        
        # 階層72: ドローダウン分析
        nodes["191^72-001"] = {
            "name": "max_drawdown_analysis",
            "layer": 72,
            "inputs": ["191^71-001", "portfolio_history"],
            "function": self._analyze_max_drawdown,
            "description": "最大ドローダウン分析"
        }
        
        nodes["191^72-002"] = {
            "name": "recovery_time_analysis",
            "layer": 72,
            "inputs": ["191^71-001", "191^71-002"],  # 階層71から入力
            "function": self._analyze_recovery_time,
            "description": "回復時間分析"
        }
        
        # 階層73: リスク統合
        nodes["191^73-001"] = {
            "name": "integrated_risk_score",
            "layer": 73,
            "inputs": ["191^71-001", "191^71-002", "191^72-001"],
            "function": self._integrate_risk_scores,
            "description": "統合リスクスコア"
        }
        
        nodes["191^73-002"] = {
            "name": "risk_adjusted_metrics",
            "layer": 73,
            "inputs": ["191^72-001", "191^72-002"],  # 階層72から入力
            "function": self._calculate_risk_adjusted_metrics,
            "description": "リスク調整済み指標"
        }
        
        # 階層74: 最終リスク評価
        nodes["191^74-001"] = {
            "name": "final_risk_assessment",
            "layer": 74,
            "inputs": ["191^73-001", "191^73-002"],
            "function": self._final_risk_assessment,
            "description": "最終リスク評価"
        }
        
        return nodes
    
    def _determine_execution_order(self) -> List[str]:
        """実行順序を決定（トポロジカルソート）"""
        return [
            "191^70-001", "191^70-002", "191^70-003",  # 階層70
            "191^71-001", "191^71-002",                # 階層71
            "191^72-001", "191^72-002",                # 階層72
            "191^73-001", "191^73-002",                # 階層73
            "191^74-001"                               # 階層74
        ]
    
    def process(self, unified_signal: Any, account_info: Dict[str, Any],
                market_data: Dict[str, Any], portfolio_data: Dict[str, Any],
                historical_data: List[Dict[str, Any]],
                portfolio_history: List[Dict[str, Any]]) -> RiskMetrics:
        """リスク評価を実行"""
        # コンテキスト初期化
        context = {
            "unified_signal": unified_signal,
            "account_info": account_info,
            "market_data": market_data,
            "portfolio_data": portfolio_data,
            "historical_data": historical_data,
            "portfolio_history": portfolio_history
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
        
        # 最終リスクメトリクス取得
        final_metrics = self.node_cache.get("191^74-001")
        
        if final_metrics:
            # 履歴に追加
            self.risk_history.append(final_metrics)
            
            # 履歴サイズ制限
            if len(self.risk_history) > 100:
                self.risk_history = self.risk_history[-100:]
            
            return final_metrics
        else:
            # デフォルトメトリクス
            return RiskMetrics(
                timestamp=datetime.now(),
                risk_level=RiskLevel.MODERATE,
                var_95=0.0,
                max_drawdown=0.0,
                sharpe_ratio=0.0,
                position_risk=0.0,
                market_risk=0.0,
                components={}
            )
    
    # ===== 階層70: 基本リスク計算関数 =====
    
    def _calculate_position_risk(self, unified_signal: Any, 
                                account_info: Dict[str, Any]) -> Dict[str, Any]:
        """ポジションサイズリスクを計算"""
        if not unified_signal or not account_info:
            return {"position_risk": 0.0, "leverage": 1.0}
        
        balance = account_info.get("balance", 10000)
        margin_used = account_info.get("margin_used", 0)
        
        # レバレッジ計算
        leverage = (margin_used / balance) if balance > 0 else 0
        
        # ポジションリスク（簡易版）
        position_risk = min(leverage * 0.1, 1.0)  # 最大100%
        
        return {
            "position_risk": position_risk,
            "leverage": leverage,
            "balance": balance,
            "margin_used": margin_used
        }
    
    def _calculate_market_risk(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """市場ボラティリティリスクを計算"""
        if not market_data:
            return {"market_risk": 0.5, "volatility": 0.01}
        
        # ボラティリティ取得（簡易版）
        volatility = market_data.get("volatility", 0.01)
        spread = market_data.get("spread", 0.5)
        
        # 市場リスク計算
        market_risk = min(volatility * 10 + spread * 0.1, 1.0)
        
        return {
            "market_risk": market_risk,
            "volatility": volatility,
            "spread": spread
        }
    
    def _calculate_correlation_risk(self, portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
        """相関リスクを計算"""
        if not portfolio_data:
            return {"correlation_risk": 0.0, "concentration": 0.0}
        
        positions = portfolio_data.get("positions", [])
        
        # 集中度計算（簡易版）
        if positions:
            total_value = sum(p.get("value", 0) for p in positions)
            max_position = max(p.get("value", 0) for p in positions)
            concentration = (max_position / total_value) if total_value > 0 else 0
        else:
            concentration = 0.0
        
        correlation_risk = concentration * 0.5
        
        return {
            "correlation_risk": correlation_risk,
            "concentration": concentration,
            "position_count": len(positions)
        }
    
    # ===== 階層71: VaR計算関数 =====
    
    def _calculate_historical_var(self, position_risk: Dict[str, Any],
                                 market_risk: Dict[str, Any],
                                 historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """ヒストリカルVaRを計算"""
        if not historical_data:
            return {"var_95": 0.02, "confidence": 0.95}
        
        # リターン計算（簡易版）
        returns = []
        for i in range(1, len(historical_data)):
            if historical_data[i].get("close") and historical_data[i-1].get("close"):
                ret = (historical_data[i]["close"] - historical_data[i-1]["close"]) / historical_data[i-1]["close"]
                returns.append(ret)
        
        if returns:
            # 95% VaR計算（簡易版）
            sorted_returns = sorted(returns)
            var_index = int(len(sorted_returns) * 0.05)
            var_95 = abs(sorted_returns[var_index]) if var_index < len(sorted_returns) else 0.02
        else:
            var_95 = 0.02
        
        # リスク調整
        adjusted_var = var_95 * (1 + position_risk.get("position_risk", 0))
        
        return {
            "var_95": adjusted_var,
            "confidence": 0.95,
            "sample_size": len(returns)
        }
    
    def _calculate_parametric_var(self, market_risk: Dict[str, Any],
                                 correlation_risk: Dict[str, Any]) -> Dict[str, Any]:
        """パラメトリックVaRを計算"""
        volatility = market_risk.get("volatility", 0.01)
        correlation = correlation_risk.get("correlation_risk", 0.0)
        
        # パラメトリックVaR（簡易版）
        # 1.645 = 95%信頼水準のz値
        var_95 = 1.645 * volatility * (1 + correlation)
        
        return {
            "parametric_var_95": var_95,
            "volatility_input": volatility,
            "correlation_adjustment": correlation
        }
    
    # ===== 階層72: ドローダウン分析関数 =====
    
    def _analyze_max_drawdown(self, historical_var: Dict[str, Any],
                             portfolio_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """最大ドローダウンを分析"""
        if not portfolio_history:
            return {"max_drawdown": 0.0, "drawdown_periods": []}
        
        # 最大ドローダウン計算（簡易版）
        values = [p.get("value", 0) for p in portfolio_history]
        
        if values:
            peak = values[0]
            max_dd = 0
            current_dd = 0
            
            for value in values:
                if value > peak:
                    peak = value
                    current_dd = 0
                else:
                    current_dd = (peak - value) / peak if peak > 0 else 0
                    max_dd = max(max_dd, current_dd)
        else:
            max_dd = 0.0
        
        return {
            "max_drawdown": max_dd,
            "var_adjusted_dd": max_dd * (1 + historical_var.get("var_95", 0)),
            "periods_analyzed": len(values)
        }
    
    def _analyze_recovery_time(self, historical_var: Dict[str, Any],
                              parametric_var: Dict[str, Any]) -> Dict[str, Any]:
        """回復時間を分析"""
        # VaRから推定されるリスク
        h_var = historical_var.get("var_95", 0.02)
        p_var = parametric_var.get("parametric_var_95", 0.02)
        avg_var = (h_var + p_var) / 2
        
        # VaRベースで推定される最大ドローダウン（簡易推定）
        max_dd = avg_var * 5  # VaRの5倍を仮定
        
        # 回復時間推定（簡易版）
        if max_dd > 0:
            # ドローダウンが大きいほど回復時間が長い
            estimated_days = int(max_dd * 100)  # 簡易推定
        else:
            estimated_days = 0
        
        return {
            "estimated_recovery_days": estimated_days,
            "recovery_confidence": 0.7,
            "based_on_drawdown": max_dd
        }
    
    # ===== 階層73: リスク統合関数 =====
    
    def _integrate_risk_scores(self, historical_var: Dict[str, Any],
                              parametric_var: Dict[str, Any],
                              drawdown: Dict[str, Any]) -> Dict[str, Any]:
        """リスクスコアを統合"""
        # 各リスク指標を取得
        h_var = historical_var.get("var_95", 0.02)
        p_var = parametric_var.get("parametric_var_95", 0.02)
        max_dd = drawdown.get("max_drawdown", 0.0)
        
        # 統合スコア計算（加重平均）
        integrated_score = (h_var * 0.4 + p_var * 0.3 + max_dd * 0.3)
        
        # リスクレベル判定
        if integrated_score < 0.02:
            risk_level = RiskLevel.MINIMAL
        elif integrated_score < 0.05:
            risk_level = RiskLevel.LOW
        elif integrated_score < 0.10:
            risk_level = RiskLevel.MODERATE
        elif integrated_score < 0.20:
            risk_level = RiskLevel.HIGH
        else:
            risk_level = RiskLevel.EXTREME
        
        return {
            "integrated_score": integrated_score,
            "risk_level": risk_level,
            "components": {
                "historical_var": h_var,
                "parametric_var": p_var,
                "max_drawdown": max_dd
            }
        }
    
    def _calculate_risk_adjusted_metrics(self, drawdown_analysis: Dict[str, Any],
                                        recovery_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """リスク調整済み指標を計算"""
        max_dd = drawdown_analysis.get("max_drawdown", 0.05)
        recovery_days = recovery_analysis.get("estimated_recovery_days", 0)
        
        # リスクスコア推定（簡易版）
        risk_score = max_dd
        
        # シャープレシオ計算（簡易版）
        # 仮定: リターン = 0.1 (10%)
        expected_return = 0.1
        sharpe_ratio = (expected_return / risk_score) if risk_score > 0 else 0
        
        # カルマーレシオ計算（簡易版）
        calmar_ratio = (expected_return / max_dd) if max_dd > 0 else 0
        
        return {
            "sharpe_ratio": sharpe_ratio,
            "calmar_ratio": calmar_ratio,
            "recovery_days": recovery_days,
            "risk_efficiency": sharpe_ratio / (1 + recovery_days/365)
        }
    
    # ===== 階層74: 最終リスク評価関数 =====
    
    def _final_risk_assessment(self, integrated_risk: Dict[str, Any],
                              risk_adjusted: Dict[str, Any]) -> RiskMetrics:
        """最終リスク評価を生成"""
        return RiskMetrics(
            timestamp=datetime.now(),
            risk_level=integrated_risk.get("risk_level", RiskLevel.MODERATE),
            var_95=integrated_risk.get("components", {}).get("historical_var", 0.02),
            max_drawdown=integrated_risk.get("components", {}).get("max_drawdown", 0.0),
            sharpe_ratio=risk_adjusted.get("sharpe_ratio", 0.0),
            position_risk=integrated_risk.get("integrated_score", 0.05),
            market_risk=integrated_risk.get("integrated_score", 0.05),
            components={
                "integrated_risk": integrated_risk,
                "risk_adjusted_metrics": risk_adjusted
            }
        )
    
    def get_risk_history(self, limit: int = 10) -> List[RiskMetrics]:
        """リスク履歴を取得"""
        return self.risk_history[-limit:] if self.risk_history else []