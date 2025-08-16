# FX取引システム PKGシステム設計書（関数型DAG版）

## 1. 概要

### 1.1 目的
本設計書は、FX取引システムの中核となる関数型DAGベースのPKG（パッケージ）システムの詳細設計を定義する。

### 1.2 スコープ
- 関数型DAGアーキテクチャ
- 階層的ID体系と管理方式
- パッケージ関数の定義と実装
- マルチタイムフレーム並列実行
- 大規模ロジック構成手法

### 1.3 前提条件
- 191^系統の階層的識別子体系
- 6つの時間足（1分、5分、15分、30分、60分、240分）での並列実行
- 関数合成による大規模ロジック構成
- 生データ記号からの連続的データフロー

## 2. PKGシステムアーキテクチャ

### 2.1 関数型DAGシステム構成図

```
┌─────────────────────────────────────────────────────┐
│              PKG関数型DAGシステム全体構成             │
│                                                      │
│  ┌─────────────────────────────────────────────┐   │
│  │            統合判断層（階層3以上）           │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐ │   │
│  │  │ 方向判定 │  │ 15分足   │  │ エントリー│ │   │
│  │  │ 統合     │  │ 統合     │  │ 信号生成 │ │   │
│  │  │(階層3～) │  │(階層4～) │  │(階層5～) │ │   │
│  │  └──────────┘  └──────────┘  └──────────┘ │   │
│  └─────────────────────────────────────────────┘   │
│                      ▲                             │
│  ┌─────────────────────────────────────────────┐   │
│  │          パッケージ関数層（階層2）              │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐ │   │
│  │  │ Z(2),Z(8)│  │ SL,OR,AND│  │ CO,SG,AS │ │   │
│  │  │ 算術演算 │  │ 選択論理 │  │ 集計処理 │ │   │
│  │  │(階層2)   │  │(階層2)   │  │(階層2)   │ │   │
│  │  └──────────┘  └──────────┘  └──────────┘ │   │
│  └─────────────────────────────────────────────┘   │
│                      ▲                             │
│  ┌─────────────────────────────────────────────┐   │
│  │        生データ記号処理層（階層1）             │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐ │   │
│  │  │ Value    │  │ Logic    │  │ Indicator│ │   │
│  │  │ 基本     │  │ Signal   │  │ Value    │ │   │
│  │  │(階層1)   │  │(階層1)   │  │(階層1)   │ │   │
│  │  └──────────┘  └──────────┘  └──────────┘ │   │
│  └─────────────────────────────────────────────┘   │
│                      ▲                             │
│  ┌─────────────────────────────────────────────┐   │
│  │           生データ記号層（2700記号）           │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐ │   │
│  │  │ 平均足   │  │ MA,      │  │ 価格     │ │   │
│  │  │ OHLC     │  │ ボリバン │  │ レンジ   │ │   │
│  │  └──────────┘  └──────────┘  └──────────┘ │   │
│  └─────────────────────────────────────────────┘   │
│                                                      │
│  [時間足並列処理: 1M,5M,15M,30M,60M,240M]            │
└─────────────────────────────────────────────────────┘
```

### 2.2 コンポーネント詳細

#### 2.2.1 パッケージ関数定義
```python
@dataclass
class PKGFunction:
    """パッケージ関数定義"""
    id: str                 # [時間足][周期][通貨]^[階層]-[連番] (例: 191^2-126)
    function_type: str      # Z, SL, OR, AND, CO, SG, AS, MN, etc.
    input_arity: int        # 入力数（2, 4, 8等）
    input_refs: List[str]   # 参照する生データ記号(AA001等)またはPKG ID
    output_type: str        # "code" (1,2,3) or "value" (連続値)
    timeframe: str          # 対象時間足
    level: int             # 階層レベル (1:生データのみ, 2:階層1参照, 3:階層1,2参照...)
    
    def evaluate(self, inputs: Dict[str, Any]) -> Any:
        """関数評価実行"""
        pass

class PKGFunctionManager:
    """PKG関数システム管理クラス"""
    
    def __init__(self):
        self.function_registry = {}  # ID -> PKGFunction
        self.dag_manager = DAGManager()
        self.executor = MultiTimeframeExecutor()
        
    def register_function(self, function: PKGFunction):
        """パッケージ関数登録"""
        # 階層レベル検証
        if not self._validate_hierarchy(function):
            raise ValueError(f"Invalid hierarchy: {function.id}")
            
        self.function_registry[function.id] = function
        self.dag_manager.add_node(function)
        
    def build_dag(self) -> DAG:
        """関数DAG構築"""
        return self.dag_manager.build_dependency_graph()
```

#### 2.2.2 PKG ID体系管理
```python
class PKGIDManager:
    """PKG ID体系管理"""
    
    # ID形式: [時間足][周期][通貨]^[階層]-[連番]
    # 例: 191^2-126 = 1分足,周期なし,USDJPY,第2階層,126番
    PKG_ID_PATTERN = re.compile(r'^(\d)(\d)(\d)\^(\d+)-(\d+)$')
    
    # 時間足プレフィックス
    TIMEFRAME_PREFIX = {
        '1M': 1, '5M': 2, '15M': 3,
        '30M': 4, '60M': 5, '240M': 6
    }
    
    def generate_function_id(self, level: int, func_type: int, number: int) -> str:
        """関数ID生成"""
        return f"{level}91^{func_type}-{number}"
    
    def parse_function_id(self, function_id: str) -> dict:
        """PKG ID解析"""
        match = self.PKG_ID_PATTERN.match(function_id)
        if not match:
            raise ValueError(f"Invalid PKG ID format: {function_id}")
            
        return {
            'timeframe': int(match.group(1)),  # 1:1分,2:5分,3:15分,4:30分,5:1時間,6:4時間
            'period': int(match.group(2)),     # 9:共通(周期なし)、他:TSML周期
            'currency': int(match.group(3)),   # 1:USDJPY,2:EURUSD,3:EURJPY
            'hierarchy': int(match.group(4)),  # 1:生データ参照,2:階層1参照,3以降:下位階層参照
            'sequence': int(match.group(5))    # 連番
        }
    
    def get_timeframe_function_id(self, base_id: str, timeframe: str) -> str:
        """時間足別関数ID取得"""
        parsed = self.parse_function_id(base_id)
        tf_prefix = self.TIMEFRAME_PREFIX.get(timeframe, 1)
        
        # 時間足プレフィックスを最上位に追加
        return f"{tf_prefix}{parsed['level']}91^{parsed['type']}-{parsed['number']}"
    
    def validate_hierarchy(self, function_id: str, input_refs: List[str]) -> bool:
        """階層依存関係検証"""
        func_level = self.parse_function_id(function_id)['hierarchy']
        
        for ref_id in input_refs:
            if '^' in ref_id:  # PKG IDの場合
                ref_level = self.parse_function_id(ref_id)['hierarchy']
                if ref_level >= func_level:  # 自分より下位階層のみ参照可能
                    return False
            # 生データ記号(AA001等)は階層1でのみ参照可能
            elif func_level != 1:
                return False
        return True
```

## 3. パッケージ関数システム

### 3.1 関数タイプ定義

#### 3.1.1 パッケージ関数タイプ
```python
class PKGFunctionType(Enum):
    """パッケージ関数タイプ定義"""
    # 算術演算関数
    Z2 = "Z(2)"         # 2入力算術演算（減算用）
    Z8 = "Z(8)"         # 8入力 mod演算
    RO = "RO"           # ROUNDDOWN関数
    
    # 選択・論理関数
    SL = "SL"           # SELECT関数（可変入力）
    BL = "BL"           # BLOCK SELECT関数
    OR = "OR"           # 論理OR演算
    AND = "AND"         # 論理AND演算
    X2 = "X2"           # 2入力マッチング関数
    
    # 集計処理関数
    CO = "CO"           # COUNT関数（時間窓での累積カウント）
    SG = "SG"           # SUM_GROUP関数（グループ内積算）
    AS = "AS"           # AVERAGE_SECTION（区間平均計算）
    
    # 時間処理関数
    MN = "MN"           # MINUTE関数（時刻処理）
    SS = "SS"           # SPECIFIED_SHUKI（指定周期関数）
    
    # 特殊関数
    I = "I"             # IDEAL関数（理想値計算）
    NL = "NL"           # LINEAR_LINE（線形補間）
    
    # 生データシンボル
    VALUE = "VALUE"     # 生データシンボルのみ（Level 1）
    LOGIC_SIGNAL = "LOGIC_SIGNAL"   # 上下計算シグナル
    INDICATOR_VALUE = "INDICATOR_VALUE" # 指標値

class PKGOutputType(Enum):
    """パッケージ出力タイプ"""
    CODE = "code"       # コード値 (0,1,2,3)
    VALUE = "value"     # 連続値
    BOOLEAN = "boolean" # 論理値
```

#### 3.1.2 関数実装例
```python
class PKGFunctionImplementations:
    """パッケージ関数実装例"""
    
    @staticmethod
    def z2_subtract(input1: float, input2: float) -> float:
        """Z(2) - 2入力減算関数"""
        return input1 - input2
    
    @staticmethod
    def z8_mod(inputs: List[float]) -> int:
        """Z(8) - 8入力mod演算"""
        if len(inputs) != 8:
            raise ValueError("Z8 requires exactly 8 inputs")
        sum_val = sum(inputs)
        return int(sum_val) % 8
    
    @staticmethod
    def sl_select(range_values: List[Any], index: int) -> Any:
        """SL - SELECT関数（範囲指定の行数分）"""
        if 0 <= index < len(range_values):
            return range_values[index]
        return None
    
    @staticmethod
    def sign_function(value: float) -> int:
        """符号関数 - 連続値→{1,2}コード化"""
        return 1 if value >= 0 else 2
    
    @staticmethod
    def and2_logic(code1: int, code2: int) -> int:
        """AND2 - 2入力論理AND"""
        # 1=True, 2=Falseとして処理
        bool1 = (code1 == 1)
        bool2 = (code2 == 1)
        return 1 if (bool1 and bool2) else 2
    
    @staticmethod
    def co_count(time_series: List[int], target_code: int) -> int:
        """CO - COUNT関数（時間窓での特定コードカウント）"""
        return time_series.count(target_code)
```

### 3.2 DAG評価エンジン

#### 3.2.1 関数DAG評価アルゴリズム
```python
class PKGFunctionDAGEngine:
    """パッケージ関数DAG評価エンジン"""
    
    def __init__(self):
        self.function_registry = {}  # ID -> PKGFunction
        self.dag_graph = nx.DiGraph()  # DAGグラフ
        self.executor_pool = {}
        
    async def evaluate_all_timeframes(self) -> Dict[str, PKGEvaluationResult]:
        """全時間足での並列DAG評価"""
        
        timeframes = ['1M', '5M', '15M', '30M', '60M', '240M']
        tasks = []
        
        for tf in timeframes:
            tasks.append(self.evaluate_dag(tf))
        
        results = await asyncio.gather(*tasks)
        return {tf: result for tf, result in zip(timeframes, results)}
    
    def evaluate_dag(self, timeframe: str) -> PKGEvaluationResult:
        """指定時間足でのDAG評価"""
        
        # 1. トポロジカルソートで評価順序決定
        evaluation_order = nx.topological_sort(self.dag_graph)
        
        # 2. 中間計算値保存用
        intermediate_values = {}
        execution_path = []
        direction_code = 3  # デフォルト: 待機
        
        # 3. 階層順に関数評価（生データ記号→階層1→階層2...）
        for node_id in evaluation_order:
            function = self.function_registry[node_id]
            
            # 時間足フィルタリング
            if function.timeframe != timeframe:
                continue
                
            # 入力値収集
            inputs = self._collect_inputs(function, intermediate_values)
            
            # 関数実行
            output = function.evaluate(inputs)
            intermediate_values[node_id] = output
            execution_path.append(node_id)
            
            # Level 3（統合判断層）で方向コード出力
            if function.level == 3 and function.output_type == "code":
                direction_code = output
        
        # 4. 結果返却
        return PKGEvaluationResult(
            timeframe=timeframe,
            direction_code=direction_code,  # 1:上, 2:下, 3:待機
            confidence=self._calculate_confidence(intermediate_values),
            intermediate_values=intermediate_values,
            execution_path=execution_path
        )
    
    def _collect_inputs(self, function: PKGFunction, values: dict) -> dict:
        """関数の入力値収集"""
        inputs = {}
        for ref_id in function.input_refs:
            if ref_id in values:
                inputs[ref_id] = values[ref_id]
            else:
                # 生データ記号から取得
                inputs[ref_id] = self._get_raw_symbol_data(ref_id)
        return inputs
```

## 4. マルチタイムフレーム実行システム

### 4.1 並列実行エンジン
```python
class MultiTimeframeExecutor:
    """マルチタイムフレーム並列実行エンジン"""
    
    def __init__(self):
        self.dag_engine = PKGFunctionDAGEngine()
        self.performance_tracker = PerformanceTracker()
        
    async def execute_trading_cycle(self) -> Dict[str, int]:
        """取引サイクル実行（全時間足）"""
        
        # 1. 全時間足でのDAG並列評価
        start_time = time.time()
        results = await self.dag_engine.evaluate_all_timeframes()
        
        # 2. パフォーマンス記録
        execution_time = time.time() - start_time
        self.performance_tracker.record_cycle(execution_time, results)
        
        # 3. 各時間足の方向コードを返却
        direction_codes = {}
        for tf, result in results.items():
            direction_codes[tf] = result.direction_code
            
        return direction_codes  # {'15M': 1, '5M': 2, ...}
```

### 4.2 関数合成パイプライン
```python
class FunctionCompositionPipeline:
    """関数合成によるパイプライン構築"""
    
    def compose_complex_logic(self, pattern: str) -> Callable:
        """複雑ロジックの関数合成"""
        
        if pattern == "MATCH_INDEX_FLOW":
            # MATCH → INDEX → sum → mod → ROUNDDOWN
            return self._compose_match_index_flow()
        elif pattern == "STATISTICAL_ANALYSIS":
            # CO → SG → AS → MN
            return self._compose_statistical_flow()
        else:
            raise ValueError(f"Unknown pattern: {pattern}")
    
    def _compose_match_index_flow(self) -> Callable:
        """MATCH→INDEXフローの合成"""
        def pipeline(inputs):
            # Step1: X2タイプ（範囲指定ルートIDと条件1の一致判定）
            match_result = PKGFunctionImplementations.x2_match(
                inputs['range_values'], 
                inputs['condition1']
            )
            
            # Step2: SLタイプ（一致結果に基づく出力値選定）
            selected_value = PKGFunctionImplementations.sl_select(
                inputs['output_values'],
                match_result
            )
            
            return selected_value
        
        return pipeline
```

## 5. 関数合成パイプラインシステム

### 5.1 大規模ロジック構成
```python
class LargeScaleLogicComposer:
    """大規模ロジック構成器"""
    
    def __init__(self):
        self.function_chains = {}
        self.optimization_rules = OptimizationRules()
        
    def build_trading_logic_dag(self) -> nx.DiGraph:
        """取引ロジックDAG構築"""
        
        dag = nx.DiGraph()
        
        # Level 1: 生データ処理ノード追加
        base_nodes = self._create_base_layer_nodes()
        dag.add_nodes_from(base_nodes)
        
        # Level 2: 中間処理ノード追加
        intermediate_nodes = self._create_intermediate_nodes()
        dag.add_nodes_from(intermediate_nodes)
        
        # Level 3: 統合判断ノード追加
        integration_nodes = self._create_integration_nodes()
        dag.add_nodes_from(integration_nodes)
        
        # エッジ追加（依存関係）
        self._add_dependency_edges(dag)
        
        # DAG検証
        if not nx.is_directed_acyclic_graph(dag):
            raise ValueError("Generated graph contains cycles!")
            
        return dag
        
    def _create_excel_function_chain(self, excel_formula: str) -> List[PKGFunction]:
        """Excel関数のパッケージ関数チェーンに変換"""
        
        # Excel関数解析
        parsed_formula = self._parse_excel_formula(excel_formula)
        
        # 関数チェーン生成
        function_chain = []
        for step in parsed_formula:
            pkg_function = self._excel_to_pkg_function(step)
            function_chain.append(pkg_function)
            
        return function_chain
```

### 5.2 実行パフォーマンス
```python
class PerformanceOptimizer:
    """DAG実行パフォーマンス最適化"""
    
    def __init__(self):
        self.benchmark_data = BenchmarkData()
        
    def optimize_dag_execution(self, dag: nx.DiGraph) -> nx.DiGraph:
        """DAG実行の最適化"""
        
        # 1. 並列化可能ノードの特定
        parallel_groups = self._identify_parallel_groups(dag)
        
        # 2. メモ化対象の特定
        memoization_targets = self._identify_memoization_targets(dag)
        
        # 3. 不要計算の除去
        pruned_dag = self._prune_unnecessary_computations(dag)
        
        # 4. 実行順序最適化
        optimized_dag = self._optimize_execution_order(pruned_dag)
        
        return optimized_dag
        
    def measure_performance(self, dag: nx.DiGraph) -> PerformanceMetrics:
        """パフォーマンス測定"""
        
        metrics = PerformanceMetrics()
        
        # 既存システムとの比較（メモから取得した実測値）
        target_metrics = {
            '全体': 19,      # ms
            'もみ': 77,      # ms  
            'OP分岐': 101.3, # ms
            'オーバーシュート': 550.6,  # ms
            '時間結合': 564.9  # ms
        }
        
        # 各処理時間測定
        for process_name, target_time in target_metrics.items():
            measured_time = self._measure_process_time(dag, process_name)
            metrics.add_measurement(process_name, measured_time, target_time)
            
        return metrics
```

### 5.3 DAG最適化
```python
class DAGOptimizationEngine:
    """DAG最適化エンジン"""
    
    def apply_optimization_strategies(self, dag: nx.DiGraph) -> nx.DiGraph:
        """最適化戦略適用"""
        
        optimized_dag = dag.copy()
        
        # 1. 共通部分式除去
        optimized_dag = self._eliminate_common_subexpressions(optimized_dag)
        
        # 2. 定数畳み込み
        optimized_dag = self._constant_folding(optimized_dag)
        
        # 3. デッドコード除去
        optimized_dag = self._dead_code_elimination(optimized_dag)
        
        # 4. ループ不変式の移動
        optimized_dag = self._loop_invariant_motion(optimized_dag)
        
        return optimized_dag
```

## 6. 評価結果データ構造

### 6.1 PKG評価結果
```python
@dataclass
class PKGEvaluationResult:
    """パッケージ関数評価結果"""
    timeframe: str                    # 時間足
    direction_code: int              # 方向コード(1:上, 2:下, 3:待機)
    confidence: float                # 確信度 (0.0-1.0)
    intermediate_values: Dict[str, Any]  # 中間計算値
    execution_path: List[str]        # 実行されたPKG関数のID順
    performance_metrics: Dict[str, float] # パフォーマンスメトリクス
    
class TradingDecisionResult:
    """取引判断結果（全時間足統合）"""
    primary_direction: int           # 主要方向（15分足基準）
    timeframe_consensus: Dict[str, int]  # 各時間足の方向コード
    confidence_by_timeframe: Dict[str, float]  # 時間足別確信度
    recommended_action: str          # 推奨アクション
    risk_assessment: str            # リスク評価
```

## 7. 実装上の考慮事項

### 7.1 システム移行
- **段階的移行**: 既存システムとの並行稼働による安全な移行
- **A/Bテスト**: 両システムの結果比較
- **パフォーマンス検証**: 目標19ms（全体）の維持

### 7.2 拡張性
- **新関数追加**: プラグイン方式での関数拡張
- **DAG構造変更**: 動的な依存関係変更
- **時間足追加**: 新しい時間足の追加対応

### 7.3 監視・運用
- **リアルタイム監視**: DAG実行パフォーマンスの監視
- **エラー処理**: 個別関数エラーの分離と復旧
- **ログ記録**: 実行パスと中間値の記録

---

最終更新日：2025年1月
バージョン：2.0（関数型DAG版）