"""
関数合成器（TDD - GREEN: 最小限の実装）
"""

from typing import List, Tuple, Any, Dict
from .function_factory import PKGFunctionFactory, PKGFunction


class ComposedFunction:
    """合成関数"""
    
    def __init__(self, functions: List[PKGFunction]):
        self.functions = functions
    
    def evaluate(self, inputs: Dict[str, Any]) -> Any:
        """段階的に関数を適用"""
        result = inputs
        for func in self.functions:
            # 前の結果を次の入力として使用
            if isinstance(result, dict):
                result = func.evaluate(result)
            else:
                # 単一値の場合はinput1として渡す
                result = func.evaluate({"input1": result})
        return result


class FunctionComposer:
    """関数合成器"""
    
    def __init__(self, factory: PKGFunctionFactory):
        self.factory = factory
    
    def compose(self, function_specs: List[Tuple[str, int]]) -> ComposedFunction:
        """
        関数を合成
        
        Args:
            function_specs: [(関数タイプ, arity), ...]
        """
        functions = []
        for func_type, arity in function_specs:
            func = self.factory.create_function(func_type, arity)
            functions.append(func)
        
        return ComposedFunction(functions)