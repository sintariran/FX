"""
PKG関数ファクトリー（TDD - REFACTOR: コード改善）

各PKG関数（Z, SL, OR, AND, CO, SG, AS, MN）を生成
メモファイルのロジックに基づく実装
"""

from typing import Dict, Any, Optional, List, Union
from abc import ABC, abstractmethod
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class FunctionMetadata:
    """関数メタデータ"""
    function_type: str
    arity: int
    description: str
    input_type: str  # "code" or "value"
    output_type: str  # "code" or "value"


class PKGFunction(ABC):
    """
    PKG関数の基底クラス
    
    PKGシステムの階層2（パッケージ関数層）で使用される
    基本的な演算・論理関数を定義
    """
    
    def __init__(self, arity: int, **kwargs):
        """
        Args:
            arity: 入力数（2, 4, 8など）
            **kwargs: 関数固有のパラメータ
        """
        self.arity = arity
        self.config = kwargs
        self.metadata = self._create_metadata()
        self._validate_arity()
    
    @abstractmethod
    def evaluate(self, inputs: Dict[str, Any]) -> Any:
        """
        関数評価
        
        Args:
            inputs: 入力値の辞書
            
        Returns:
            評価結果
        """
        pass
    
    @abstractmethod
    def _create_metadata(self) -> FunctionMetadata:
        """メタデータ生成"""
        pass
    
    def _validate_arity(self):
        """入力数の妥当性検証"""
        valid_arities = [1, 2, 4, 8]
        if self.arity not in valid_arities:
            logger.warning(f"Non-standard arity {self.arity} for {self.__class__.__name__}")
    
    def _extract_values(self, inputs: Dict[str, Any]) -> List[Any]:
        """入力辞書から値リストを抽出"""
        # input1, input2, ... の形式を想定
        values = []
        for i in range(1, self.arity + 1):
            key = f"input{i}"
            if key in inputs:
                values.append(inputs[key])
            elif len(inputs) >= i:
                # キーがない場合は順番に取得
                values.append(list(inputs.values())[i-1])
        
        return values[:self.arity]


class ZFunction(PKGFunction):
    """
    Z関数: 最大値選択
    
    複数の入力から最大値を選択する。
    取引コード（1:買い, 2:売り, 3:待機）の優先順位判定に使用。
    待機(3) > 売り(2) > 買い(1) の優先度。
    """
    
    def evaluate(self, inputs: Dict[str, Any]) -> Any:
        values = self._extract_values(inputs)
        return max(values) if values else 0
    
    def _create_metadata(self) -> FunctionMetadata:
        return FunctionMetadata(
            function_type="Z",
            arity=self.arity,
            description=f"最大値選択（{self.arity}入力）",
            input_type="code",
            output_type="code"
        )


class SLFunction(PKGFunction):
    """
    SL関数: 条件選択（Selection Logic）
    
    条件に基づいて2つの値から選択する。
    if-then-else形式の条件分岐を実現。
    """
    
    def evaluate(self, inputs: Dict[str, Any]) -> Any:
        # 特定のキー名を期待
        condition = inputs.get("condition", 0)
        if_true = inputs.get("if_true", 0)
        if_false = inputs.get("if_false", 0)
        
        # conditionが真（非ゼロ）ならif_true、偽（ゼロ）ならif_false
        return if_true if condition else if_false
    
    def _create_metadata(self) -> FunctionMetadata:
        return FunctionMetadata(
            function_type="SL",
            arity=3,
            description="条件選択",
            input_type="mixed",
            output_type="code"
        )


class ORFunction(PKGFunction):
    """
    OR関数: 論理和
    
    複数の入力のいずれかが真（非ゼロ）なら1を返す。
    複数条件の緩い判定に使用。
    """
    
    def evaluate(self, inputs: Dict[str, Any]) -> Any:
        values = self._extract_values(inputs)
        return 1 if any(bool(v) for v in values) else 0
    
    def _create_metadata(self) -> FunctionMetadata:
        return FunctionMetadata(
            function_type="OR",
            arity=self.arity,
            description=f"論理和（{self.arity}入力）",
            input_type="code",
            output_type="code"
        )


class ANDFunction(PKGFunction):
    """
    AND関数: 論理積
    
    すべての入力が真（非ゼロ）なら1を返す。
    複数条件の厳密な判定に使用。
    """
    
    def evaluate(self, inputs: Dict[str, Any]) -> Any:
        values = self._extract_values(inputs)
        if not values:
            return 0
        return 1 if all(bool(v) for v in values) else 0
    
    def _create_metadata(self) -> FunctionMetadata:
        return FunctionMetadata(
            function_type="AND",
            arity=self.arity,
            description=f"論理積（{self.arity}入力）",
            input_type="code",
            output_type="code"
        )


class COFunction(PKGFunction):
    """
    CO関数: カウント（Count）
    
    特定の値が入力中に何回出現するかをカウント。
    同じシグナルの出現頻度を測定。
    """
    
    def __init__(self, arity: int, target_value: Any = 1, **kwargs):
        """
        Args:
            arity: 入力数
            target_value: カウント対象の値（デフォルト: 1）
        """
        self.target_value = target_value
        super().__init__(arity, **kwargs)
    
    def evaluate(self, inputs: Dict[str, Any]) -> Any:
        values = self._extract_values(inputs)
        return sum(1 for v in values if v == self.target_value)
    
    def _create_metadata(self) -> FunctionMetadata:
        return FunctionMetadata(
            function_type="CO",
            arity=self.arity,
            description=f"値{self.target_value}のカウント（{self.arity}入力）",
            input_type="code",
            output_type="value"
        )


class SGFunction(PKGFunction):
    """
    SG関数: 符号（Sign）
    
    値の符号を返す（正:1, ゼロ:0, 負:-1）。
    価格変動の方向判定に使用。
    """
    
    def evaluate(self, inputs: Dict[str, Any]) -> Any:
        values = self._extract_values(inputs)
        value = values[0] if values else 0
        
        if value > 0:
            return 1
        elif value < 0:
            return -1
        else:
            return 0
    
    def _create_metadata(self) -> FunctionMetadata:
        return FunctionMetadata(
            function_type="SG",
            arity=1,
            description="符号判定",
            input_type="value",
            output_type="code"
        )


class ASFunction(PKGFunction):
    """
    AS関数: 合計（Add Sum）
    
    すべての入力値を合計する。
    複数指標の統合値計算に使用。
    """
    
    def evaluate(self, inputs: Dict[str, Any]) -> Any:
        values = self._extract_values(inputs)
        return sum(values) if values else 0
    
    def _create_metadata(self) -> FunctionMetadata:
        return FunctionMetadata(
            function_type="AS",
            arity=self.arity,
            description=f"合計（{self.arity}入力）",
            input_type="value",
            output_type="value"
        )


class MNFunction(PKGFunction):
    """
    MN関数: 最小値（Minimum）
    
    複数の入力から最小値を選択する。
    保守的な判定（最も慎重な選択）に使用。
    """
    
    def evaluate(self, inputs: Dict[str, Any]) -> Any:
        values = self._extract_values(inputs)
        return min(values) if values else 0
    
    def _create_metadata(self) -> FunctionMetadata:
        return FunctionMetadata(
            function_type="MN",
            arity=self.arity,
            description=f"最小値選択（{self.arity}入力）",
            input_type="code",
            output_type="code"
        )


class PKGFunctionFactory:
    """
    PKG関数ファクトリー
    
    各種PKG関数のインスタンスを生成する。
    PKGシステムの階層2で使用される基本関数を管理。
    """
    
    # 関数タイプとクラスのマッピング
    FUNCTION_CLASSES = {
        "Z": ZFunction,    # 最大値
        "SL": SLFunction,  # 選択論理
        "OR": ORFunction,  # 論理和
        "AND": ANDFunction,  # 論理積
        "CO": COFunction,  # カウント
        "SG": SGFunction,  # 符号
        "AS": ASFunction,  # 合計
        "MN": MNFunction   # 最小値
    }
    
    def __init__(self):
        self.created_functions = {}  # キャッシュ
    
    def create_function(self, 
                       function_type: str, 
                       arity: int = 1, 
                       cache_key: Optional[str] = None,
                       **kwargs) -> PKGFunction:
        """
        関数インスタンス生成
        
        Args:
            function_type: 関数タイプ（Z, SL, OR, AND, CO, SG, AS, MN）
            arity: 入力数
            cache_key: キャッシュ用のキー（オプション）
            **kwargs: 関数固有のパラメータ
            
        Returns:
            PKGFunctionインスタンス
            
        Raises:
            ValueError: 不明な関数タイプの場合
        """
        if function_type not in self.FUNCTION_CLASSES:
            raise ValueError(
                f"Unknown function type: {function_type}. "
                f"Available types: {list(self.FUNCTION_CLASSES.keys())}"
            )
        
        # キャッシュ確認
        if cache_key and cache_key in self.created_functions:
            logger.debug(f"Using cached function: {cache_key}")
            return self.created_functions[cache_key]
        
        # 関数インスタンス生成
        function_class = self.FUNCTION_CLASSES[function_type]
        
        # 特殊なパラメータを持つ関数の処理
        if function_type == "CO" and "target_value" in kwargs:
            function = function_class(arity, target_value=kwargs["target_value"])
        else:
            function = function_class(arity, **kwargs)
        
        # キャッシュ保存
        if cache_key:
            self.created_functions[cache_key] = function
        
        logger.debug(f"Created {function_type} function with arity {arity}")
        return function
    
    def get_function_info(self, function_type: str) -> Optional[str]:
        """関数の説明を取得"""
        if function_type not in self.FUNCTION_CLASSES:
            return None
        
        func_class = self.FUNCTION_CLASSES[function_type]
        return func_class.__doc__
    
    def list_available_functions(self) -> List[str]:
        """利用可能な関数タイプのリストを返す"""
        return list(self.FUNCTION_CLASSES.keys())