# FX取引システム マルチタイムフレームAI統合アーキテクチャ設計書

## 📋 概要

既存のPKGシステムによる確定的な取引ロジックを基盤としつつ、複数時間足（5分、15分、1時間）のシグナルとポートフォリオ状況を考慮したAI統合型の取引システムです。

## 🎯 設計方針

### 基本原則
1. **15分足を基準**としつつ、5分足と1時間足のシグナルも考慮
2. **PKGシステムの確定的計算**は各時間足で独立して実行
3. **AIは複数シグナルの統合判断**とポートフォリオ考慮に特化
4. **既存ロジックの移植性**を最大限考慮したシンプルな構成

## 📐 システムアーキテクチャ

```
┌─────────────────────────────────────────────────────┐
│        統合判断AIエージェント層                      │
│  ┌────────────────────────────────────────────┐    │
│  │ マルチタイムフレーム統合エンジン           │    │
│  │ - 15分足（基準）の重み付け評価             │    │
│  │ - 5分足シグナル（短期勢い確認）            │    │
│  │ - 1時間足シグナル（トレンド確認）          │    │
│  │ - ポートフォリオリスク評価                 │    │
│  └────────────────────────────────────────────┘    │
└──────────────────┬──────────────────────────────────┘
                   │AI判断
┌──────────────────┴──────────────────────────────────┐
│         シグナル生成層（確定的計算）                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│  │ 5分足        │ │ 15分足      │ │ 1時間足     │ │
│  │ PKG判定      │ │ PKG判定      │ │ PKG判定     │ │
│  │ (191^ID形式) │ │ (191^ID形式) │ │ (191^ID形式)│ │
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘ │
│         │                │                │         │
│  ┌──────┴────────────────┴────────────────┴──────┐ │
│  │      指標計算エンジン（Python + NumPy）        │ │
│  │      - TSML周期別OsMA計算                      │ │
│  │      - 平均足・レンジ・同逆判定                │ │
│  └───────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
                   │
┌─────────────────────────────────────────────────────┐
│              データ基盤層                            │
│  ┌──────────────┐  ┌──────────────────────┐      │
│  │ TimescaleDB   │  │ Redis               │      │
│  │ (時系列DB)    │  │ (リアルタイムキャッシュ) │      │
│  └──────────────┘  └──────────────────────┘      │
│  ┌─────────────────────────────────────────────┐   │
│  │    イベントストア（シンプルファイルベース）   │   │
│  │    - JSONL形式での取引履歴保存               │   │
│  │    - 完全な再現性とバックテスト対応          │   │
│  └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

## 🔧 コンポーネント詳細

### 1. 確定的シグナル生成層（Python）
```python
class SignalGenerator:
    """各時間足での確定的なシグナル生成"""
    
    def __init__(self, timeframe: str):
        self.timeframe = timeframe
        self.pkg_engine = PKGEngine()  # 191^ID形式の条件管理
        self.indicator_calc = IndicatorCalculator()
        
    def generate_signal(self, market_data: dict) -> Signal:
        # 1. 高速指標計算（NumPy使用）
        indicators = self.indicator_calc.calculate_all(
            market_data,
            self.get_tsml_periods()  # 時間足別TSML周期
        )
        
        # 2. PKG条件評価（完全に確定的）
        pkg_result = self.pkg_engine.evaluate(
            timeframe=self.timeframe,
            indicators=indicators,
            range_data=market_data['range'],
            dougyaku=market_data['dougyaku']  # 同逆判定
        )
        
        # 3. シグナル生成
        return Signal(
            timeframe=self.timeframe,
            action=pkg_result.action,
            strength=pkg_result.confidence,
            conditions_met=pkg_result.matched_conditions,
            timestamp=market_data['timestamp']
        )
    
    def get_tsml_periods(self) -> dict:
        """時間足別のTSML周期設定"""
        return {
            '5M': {'T': 10, 'S': 15, 'M': 30, 'L': 45},
            '15M': {'T': 10, 'S': 15, 'M': 30, 'L': 45},
            '1H': {'T': 60, 'S': 90, 'M': 180, 'L': 360}
        }
```

### 2. マルチタイムフレーム統合AI
```python
class MultiTimeframeAITrader:
    """複数時間足シグナルの統合判断"""
    
    def __init__(self):
        self.signal_generators = {
            '5M': SignalGenerator('5M'),
            '15M': SignalGenerator('15M'),  # 基準時間足
            '1H': SignalGenerator('1H')
        }
        self.portfolio_manager = PortfolioManager()
        self.ai_engine = TradingDecisionAI()
        self.event_store = EventStore()
        
    async def process_market_update(self, tick_data: dict) -> TradingDecision:
        # 1. 各時間足でのシグナル生成（並列処理）
        signals = await self._generate_all_signals(tick_data)
        
        # 2. ポートフォリオ状況の取得
        portfolio_state = self.portfolio_manager.get_current_state()
        
        # 3. AIによる統合判断
        ai_context = self._build_ai_context(signals, portfolio_state)
        decision = await self.ai_engine.make_decision(ai_context)
        
        # 4. イベントストアへの記録
        await self.event_store.record({
            'timestamp': tick_data['timestamp'],
            'signals': signals,
            'portfolio': portfolio_state,
            'decision': decision
        })
        
        return decision
    
    async def _generate_all_signals(self, tick_data: dict) -> dict:
        """並列シグナル生成"""
        tasks = []
        for tf, generator in self.signal_generators.items():
            if self._is_candle_closed(tick_data, tf):
                task = asyncio.create_task(
                    generator.generate_signal(tick_data[tf])
                )
                tasks.append((tf, task))
        
        results = {}
        for tf, task in tasks:
            results[tf] = await task
        
        return results
    
    def _build_ai_context(self, signals: dict, portfolio: dict) -> dict:
        """AI判断用のコンテキスト構築"""
        return {
            'base_timeframe': '15M',
            'signals': {
                '5M': signals.get('5M', None),      # 短期勢い
                '15M': signals.get('15M', None),    # 基準判断
                '1H': signals.get('1H', None)       # トレンド
            },
            'portfolio': {
                'positions': portfolio['positions'],
                'margin_usage': portfolio['margin_usage'],
                'unrealized_pnl': portfolio['unrealized_pnl'],
                'correlation_risk': portfolio['correlation_risk']
            },
            'timeframe_weights': {
                '5M': 0.2,   # 補助的
                '15M': 0.5,  # メイン
                '1H': 0.3    # トレンド確認
            }
        }
```

### 3. 高度な財務戦略AI（5大トレーダーの手法統合）
```python
class AdvancedFinancialStrategyAI:
    """5大トレーダーの財務管理手法を統合したAI"""
    
    def __init__(self):
        # 各トレーダーの戦略モジュール
        self.lipschutz_strategy = LipschutzCorrelationVAR()
        self.ptj_strategy = PTJSystematicRisk()
        self.kovner_strategy = KovnerStopBasedSizing()
        self.soros_strategy = SorosReflexivity()
        self.druckenmiller_strategy = DruckenmillerLiquidity()
        
        # 統合AI判断エンジン
        self.ai_engine = FinancialAI()
        
        # リアルタイムメトリクス
        self.metrics = {
            'correlation_matrix': None,
            'var_by_cluster': None,
            'liquidity_cycle': None,
            'drawdown_status': None,
            'consecutive_losses': 0
        }

class LipschutzCorrelationVAR:
    """Bill Lipschutz: 相関ベースのVAR管理"""
    
    def calculate_position_size(self, signal, portfolio, market_data):
        # 1. 関連通貨群の相関マトリクス計算
        correlation_matrix = self._calculate_correlation_matrix(
            portfolio.get_symbols()
        )
        
        # 2. 相関クラスタリング
        clusters = self._hierarchical_clustering(correlation_matrix)
        
        # 3. クラスター単位でのVAR計算
        cluster_var = {}
        for cluster_id, symbols in clusters.items():
            cluster_var[cluster_id] = self._calculate_cluster_var(
                symbols, 
                portfolio,
                confidence_level=0.99
            )
        
        # 4. 新規ポジションが属するクラスターのVAR制限
        target_cluster = self._find_cluster(signal.symbol, clusters)
        max_var = portfolio.nav * 0.03  # 最大3%
        
        current_var = cluster_var.get(target_cluster, 0)
        available_risk = max(0, max_var - current_var)
        
        # 5. 流動性考慮（G7イベント前は50%カット）
        if self._is_low_liquidity_period():
            available_risk *= 0.5
            
        return self._var_to_position_size(available_risk, signal)
    
    def _is_low_liquidity_period(self):
        """流動性蒸発イベントの検出"""
        upcoming_events = self.get_economic_calendar()
        high_impact_events = ['NFP', 'FOMC', 'ECB', 'G7']
        
        for event in upcoming_events:
            if event.impact == 'HIGH' and event.name in high_impact_events:
                hours_until = (event.datetime - datetime.now()).hours
                if hours_until < 6:  # 6時間前から縮小
                    return True
        return False

class PTJSystematicRisk:
    """Paul Tudor Jones: 1%ルール + 5:1 + 200MA"""
    
    def calculate_position_size(self, signal, portfolio, market_data):
        # 1. 基本1%ルール
        risk_per_trade = portfolio.nav * 0.01
        
        # 2. 連敗時の自動縮小
        if self.consecutive_losses > 3:
            reduction_factor = 1 / math.sqrt(self.consecutive_losses)
            risk_per_trade *= reduction_factor
        
        # 3. 200日MAからの距離でリスク調整
        ma200 = market_data.get_ma(200)
        distance_from_ma = abs(market_data.price - ma200) / ma200
        
        if distance_from_ma > 0.05:  # 5%以上乖離
            risk_per_trade *= 0.5  # リスク半減
        
        # 4. リスクリワード5:1の確認
        if signal.expected_rr < 5:
            return 0  # 取引しない
            
        # 5. ストップ幅からロット計算
        position_size = risk_per_trade / signal.stop_distance
        
        return position_size

class KovnerStopBasedSizing:
    """Bruce Kovner: Stop先行 + 相関重複回避"""
    
    def calculate_position_size(self, signal, portfolio, market_data):
        # 1. テクニカル障壁からストップ決定
        technical_stop = self._find_technical_barrier(
            market_data,
            signal.direction
        )
        
        stop_distance = abs(market_data.price - technical_stop)
        
        # 2. 基本サイズ計算（1-2%リスク）
        risk_percentage = 0.015  # 1.5%
        base_size = (portfolio.nav * risk_percentage) / stop_distance
        
        # 3. "半分ルール"（初心者は5倍大きすぎる）
        conservative_size = base_size * 0.5
        
        # 4. 相関重複チェック
        effective_positions = self._calculate_effective_positions(
            portfolio,
            signal.symbol
        )
        
        if effective_positions > 3:
            # 実効ポジション数が多い場合は更に縮小
            conservative_size *= (3 / effective_positions)
            
        return conservative_size

class SorosReflexivity:
    """George Soros: リフレクシビティ + 非対称性最大化"""
    
    def calculate_position_size(self, signal, portfolio, market_data):
        # 1. リフレクシビティスコア計算
        reflexivity_score = self._calculate_reflexivity(market_data)
        
        # 2. 転換点の可能性評価
        if reflexivity_score > 0.8:  # 自己強化ループの臨界点
            # 確信度に応じた巨大ポジション
            if signal.conviction > 0.9:
                return portfolio.nav * 0.5  # 資本の50%投入
            else:
                return portfolio.nav * 0.2
        
        # 3. 通常時は小さく、含み益は急速増し玉
        if self._has_profitable_position(signal.symbol):
            # 含み益がある場合は非対称性を拡大
            current_profit = self._get_unrealized_profit(signal.symbol)
            add_size = current_profit * 2  # 利益の2倍を追加
            
            return min(add_size, portfolio.nav * 0.3)
        
        # 4. 新規エントリーは控えめに
        return portfolio.nav * 0.02

class DruckenmillerLiquidity:
    """Stanley Druckenmiller: 流動性サイクル + 集中投資"""
    
    def __init__(self):
        self.annual_bets_used = 0  # 年間集中投資回数
        self.max_annual_bets = 2
        
    def calculate_position_size(self, signal, portfolio, market_data):
        # 1. 中央銀行流動性サイクル分析
        liquidity_score = self._analyze_cb_liquidity()
        
        # 2. 流動性拡大期の判定
        if liquidity_score > 2:  # 2σ以上の流動性拡大
            if self.annual_bets_used < self.max_annual_bets:
                # 年1-2回の"Bet the ranch"
                self.annual_bets_used += 1
                return portfolio.nav * 0.8  # 80%投入
        
        # 3. 流動性縮小期
        elif liquidity_score < -1:
            return 0  # ポジションゼロ
        
        # 4. 通常期は中程度
        return portfolio.nav * 0.05
    
    def _analyze_cb_liquidity(self):
        """中央銀行流動性の加減速分析"""
        # FRB, ECB, BOJ等のバランスシート変化率
        cb_data = self.get_central_bank_data()
        
        liquidity_growth = sum([
            cb['balance_sheet_growth'] * cb['weight']
            for cb in cb_data
        ])
        
        # Zスコア計算
        return (liquidity_growth - self.mean) / self.std
```

### 4. 統合財務戦略AI
```python
class IntegratedFinancialAI:
    """5大トレーダーの手法を統合した財務AI"""
    
    def __init__(self):
        self.strategies = {
            'lipschutz': LipschutzCorrelationVAR(),
            'ptj': PTJSystematicRisk(),
            'kovner': KovnerStopBasedSizing(),
            'soros': SorosReflexivity(),
            'druckenmiller': DruckenmillerLiquidity()
        }
        self.risk_engine = RiskEngine()
        
    async def calculate_optimal_position(self, signal, portfolio, market_data):
        """各戦略を統合した最適ポジションサイズ決定"""
        
        # 1. 各戦略でのサイズ計算
        strategy_sizes = {}
        for name, strategy in self.strategies.items():
            size = strategy.calculate_position_size(
                signal, portfolio, market_data
            )
            strategy_sizes[name] = size
        
        # 2. 市場環境に応じた重み付け
        weights = self._calculate_strategy_weights(market_data)
        
        # 3. 加重平均 + リスク制限
        weighted_size = sum([
            strategy_sizes[name] * weights[name]
            for name in strategy_sizes
        ])
        
        # 4. 追加のリスク制限
        final_size = self._apply_risk_limits(
            weighted_size,
            portfolio,
            signal
        )
        
        # 5. 実行可能性チェック
        return self._ensure_executable(final_size, market_data)
    
    def _calculate_strategy_weights(self, market_data):
        """市場環境に応じた戦略の重み付け"""
        weights = {
            'lipschutz': 0.2,      # 常に相関管理
            'ptj': 0.2,            # システマティックリスク
            'kovner': 0.2,         # 保守的アプローチ
            'soros': 0.0,          # 特殊状況のみ
            'druckenmiller': 0.0   # 特殊状況のみ
        }
        
        # リフレクシビティ検出時
        if self._detect_reflexivity(market_data):
            weights['soros'] = 0.4
            weights['ptj'] = 0.1
            
        # 流動性サイクル検出時
        if self._detect_liquidity_cycle(market_data):
            weights['druckenmiller'] = 0.4
            weights['kovner'] = 0.1
            
        # 正規化
        total = sum(weights.values())
        return {k: v/total for k, v in weights.items()}

### 5. リスクエンジン統合
```python
class RiskEngine:
    """統合リスク管理エンジン"""
    
    def __init__(self):
        self.var_calculator = VARCalculator()
        self.correlation_monitor = CorrelationMonitor()
        self.drawdown_controller = DrawdownController()
        self.event_monitor = EventMonitor()
        self.psychological_monitor = PsychologicalLoadMonitor()
        
    def apply_comprehensive_limits(self, position_size, portfolio, signal):
        """包括的なリスク制限適用"""
        
        # 1. VaR制限（ポートフォリオ全体）
        portfolio_var = self.var_calculator.calculate_portfolio_var(
            portfolio, 
            confidence=0.99
        )
        var_limit = portfolio.nav * 0.10  # 最大10% VaR
        
        if portfolio_var + signal.potential_var > var_limit:
            var_ratio = (var_limit - portfolio_var) / signal.potential_var
            position_size *= max(0, var_ratio)
        
        # 2. 相関制限
        correlation_exposure = self.correlation_monitor.get_exposure(
            signal.symbol,
            portfolio
        )
        
        if correlation_exposure > 0.7:  # 70%以上の相関
            position_size *= (1 - correlation_exposure)
        
        # 3. ドローダウン制限
        current_dd = self.drawdown_controller.current_drawdown
        if current_dd > 0.10:  # 10%以上のDD
            position_size *= (1 - current_dd / 0.20)  # 20%で完全停止
        
        # 4. イベントリスク
        if self.event_monitor.has_high_impact_event(hours=24):
            position_size *= 0.3  # 70%削減
        
        # 5. 心理的負荷
        psych_load = self.psychological_monitor.get_load_factor()
        if psych_load > 0.7:
            position_size *= math.sqrt(0.5)  # √2で除算
            
        return max(0, position_size)

class PsychologicalLoadMonitor:
    """心理的負荷のモニタリング"""
    
    def __init__(self):
        self.consecutive_losses = 0
        self.max_daily_trades = 10
        self.today_trades = 0
        self.stress_indicators = []
        
    def get_load_factor(self) -> float:
        """心理的負荷係数（0-1）"""
        factors = []
        
        # 連敗によるストレス
        if self.consecutive_losses > 0:
            loss_stress = min(1.0, self.consecutive_losses / 5)
            factors.append(loss_stress)
        
        # オーバートレード
        trade_stress = self.today_trades / self.max_daily_trades
        factors.append(trade_stress)
        
        # 時間帯ストレス（深夜/早朝）
        hour = datetime.now().hour
        if hour < 6 or hour > 22:
            factors.append(0.5)
        
        # ボラティリティストレス
        if self.get_market_volatility() > 2.0:  # 2σ以上
            factors.append(0.7)
            
        return np.mean(factors) if factors else 0.0

### 6. 統合実行システム
```python
class IntegratedTradingSystem:
    """マルチタイムフレーム + 高度財務戦略の統合システム"""
    
    def __init__(self):
        # マルチタイムフレーム
        self.mtf_analyzer = MultiTimeframeAITrader()
        
        # 財務戦略
        self.financial_ai = IntegratedFinancialAI()
        
        # リスク管理
        self.risk_engine = RiskEngine()
        
        # 実行管理
        self.execution_manager = ExecutionManager()
        
    async def process_market_tick(self, tick_data: dict):
        """統合処理フロー"""
        
        # 1. マルチタイムフレーム分析
        mtf_signal = await self.mtf_analyzer.process_market_update(tick_data)
        
        if mtf_signal.action == TradingAction.HOLD:
            return None
            
        # 2. ポートフォリオ状態取得
        portfolio = self.get_portfolio_state()
        
        # 3. 財務戦略によるサイズ決定
        optimal_size = await self.financial_ai.calculate_optimal_position(
            mtf_signal,
            portfolio,
            tick_data
        )
        
        # 4. リスクエンジンによる最終調整
        final_size = self.risk_engine.apply_comprehensive_limits(
            optimal_size,
            portfolio,
            mtf_signal
        )
        
        # 5. 実行
        if final_size > self.get_minimum_trade_size():
            order = self.execution_manager.create_order(
                signal=mtf_signal,
                size=final_size,
                risk_params=self._calculate_risk_params(mtf_signal)
            )
            
            return await self.execution_manager.execute(order)
            
        return None
    
    def _calculate_risk_params(self, signal):
        """リスクパラメータの計算"""
        return {
            'stop_loss': self._calculate_stop_loss(signal),
            'take_profit': self._calculate_take_profit(signal),
            'trailing_stop': self._calculate_trailing_stop(signal),
            'time_limit': self._calculate_time_limit(signal)
        }

### 7. バックテスト対応
```python
class BacktestEngine:
    """イベントソーシングを活用したバックテスト"""
    
    def __init__(self):
        self.event_store = EventStore()
        self.trading_system = IntegratedTradingSystem()
        
    async def run_backtest(self, start_date: str, end_date: str):
        """過去データでのバックテスト実行"""
        
        # イベントの再生
        events = await self.event_store.replay(start_date, end_date)
        
        results = {
            'trades': [],
            'pnl': [],
            'drawdown': [],
            'metrics': {}
        }
        
        for event in events:
            # 各イベントでシステムを実行
            decision = await self.trading_system.process_market_tick(
                event['tick_data']
            )
            
            if decision:
                results['trades'].append(decision)
                
        # パフォーマンス分析
        results['metrics'] = self._calculate_performance_metrics(results)
        
        return results
    
    def _calculate_performance_metrics(self, results):
        """パフォーマンスメトリクスの計算"""
        return {
            'total_return': self._calculate_return(results['pnl']),
            'sharpe_ratio': self._calculate_sharpe(results['pnl']),
            'max_drawdown': self._calculate_max_dd(results['drawdown']),
            'win_rate': self._calculate_win_rate(results['trades']),
            'profit_factor': self._calculate_profit_factor(results['trades']),
            'strategy_attribution': self._calculate_attribution(results['trades'])
        }
```

### 7. テクニカル統合AI
```python
class TechnicalIntegrationAI:
    """マルチタイムフレームのテクニカル分析統合"""
    
    def __init__(self):
        self.llm = self._initialize_llm()
        self.cache = LRUCache(maxsize=1000)
        
    async def analyze_multitimeframe(self, context: dict) -> dict:
        """複数時間足の統合分析"""
        
        prompt = f"""
        マルチタイムフレーム取引判断：
        
        【シグナル状況】
        5分足: {context['signals']['5M']}
        15分足（基準）: {context['signals']['15M']}
        1時間足: {context['signals']['1H']}
        
        【ポートフォリオ】
        現在のポジション: {context['portfolio']['positions']}
        使用証拠金率: {context['portfolio']['margin_usage']}%
        
        【判断基準】
        - 15分足を基準（重み50%）
        - 5分足で短期勢い確認（重み20%）
        - 1時間足でトレンド確認（重み30%）
        
        最適なエントリー/エグジット判断を行ってください。
        """
        
        response = await self.llm.analyze(prompt)
        return self._parse_response(response)
```

### 8. ポートフォリオ管理
```python
class PortfolioManager:
    """ポートフォリオ状態の管理と評価"""
    
    def __init__(self):
        self.positions = {}
        self.risk_calculator = RiskCalculator()
        
    def get_current_state(self) -> dict:
        """現在のポートフォリオ状態"""
        return {
            'positions': self._get_active_positions(),
            'margin_usage': self._calculate_margin_usage(),
            'unrealized_pnl': self._calculate_unrealized_pnl(),
            'correlation_risk': self._calculate_correlation_risk(),
            'max_drawdown': self._calculate_max_drawdown(),
            'sharpe_ratio': self._calculate_sharpe_ratio()
        }
    
    def _calculate_correlation_risk(self) -> float:
        """ポジション間の相関リスク計算"""
        if len(self.positions) < 2:
            return 0.0
            
        correlations = []
        for pos1, pos2 in itertools.combinations(self.positions.values(), 2):
            corr = self.risk_calculator.calculate_correlation(
                pos1.symbol, 
                pos2.symbol
            )
            correlations.append(abs(corr))
            
        return np.mean(correlations) if correlations else 0.0
```

### 9. イベントストア（シンプル実装）
```python
class EventStore:
    """取引イベントの永続化（JSONL形式）"""
    
    def __init__(self, base_path: str = "./events"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
        
    async def record(self, event: dict) -> None:
        """イベントの記録"""
        date = datetime.now().strftime("%Y%m%d")
        file_path = self.base_path / f"events_{date}.jsonl"
        
        async with aiofiles.open(file_path, mode='a') as f:
            await f.write(json.dumps(event) + '\n')
    
    async def replay(self, start_date: str, end_date: str) -> List[dict]:
        """バックテスト用のイベント再生"""
        events = []
        for file_path in self._get_files_in_range(start_date, end_date):
            async with aiofiles.open(file_path, mode='r') as f:
                async for line in f:
                    events.append(json.loads(line))
        
        return sorted(events, key=lambda e: e['timestamp'])
```

## 📊 実装上の最適化

### 1. レスポンス時間の最適化
```python
# 時間足ごとの更新頻度を考慮した処理
class OptimizedProcessor:
    def __init__(self):
        self.last_update = {'5M': None, '15M': None, '1H': None}
        
    async def process_tick(self, tick):
        updates = []
        
        # 更新が必要な時間足のみ処理
        for tf in ['5M', '15M', '1H']:
            if self._needs_update(tick.timestamp, tf):
                updates.append(tf)
                self.last_update[tf] = tick.timestamp
        
        if updates:
            return await self.process_timeframes(tick, updates)
```

### 2. AI判断のキャッシング戦略
```python
# 類似パターンでの判断再利用
def _generate_cache_key(self, context: dict) -> str:
    """シグナルパターンのハッシュ化"""
    signal_pattern = []
    for tf in ['5M', '15M', '1H']:
        if signal := context['signals'].get(tf):
            signal_pattern.append(f"{tf}:{signal.action}:{signal.strength//10}")
    
    portfolio_state = f"margin:{context['portfolio']['margin_usage']//5}"
    
    return hashlib.md5(
        f"{':'.join(signal_pattern)}:{portfolio_state}".encode()
    ).hexdigest()
```

## 🚀 段階的実装計画

### Phase 1: 基盤構築（1ヶ月）
- [ ] PKGシステムのPython移植
- [ ] 指標計算エンジンの実装
- [ ] 基本的なイベントストア

### Phase 2: マルチタイムフレーム統合（1.5ヶ月）
- [ ] 並列シグナル生成システム
- [ ] 時間足統合ロジック
- [ ] バックテスト環境

### Phase 3: AI統合（1.5ヶ月）
- [ ] LLMベースの判断エンジン
- [ ] プロンプトエンジニアリング
- [ ] キャッシング最適化

### Phase 4: 本番環境構築（1ヶ月）
- [ ] リアルタイムデータ接続
- [ ] 監視・アラートシステム
- [ ] 段階的な本番移行

## 📈 期待される成果

1. **5大トレーダーの財務戦略の統合実装**
   - Lipschutz: 相関VARによる精密なリスク管理
   - PTJ: システマティックな1%ルール
   - Kovner: 保守的なStop先行サイジング
   - Soros: リフレクシビティによる集中投資
   - Druckenmiller: 流動性サイクルの活用

2. **マルチタイムフレーム統合**
   - 15分足基準の意思決定
   - 5分足・1時間足の補完的活用
   - 時間足間の矛盾をAIで解決

3. **高度なリスク管理**
   - ポートフォリオVaR制限
   - 相関クラスタリング
   - 心理的負荷の定量化
   - イベントリスク管理

4. **完全な監査証跡**
   - イベントソーシングによる再現性
   - 戦略帰属分析
   - パフォーマンス要因分解

5. **実践的な実装**
   - 既存PKGロジックの継承
   - 段階的な改善可能性
   - バックテスト対応

## 📊 まとめ

この設計により、以下が実現されます：

1. **世界トップトレーダーの財務管理手法の統合**
   - 各トレーダーの強みを市場環境に応じて活用
   - 守りの徹底と攻めの集中を両立

2. **マルチタイムフレームの高度な統合**
   - PKGシステムによる確定的シグナル生成
   - AIによる時間足間の矛盾解決

3. **包括的なリスク管理**
   - VaR、相関、ドローダウン、心理的負荷の総合管理
   - イベントリスクへの自動対応

4. **実装の現実性**
   - 既存ロジックの移植可能性
   - 段階的な開発・テスト・導入

---

最終更新日：2025年1月4日