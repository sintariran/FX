# PKG DAG最適化戦略とAIエージェント活用方針

## 1. 重要な原則：AIエージェントの役割を限定する

### 1.1 ❌ 間違った使い方：AIエージェントに取引を任せる

```python
# 間違い：AIエージェントが取引判断を行う
class TradingAgent:
    def decide_trade(self, market_data):
        # LLMやMLモデルが直接取引を決定
        return ai_model.predict(market_data)  # ❌ これはやらない
```

### 1.2 ✅ 正しい使い方：DAG構造の探索と最適化のみ

```python
# 正解：AIエージェントはDAG構造の探索のみ
class DAGOptimizationAgent:
    def explore_dag_structure(self, current_dag, backtest_results):
        # DAGのノード構成や接続を探索
        # 新しいDAG構造の提案のみ
        return proposed_dag_structure  # ✅ 構造の提案だけ
```

## 2. AIエージェント（Mastraなど）の適切な活用範囲

### 2.1 AIエージェントが行うこと

#### DAG構造の探索
```python
class DAGStructureExplorer:
    """AIエージェントによるDAG構造探索"""
    
    def explore(self, current_performance):
        """
        DAG構造の改善案を探索
        
        行うこと：
        - ノードの追加/削除の提案
        - 階層構造の変更提案
        - 関数の組み合わせパターン探索
        - パラメータ範囲の提案
        """
        
        # 例：新しいノード追加の提案
        suggestions = []
        
        # 1. 現在のDAGの弱点を分析
        weak_points = self.analyze_weak_points(current_performance)
        
        # 2. 改善可能な構造を提案
        if weak_points['momi_detection_accuracy'] < 0.7:
            suggestions.append({
                'action': 'add_node',
                'layer': 2,
                'function': 'enhanced_momi_detection',
                'dependencies': ['191^1-101', '191^1-104']
            })
        
        # 3. 関数の組み合わせを提案
        if weak_points['signal_conflicts'] > 0.3:
            suggestions.append({
                'action': 'modify_aggregation',
                'node': '191^3-301',
                'new_function': 'weighted_voting',
                'reason': 'reduce_conflicts'
            })
        
        return suggestions
```

#### バックテストパラメータの探索
```python
class BacktestParameterExplorer:
    """バックテストのパラメータ空間探索"""
    
    def suggest_parameters(self, dag_structure, historical_performance):
        """
        テストすべきパラメータの組み合わせを提案
        
        行うこと：
        - 閾値の探索範囲提案
        - 重みの組み合わせ提案
        - 時間窓の最適化提案
        """
        
        return {
            'momi_threshold': [0.2, 0.3, 0.4],  # 探索範囲の提案
            'kairi_sensitivity': [1.5, 2.0, 2.5],
            'timeframe_weights': [
                {'1M': 0.1, '5M': 0.2, '15M': 0.4, '1H': 0.2, '4H': 0.1},
                {'1M': 0.05, '5M': 0.15, '15M': 0.5, '1H': 0.2, '4H': 0.1},
            ]
        }
```

### 2.2 AIエージェントが行わないこと

#### ❌ 取引の実行判断
```python
# AIエージェントはこれをやらない
def make_trading_decision(market_data):
    # 取引するかどうかの判断はDAGが行う
    # AIエージェントは関与しない
    pass
```

#### ❌ リアルタイムの市場分析
```python
# AIエージェントはこれをやらない
def analyze_current_market():
    # リアルタイム分析はDAGの役割
    # AIエージェントは構造の最適化のみ
    pass
```

#### ❌ ポジションサイジング
```python
# AIエージェントはこれをやらない
def calculate_position_size():
    # 財務DAGが決定論的に計算
    # AIエージェントは関与しない
    pass
```

## 3. Mastraを使った実装例

### 3.1 DAG探索エージェントの設計

```python
# src/optimization/dag_explorer_agent.py

from mastra import Agent, Tool, Memory
import numpy as np

class DAGExplorerAgent(Agent):
    """DAG構造探索専用エージェント"""
    
    def __init__(self):
        super().__init__(
            name="DAG Structure Explorer",
            description="Explores and optimizes DAG structures for trading",
            tools=[
                AnalyzePerformanceTool(),
                ProposeStructureTool(),
                SimulateDAGTool()
            ],
            memory=DAGExplorationMemory()
        )
    
    async def explore_dag_improvements(self, current_dag, performance_metrics):
        """
        DAG改善案を探索（取引判断はしない）
        
        Returns:
            改善案のリスト（構造のみ、取引判断は含まない）
        """
        
        # 1. 現在のパフォーマンスを分析
        analysis = await self.use_tool(
            "AnalyzePerformance",
            dag=current_dag,
            metrics=performance_metrics
        )
        
        # 2. 構造改善案を生成
        proposals = await self.use_tool(
            "ProposeStructure",
            weak_points=analysis['weak_points'],
            constraints={
                'max_layers': 50,
                'max_nodes_per_layer': 200,
                'no_horizontal_refs': True  # PKGルール遵守
            }
        )
        
        # 3. 提案をシミュレート（バックテストではない）
        simulated_structures = []
        for proposal in proposals:
            structure = await self.use_tool(
                "SimulateDAG",
                proposal=proposal
            )
            simulated_structures.append(structure)
        
        # 4. メモリに記録（学習用）
        self.memory.store(
            current_structure=current_dag,
            proposals=simulated_structures,
            performance=performance_metrics
        )
        
        return simulated_structures
```

### 3.2 探索結果の適用フロー

```python
class DAGOptimizationPipeline:
    """DAG最適化パイプライン"""
    
    def __init__(self):
        self.explorer_agent = DAGExplorerAgent()  # 探索エージェント
        self.backtester = Backtester()            # バックテスター（決定論的）
        self.dag_builder = DAGBuilder()           # DAG構築（決定論的）
    
    async def optimize(self, historical_data):
        """
        最適化フロー：
        1. エージェントが構造を提案
        2. 決定論的にバックテスト
        3. 最良の構造を選択
        """
        
        current_dag = self.dag_builder.current_dag
        current_performance = self.backtester.evaluate(
            current_dag, 
            historical_data
        )
        
        # エージェントは構造の提案のみ
        proposed_structures = await self.explorer_agent.explore_dag_improvements(
            current_dag,
            current_performance
        )
        
        # 各提案を決定論的にバックテスト
        best_structure = None
        best_performance = current_performance['sharpe_ratio']
        
        for structure in proposed_structures:
            # 提案された構造でDAGを構築
            test_dag = self.dag_builder.build_from_structure(structure)
            
            # 決定論的バックテスト
            performance = self.backtester.evaluate(test_dag, historical_data)
            
            if performance['sharpe_ratio'] > best_performance:
                best_performance = performance['sharpe_ratio']
                best_structure = structure
        
        # 最良の構造を適用
        if best_structure:
            self.dag_builder.apply_structure(best_structure)
            print(f"新しいDAG構造を適用: Sharpe改善 {best_performance:.3f}")
        
        return best_structure
```

## 4. 探索と実行の明確な分離

### 4.1 探索フェーズ（オフライン）

```python
class ExplorationPhase:
    """探索フェーズ：AIエージェントが活動"""
    
    def run(self):
        """
        週末や市場クローズ時に実行
        - DAG構造の探索
        - パラメータ空間の探索
        - バックテストによる検証
        """
        
        # AIエージェントによる探索
        proposed_dags = self.agent.explore()
        
        # 決定論的な評価
        best_dag = self.evaluate_proposals(proposed_dags)
        
        # 次の取引セッションで使用するDAGを確定
        self.save_production_dag(best_dag)
```

### 4.2 実行フェーズ（オンライン）

```python
class ExecutionPhase:
    """実行フェーズ：AIエージェントは関与しない"""
    
    def run(self):
        """
        市場オープン時に実行
        - 確定済みDAGによる決定論的評価
        - AIエージェントは一切関与しない
        - 純粋な関数評価のみ
        """
        
        # 事前に確定したDAGをロード
        production_dag = self.load_production_dag()
        
        while market.is_open():
            # 決定論的にDAGを評価
            signal = production_dag.evaluate(market.get_tick())
            
            # 決定論的に執行
            if signal['action'] == 'execute':
                self.execute_order(signal)
```

## 5. なぜこの分離が重要か

### 5.1 決定論性の保証

```yaml
取引実行時の要件:
  - 決定論的: 同じ入力→同じ出力
  - 高速: < 30ms
  - 検証可能: 全ての判断が追跡可能
  - 安定: 実行中の構造変更なし
```

### 5.2 責任の明確化

| フェーズ | 責任主体 | 実行タイミング | 特徴 |
|---------|---------|--------------|------|
| 探索 | AIエージェント | オフライン | 創造的、試行錯誤、時間制約なし |
| 評価 | バックテスター | オフライン | 決定論的、検証可能、再現可能 |
| 実行 | PKG DAG | リアルタイム | 決定論的、高速、ステートレス |

### 5.3 リスク管理

```python
class RiskSeparation:
    """リスクの分離"""
    
    # AIエージェントのリスク（オフラインで管理）
    exploration_risks = [
        "提案が不適切",      # → バックテストで検証
        "過学習",           # → 複数期間で検証
        "計算時間超過"       # → オフラインなので問題なし
    ]
    
    # 実行時のリスク（決定論的に管理）
    execution_risks = [
        "遅延",            # → 30ms以内を保証
        "エラー",          # → 純粋関数で防止
        "予期しない動作"    # → 決定論的なので発生しない
    ]
```

## 6. 実装チェックリスト

### 6.1 AIエージェント実装時の確認事項

- [ ] エージェントは構造提案のみを行うか？
- [ ] 取引判断をエージェントが行っていないか？
- [ ] エージェントの出力は構造定義のみか？
- [ ] 実行時にエージェントを呼び出していないか？
- [ ] バックテストは決定論的に実行されるか？

### 6.2 システム設計の確認事項

- [ ] 探索フェーズと実行フェーズが分離されているか？
- [ ] 実行フェーズは完全に決定論的か？
- [ ] DAG評価は30ms以内で完了するか？
- [ ] PKGルール（横参照禁止）を守っているか？
- [ ] ステートレス性が保たれているか？

## 7. まとめ

### 正しいAIエージェントの使い方

1. **探索専門**: DAG構造とパラメータの探索のみ
2. **オフライン実行**: 市場クローズ時に探索
3. **提案のみ**: 実際の評価は決定論的システムが実施
4. **学習と改善**: 過去の探索結果から学習

### 間違った使い方を避ける

1. **取引判断をさせない**: DAGが決定論的に判断
2. **リアルタイム実行させない**: 事前に構造を確定
3. **ブラックボックス化しない**: 全ての判断を追跡可能に

この原則を守ることで、AIの創造性を活用しつつ、取引システムの信頼性と安定性を保証できます。

---

作成日: 2025年1月
バージョン: 1.0.0