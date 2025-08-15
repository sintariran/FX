# FX取引システム バックテスト・フォワードテスト・自動最適化設計書

## 1. 概要

### 1.1 目的
本設計書は、FX取引システムにおけるバックテスト、フォワードテスト、およびロジック自動改善システムの詳細設計を定義する。

### 1.2 スコープ
- バックテストエンジン設計
- フォワードテスト環境構築
- ロジック自動最適化メカニズム
- 継続的改善パイプライン
- パフォーマンス評価フレームワーク

### 1.3 前提条件
- 約80%の予測合致率を基準
- PKGシステムとの完全統合
- AI判断層との連携
- イベントソーシングによる完全再現性

## 2. システムアーキテクチャ

### 2.1 全体構成

```
┌─────────────────────────────────────────────────────┐
│        継続的改善システム層（CILS）                  │
│                                                      │
│  ┌─────────────────────────────────────────────┐   │
│  │      検証・分析エンジン                       │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐ │   │
│  │  │ バック   │  │ フォワード│  │ ウォーク │ │   │
│  │  │ テスト   │  │ テスト   │  │ フォワード│ │   │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘ │   │
│  │       └──────────────┼──────────────┘       │   │
│  │                      ▼                       │   │
│  │  ┌─────────────────────────────────────────┐ │   │
│  │  │         精度分析モジュール               │ │   │
│  │  │  ・指標重ね合わせ率（一致率）計算      │ │   │
│  │  │  ・15分足予測精度測定（目標80%）       │ │   │
│  │  │  ・パターン成功率分析                  │ │   │
│  │  └────────────────┬────────────────────────┘ │   │
│  └───────────────────┼─────────────────────────┘   │
│                      ▼                             │
│  ┌─────────────────────────────────────────────┐   │
│  │      ルール調整エンジン                       │   │
│  │  ┌──────────────────────────────────────┐   │   │
│  │  │  ルールベース最適化                    │   │   │
│  │  │  ・閾値調整（指標一致率70%等）        │   │   │
│  │  │  ・指標ウェイト調整                    │   │   │
│  │  │  ・時間軸優先順位の最適化              │   │   │
│  │  └──────────────────────────────────────┘   │   │
│  │  ┌──────────────────────────────────────┐   │   │
│  │  │  失敗パターン対策ルール              │   │   │
│  │  │  ・高一致率での予測ミス時の対応      │   │   │
│  │  │  ・もみ合い時の判断保留ルール        │   │   │
│  │  │  ・経済指標発表時の特別処理          │   │   │
│  │  └──────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────┘   │
└──────────────────┬──────────────────────────────────┘
                   │ フィードバックループ
┌──────────────────┴──────────────────────────────────┐
│              統合判断AIエージェント層                │
│  （最適化されたパラメータとパターンを活用）          │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────┴──────────────────────────────────┐
│              取引ロジック層                          │
│  （PKG関数型DAGシステム）                       │
└─────────────────────────────────────────────────────┘
```

### 2.2 アーキテクチャ上の配置と役割分担

**継続的改善システム層（CILS: Continuous Improvement and Learning System）は、取引ロジック層と統合判断AIエージェント層の間に配置される独立したレイヤーとして実装されます。**

#### 役割の明確化

1. **検証・分析エンジン**（データ収集と評価）
   - バックテスト、フォワードテスト、ウォークフォワードテストの実行
   - テスト結果から精度分析モジュールへデータを供給
   - 客観的な性能評価の実施

2. **精度分析モジュール**（パフォーマンス測定）
   - 指標重ね合わせ率（一致率）の計算
   - 15分足予測精度の測定と目標80%との比較
   - パターンごとの成功率分析
   - 検証エンジンの結果を最適化エンジンが理解できる形に変換

3. **ルール調整エンジン**（改善実行）
   - 精度分析結果を基にルールベースでパラメータを調整
   - 失敗パターンに対する対策ルールを追加
   - 調整されたルールとパラメータを取引ロジック層へ反映

この明確な役割分担により：
- 検証→分析→最適化の一方向フローが確立
- 各コンポーネントの責任範囲が明確化
- 概念の重複を排除し、システムの保守性が向上

## 3. バックテストエンジン

### 3.1 コア機能

```python
class BacktestEngine:
    """バックテストエンジン"""
    
    def __init__(self):
        self.data_loader = HistoricalDataLoader()
        self.signal_generator = SignalGenerator()
        self.performance_tracker = PerformanceTracker()
        self.indicator_analyzer = IndicatorOverlapAnalyzer()
        
    async def run_backtest(self, 
                          start_date: datetime, 
                          end_date: datetime,
                          strategy: TradingStrategy) -> BacktestResult:
        """バックテスト実行"""
        
        # 1. ヒストリカルデータ読み込み
        historical_data = await self.data_loader.load(start_date, end_date)
        
        # 2. イベント再生
        results = []
        for timestamp, market_data in historical_data:
            # 指標の重ね合わせ率計算
            overlap_rate = self.indicator_analyzer.calculate_overlap_rate(
                market_data
            )
            
            # 予測生成
            prediction = strategy.predict(market_data, overlap_rate)
            
            # 実際の結果と比較
            actual = market_data.get_actual_direction()
            hit = (prediction == actual)
            
            results.append({
                'timestamp': timestamp,
                'prediction': prediction,
                'actual': actual,
                'hit': hit,
                'overlap_rate': overlap_rate,
                'indicators': market_data.indicators
            })
        
        # 3. 精度計算
        accuracy = sum(r['hit'] for r in results) / len(results)
        
        return BacktestResult(
            accuracy=accuracy,
            details=results,
            performance_metrics=self._calculate_metrics(results)
        )
```

### 3.2 指標重ね合わせ率分析

```python
class IndicatorOverlapAnalyzer:
    """指標重ね合わせ率分析器"""
    
    def calculate_overlap_rate(self, market_data: MarketData) -> dict:
        """指標の一致率を計算"""
        
        indicators = market_data.get_all_indicators()
        total_indicators = len(indicators)
        
        # 方向性カウント
        up_count = sum(1 for i in indicators if i.signal == 'UP')
        down_count = sum(1 for i in indicators if i.signal == 'DOWN')
        neutral_count = total_indicators - up_count - down_count
        
        # 一致率計算
        up_rate = up_count / total_indicators
        down_rate = down_count / total_indicators
        
        # 最大一致率と方向
        max_rate = max(up_rate, down_rate)
        consensus_direction = 'UP' if up_rate > down_rate else 'DOWN'
        
        return {
            'up_rate': up_rate,
            'down_rate': down_rate,
            'neutral_rate': neutral_count / total_indicators,
            'consensus_rate': max_rate,
            'consensus_direction': consensus_direction,
            'confidence': max_rate  # 確信度として使用
        }
```

### 3.3 15分足予測精度測定

```python
class M15PredictionAccuracyMeasurement:
    """15分足予測精度測定"""
    
    def __init__(self):
        self.target_accuracy = 0.80  # 目標80%合致率
        
    def measure_prediction_accuracy(self, 
                                   predictions: List[dict],
                                   timeframe: str = '15M') -> dict:
        """予測精度を測定"""
        
        # 時間足別にフィルタ
        m15_predictions = [p for p in predictions if p['timeframe'] == timeframe]
        
        # セグメント別精度計算
        segments = {
            'high_confidence': [],   # 一致率70%以上
            'medium_confidence': [], # 一致率50-70%
            'low_confidence': []     # 一致率50%未満
        }
        
        for pred in m15_predictions:
            overlap_rate = pred['overlap_rate']['consensus_rate']
            hit = pred['hit']
            
            if overlap_rate >= 0.7:
                segments['high_confidence'].append(hit)
            elif overlap_rate >= 0.5:
                segments['medium_confidence'].append(hit)
            else:
                segments['low_confidence'].append(hit)
        
        # セグメント別精度計算
        segment_accuracy = {}
        for segment, hits in segments.items():
            if hits:
                segment_accuracy[segment] = sum(hits) / len(hits)
            else:
                segment_accuracy[segment] = None
        
        # 全体精度
        all_hits = [p['hit'] for p in m15_predictions]
        overall_accuracy = sum(all_hits) / len(all_hits) if all_hits else 0
        
        return {
            'overall_accuracy': overall_accuracy,
            'segment_accuracy': segment_accuracy,
            'total_predictions': len(m15_predictions),
            'meets_target': overall_accuracy >= self.target_accuracy
        }
```

## 4. フォワードテスト環境

### 4.1 リアルタイム検証

```python
class ForwardTestEngine:
    """フォワードテストエンジン"""
    
    def __init__(self):
        self.live_data_stream = LiveDataStream()
        self.prediction_recorder = PredictionRecorder()
        self.performance_monitor = RealtimePerformanceMonitor()
        
    async def run_forward_test(self, strategy: TradingStrategy):
        """フォワードテスト実行"""
        
        async for market_data in self.live_data_stream:
            # リアルタイム予測
            prediction = strategy.predict(market_data)
            
            # 予測記録
            await self.prediction_recorder.record(
                timestamp=market_data.timestamp,
                prediction=prediction,
                market_data=market_data
            )
            
            # 15分後の検証スケジュール
            if market_data.timeframe == '15M':
                asyncio.create_task(
                    self._verify_prediction_later(
                        prediction_id=prediction.id,
                        delay_minutes=15
                    )
                )
            
            # パフォーマンス監視
            metrics = await self.performance_monitor.update(prediction)
            
            # 精度低下検出
            if metrics['rolling_accuracy'] < 0.75:  # 75%を下回ったら警告
                await self._trigger_optimization(metrics)
```

### 4.2 ウォークフォワード分析

```python
class WalkForwardAnalysis:
    """ウォークフォワード分析"""
    
    def __init__(self):
        self.optimization_window = 30  # 日
        self.test_window = 10          # 日
        self.step_size = 5             # 日
        
    async def run_analysis(self, start_date: datetime, end_date: datetime):
        """ウォークフォワード分析実行"""
        
        results = []
        current_date = start_date
        
        while current_date < end_date:
            # 最適化期間
            opt_start = current_date
            opt_end = opt_start + timedelta(days=self.optimization_window)
            
            # バックテストで最適化
            optimal_params = await self._optimize_parameters(
                opt_start, opt_end
            )
            
            # テスト期間
            test_start = opt_end
            test_end = test_start + timedelta(days=self.test_window)
            
            # フォワードテスト
            test_result = await self._forward_test(
                test_start, test_end, optimal_params
            )
            
            results.append({
                'optimization_period': (opt_start, opt_end),
                'test_period': (test_start, test_end),
                'parameters': optimal_params,
                'performance': test_result
            })
            
            # 次のステップへ
            current_date += timedelta(days=self.step_size)
        
        return self._analyze_stability(results)
```

## 5. ルールベース改善システム

### 5.1 継続的ルール調整パイプライン

```python
class RuleBasedOptimizationPipeline:
    """ルールベース最適化パイプライン"""
    
    def __init__(self):
        self.threshold_optimizer = ThresholdOptimizer()
        self.weight_adjuster = IndicatorWeightAdjuster()
        self.rule_updater = TradingRuleUpdater()
        self.optimization_interval = timedelta(days=7)  # 週次調整
        
    async def run_continuous_optimization(self):
        """継続的ルール調整実行"""
        
        while True:
            # 1. 直近のパフォーマンスデータ収集
            recent_data = await self._collect_recent_performance()
            
            # 2. 失敗パターン分析
            failure_patterns = await self._analyze_failure_patterns(recent_data)
            
            # 3. ルールベース調整
            adjustments = {}
            
            # 指標一致率の閾値調整
            if recent_data['low_confidence_trades'] > 0.3:  # 30%以上が低確信度
                adjustments['min_overlap_rate'] = 0.70  # 70%以上に引き上げ
            
            # 指標ウェイト調整
            indicator_performance = self._analyze_indicator_contribution(recent_data)
            adjustments['indicator_weights'] = self.weight_adjuster.calculate_new_weights(
                indicator_performance
            )
            
            # 失敗パターン対策ルール追加
            if 'high_overlap_miss' in failure_patterns:
                adjustments['add_rule'] = {
                    'name': 'high_overlap_miss_filter',
                    'condition': 'check_market_context_before_entry',
                    'parameters': failure_patterns['high_overlap_miss']
                }
            
            # 4. 検証
            validation_result = await self._validate_adjustments(adjustments)
            
            # 5. 適用判断
            if validation_result['expected_improvement'] > 0.02:  # 2%以上の改善見込み
                await self._apply_rule_adjustments(adjustments)
                logger.info(f"Rules adjusted: {adjustments}")
            
            # 次の調整まで待機
            await asyncio.sleep(self.optimization_interval.total_seconds())
```

### 5.2 関数合成パターン発見

```python
class BranchPatternDiscovery:
    """PKG関数合成によるパターン発見"""
    
    def discover_optimal_patterns(self, historical_data: pd.DataFrame) -> dict:
        """最適パターンの発見"""
        
        patterns = {}
        
        # 全指標組み合わせパターンを生成
        indicator_combinations = self._generate_combinations()
        
        for combination in indicator_combinations:
            # パターンごとの成功率計算
            success_rate = self._calculate_pattern_success(
                historical_data,
                combination
            )
            
            # 高成功率パターンを記録
            if success_rate > 0.75:  # 75%以上
                pattern_id = self._generate_pattern_id(combination)
                patterns[pattern_id] = {
                    'indicators': combination,
                    'success_rate': success_rate,
                    'sample_size': len(historical_data),
                    'confidence': self._calculate_confidence(
                        success_rate, 
                        len(historical_data)
                    )
                }
        
        # パターンをPKGシステムに統合
        self._integrate_to_pkg_system(patterns)
        
        return patterns
```

### 5.3 失敗パターン対策

```python
class FailurePatternRuleHandler:
    """失敗パターン対策ルールハンドラ"""
    
    def __init__(self):
        # メモに記載されている実際の対策パターン
        self.failure_rules = {
            'high_overlap_miss': {
                'description': '高一致率でも予測を外すケース',
                'rule': 'add_market_context_check',
                'parameters': {
                    'check_economic_calendar': True,
                    'check_momi_state': True,  # もみ合い確認
                    'min_trend_strength': 0.5
                }
            },
            'momi_state': {
                'description': 'もみ合い状態での誤判断',
                'rule': 'defer_judgment_in_range',
                'parameters': {
                    'range_threshold': 10,  # pips
                    'wait_for_breakout': True
                }
            },
            'economic_event': {
                'description': '経済指標発表時の特殊動作',
                'rule': 'special_handling_for_events',
                'parameters': {
                    'pre_event_minutes': 30,
                    'post_event_minutes': 60,
                    'reduce_position_size': 0.5
                }
            }
        }
        
    async def create_countermeasure_rule(self, failure_data: dict) -> dict:
        """失敗パターンに対する対策ルール作成"""
        
        # 失敗タイプ識別
        failure_type = self._identify_failure_type(failure_data)
        
        # 既知のパターンへの対応
        if failure_type in self.failure_rules:
            rule_template = self.failure_rules[failure_type]
            
            # ルールをPKGシステム形式に変換
            new_rule = {
                'rule_name': f"failsafe_{failure_type}",
                'condition': rule_template['rule'],
                'parameters': rule_template['parameters'],
                'priority': 100,  # 高優先度
                'enabled': True
            }
            
            return new_rule
        
        # 未知のパターンは記録して手動確認
        await self._log_unknown_pattern(failure_data)
        return None
```

## 6. パフォーマンス評価フレームワーク

### 6.1 総合評価メトリクス

```python
class PerformanceEvaluationFramework:
    """パフォーマンス評価フレームワーク"""
    
    def evaluate_comprehensive_performance(self, results: BacktestResult) -> dict:
        """総合パフォーマンス評価"""
        
        return {
            # 精度メトリクス
            'accuracy_metrics': {
                'overall_accuracy': results.accuracy,
                '15m_accuracy': results.m15_accuracy,
                'high_confidence_accuracy': results.high_conf_accuracy,
                'target_achievement': results.accuracy >= 0.80
            },
            
            # リスクメトリクス
            'risk_metrics': {
                'sharpe_ratio': self._calculate_sharpe_ratio(results),
                'max_drawdown': self._calculate_max_drawdown(results),
                'var_95': self._calculate_var(results, 0.95),
                'win_loss_ratio': self._calculate_win_loss_ratio(results)
            },
            
            # 安定性メトリクス
            'stability_metrics': {
                'rolling_accuracy_std': self._calculate_rolling_std(results),
                'parameter_sensitivity': self._analyze_sensitivity(results),
                'regime_adaptability': self._measure_regime_change(results)
            },
            
            # 効率性メトリクス
            'efficiency_metrics': {
                'avg_computation_time': results.avg_computation_time,
                'signal_quality': self._assess_signal_quality(results),
                'false_positive_rate': self._calculate_false_positives(results)
            }
        }
```

## 7. 統合実装

### 7.1 メインコントローラー

```python
class TestOptimizationController:
    """テスト・最適化統合コントローラー"""
    
    def __init__(self):
        self.backtest_engine = BacktestEngine()
        self.forward_test_engine = ForwardTestEngine()
        self.rule_optimization_pipeline = RuleBasedOptimizationPipeline()
        self.performance_evaluator = PerformanceEvaluationFramework()
        
    async def start_continuous_improvement(self):
        """継続的改善プロセス開始"""
        
        # 並行実行タスク
        tasks = [
            self._run_periodic_backtest(),      # 定期バックテスト
            self._run_forward_test(),           # 継続的フォワードテスト
            self._run_rule_adjustment_cycle(),  # ルール調整サイクル
            self._monitor_performance()         # パフォーマンス監視
        ]
        
        await asyncio.gather(*tasks)
```

## 8. PDCAサイクル実装

### 8.1 改善サイクル

```python
class PDCACycle:
    """PDCAサイクル実装"""
    
    async def execute_cycle(self):
        """PDCAサイクル実行"""
        
        while True:
            # Plan: 改善計画
            improvement_plan = await self._plan_improvements()
            
            # Do: 実行
            implementation_result = await self._implement_changes(
                improvement_plan
            )
            
            # Check: 検証
            validation_result = await self._validate_changes(
                implementation_result
            )
            
            # Act: 標準化または再計画
            if validation_result['successful']:
                await self._standardize_changes(implementation_result)
            else:
                await self._rollback_and_replan(implementation_result)
            
            # サイクル間隔
            await asyncio.sleep(86400)  # 日次実行
```

## 9. 監視とアラート

### 9.1 リアルタイム監視

```python
class OptimizationMonitor:
    """最適化監視システム"""
    
    def __init__(self):
        self.alert_thresholds = {
            'accuracy_drop': 0.75,      # 75%以下で警告
            'drawdown_limit': 0.10,     # 10%ドローダウンで警告
            'confidence_minimum': 0.60   # 60%以下の確信度で警告
        }
        
    async def monitor_and_alert(self):
        """監視とアラート"""
        
        while True:
            metrics = await self._collect_current_metrics()
            
            # 閾値チェック
            if metrics['current_accuracy'] < self.alert_thresholds['accuracy_drop']:
                await self._send_alert('ACCURACY_DROP', metrics)
                await self._trigger_emergency_optimization()
            
            # ダッシュボード更新
            await self._update_dashboard(metrics)
            
            await asyncio.sleep(60)  # 1分ごとに監視
```

---

## 10. まとめ

本設計により、バックテスト・フォワードテスト・ルールベース改善システムは以下の位置に実装されます：

1. **アーキテクチャ上の配置**: 継続的改善システム層（CILS）として、取引ロジック層と統合判断AIエージェント層の間に配置
2. **主要機能**: 
   - 約80%の予測精度を目標としたルールベース調整
   - 指標重ね合わせ率（一致率）の計算と閾値管理（70%以上等）
   - 失敗パターンの検出と対策ルールの追加
3. **現状のシステムとの整合性**:
   - PKGシステムへのルール調整結果の反映
   - もみ合い判定、経済指標対応など既存ロジックとの連携
   - 将来的な機械学習導入への拡張性を保持

---

最終更新日：2025年1月
バージョン：1.0