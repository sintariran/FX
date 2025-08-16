"""
メモロジックパッケージ - Week 6 PKG関数実装
97個のメモファイルから抽出したFX取引ロジックをPKG関数として実装

Week 6で実装した核心PKG関数:
- 同逆判定(Dokyaku): 前々足乖離による方向判断、勝率55.7%〜56.1%
- 行帰判定(Ikikaeri): 前足の動きから今足の方向予測
- もみ判定(Momi): レンジ相場とブレイクアウト検出
- オーバーシュート判定: 残足による転換予測
- 時間結合(Jikan_Ketsugou): マルチタイムフレーム統合判断
- 乖離判断(Kairi): 平均足と実勢価格の乖離分析
- レンジ判定(Range): 軸周期による動的レンジ判定
- 予知計算(Yochi): 複数条件分岐による方向予測
"""

# Week 6 新規実装PKG関数
from .core_pkg_functions import (
    BasePKGFunction,
    PKGId,
    MarketData,
    OperationSignal,
    TimeFrame,
    Currency,
    Period,
    DokyakuFunction,
    IkikaerikFunction
)

from .advanced_pkg_functions import (
    MomiFunction,
    OvershootFunction,
    TimeKetsugouFunction
)

from .specialized_pkg_functions import (
    KairiFunction,
    RangeFunction,
    YochiFunction
)

from .pkg_system_integration import (
    PKGSystemIntegration,
    PKGExecutionResult,
    SystemPerformanceMetrics
)

# 既存のメモロジック関数（互換性維持）
try:
    from .operation_logic import (
        OperationLogicFunction,
        DivergenceDetectionFunction,
        ConversionJudgmentFunction,
        OperationLogicFactory
    )
    
    from .divergence_logic import (
        DivergenceAnalysisFunction,
        DivergenceStateFunction,
        PriceAverageRelationFunction
    )
    
    from .time_frame_logic import (
        TimeFrameConnectionFunction,
        MultiTimeFrameLogicFunction,
        TimeFrameCombinationFunction
    )
    
    from .situation_logic import (
        SituationStateFunction,
        DirectionJudgmentFunction,
        ResistanceLineFunction
    )
    
    LEGACY_FUNCTIONS_AVAILABLE = True
    
except ImportError:
    # 既存関数が見つからない場合はスキップ
    LEGACY_FUNCTIONS_AVAILABLE = False

__all__ = [
    # Week 6 新規PKG関数 - 核心実装
    'BasePKGFunction',
    'PKGId',
    'MarketData', 
    'OperationSignal',
    'TimeFrame',
    'Currency',
    'Period',
    'DokyakuFunction',        # 同逆判定
    'IkikaerikFunction',      # 行帰判定
    'MomiFunction',           # もみ判定
    'OvershootFunction',      # オーバーシュート判定
    'TimeKetsugouFunction',   # 時間結合
    'KairiFunction',          # 乖離判断
    'RangeFunction',          # レンジ判定
    'YochiFunction',          # 予知計算
    
    # システム統合
    'PKGSystemIntegration',
    'PKGExecutionResult',
    'SystemPerformanceMetrics',
]

# 既存関数が利用可能な場合は追加
if LEGACY_FUNCTIONS_AVAILABLE:
    __all__.extend([
        'OperationLogicFunction',
        'DivergenceDetectionFunction', 
        'ConversionJudgmentFunction',
        'OperationLogicFactory',
        'DivergenceAnalysisFunction',
        'DivergenceStateFunction',
        'PriceAverageRelationFunction',
        'TimeFrameConnectionFunction',
        'MultiTimeFrameLogicFunction',
        'TimeFrameCombinationFunction',
        'SituationStateFunction',
        'DirectionJudgmentFunction',
        'ResistanceLineFunction'
    ])

# バージョン情報
__version__ = "6.0.0"
__memo_analysis_date__ = "2025-08-15"
__memo_files_processed__ = 97
__core_concepts_implemented__ = [
    "同逆判定(Dokyaku)",
    "行帰判定(Ikikaeri)", 
    "もみ判定(Momi)",
    "オーバーシュート判定",
    "時間結合(Jikan_Ketsugou)",
    "乖離判断(Kairi)",
    "レンジ判定(Range)",
    "予知計算(Yochi)"
]