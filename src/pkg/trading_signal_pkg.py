"""
正しいPKG実装による取引シグナルシステム
完全な関数型DAGアーキテクチャ
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


# ==========================================
# 生データ層のID体系
# ==========================================
class RawDataSymbol(Enum):
    """生データ記号定義（メモファイルより）"""
    # AA系: 基本価格データ（001-329）
    AA001 = "現在ビッド価格"
    AA002 = "前足終値"
    AA003 = "現在足高値"
    AA004 = "現在足安値"
    AA005 = "現在足始値"
    
    # AB系: 派生価格データ（301-312）
    AB301 = "平均足始値"
    AB302 = "平均足高値"
    AB303 = "平均足安値"
    AB304 = "平均足終値"
    
    # As系: 時間足別データ（a=M1, b=M5, c=M15...）
    Asa001 = "1分足平均足"
    Asb001 = "5分足平均足"
    Asc001 = "15分足平均足"
    
    # BA系: ボリューム・出来高データ
    BA018 = "現在足出来高"
    
    # CA系: 計算指標
    CA001 = "レンジ幅"
    CA002 = "乖離率"


# ==========================================
# PKG ID体系の正確な実装
# ==========================================
@dataclass
class PKGID:
    """PKG ID: [時間足][周期][通貨]^[階層]-[連番]"""
    timeframe: int    # 1=1分, 2=5分, 3=15分, 4=30分, 5=1時間, 6=4時間
    period: int       # 9=共通(周期なし), その他=TSML周期
    currency: int     # 1=USDJPY, 2=EURUSD, 3=EURJPY
    hierarchy: int    # 1=生データ参照, 2=階層1参照, 3以降=下位階層参照
    sequence: int     # 連番
    
    def __str__(self):
        return f"{self.timeframe}{self.period}{self.currency}^{self.hierarchy}-{self.sequence}"
    
    @classmethod
    def parse(cls, pkg_id: str):
        """PKG ID文字列をパース"""
        import re
        match = re.match(r'^(\d)(\d)(\d)\^(\d+)-(\d+)$', pkg_id)
        if not match:
            raise ValueError(f"Invalid PKG ID: {pkg_id}")
        return cls(
            timeframe=int(match.group(1)),
            period=int(match.group(2)),
            currency=int(match.group(3)),
            hierarchy=int(match.group(4)),
            sequence=int(match.group(5))
        )


# ==========================================
# PKG基本関数の純粋な実装
# ==========================================
class PKGBaseFunction:
    """PKG基本関数の基底クラス（純粋関数）"""
    
    def evaluate(self, inputs: Dict[str, Any]) -> Any:
        """純粋関数としての評価"""
        raise NotImplementedError


class ZFunction(PKGBaseFunction):
    """Z関数: 算術演算"""
    
    def evaluate(self, inputs: Dict[str, Any]) -> float:
        """Z(2): 減算、Z(8): mod演算"""
        values = list(inputs.values())
        if len(values) == 2:
            return values[0] - values[1]
        elif len(values) == 8:
            return sum(values) % 8
        return 0.0


class SLFunction(PKGBaseFunction):
    """SL関数: 条件選択"""
    
    def evaluate(self, inputs: Dict[str, Any]) -> Any:
        """SL(condition, true_value, false_value)"""
        condition = inputs.get('condition', False)
        true_val = inputs.get('true_value', 0)
        false_val = inputs.get('false_value', 0)
        return true_val if condition else false_val


class ANDFunction(PKGBaseFunction):
    """AND関数: 論理積"""
    
    def evaluate(self, inputs: Dict[str, Any]) -> int:
        """AND(code1, code2): 1=True, 2=False, 3=待機"""
        values = list(inputs.values())
        # 3（待機）が含まれていたら待機
        if 3 in values:
            return 3
        # すべて1なら1（買い）
        if all(v == 1 for v in values):
            return 1
        # すべて2なら2（売り）
        if all(v == 2 for v in values):
            return 2
        # それ以外は待機
        return 3


class ORFunction(PKGBaseFunction):
    """OR関数: 論理和"""
    
    def evaluate(self, inputs: Dict[str, Any]) -> int:
        """OR(code1, code2): 優先順位付き選択"""
        values = list(inputs.values())
        # 3（待機）が最優先
        if 3 in values:
            return 3
        # 1か2があればそれを返す
        for v in [1, 2]:
            if v in values:
                return v
        return 0


class MNFunction(PKGBaseFunction):
    """MN関数: 最小値選択（優先順位）"""
    
    def evaluate(self, inputs: Dict[str, Any]) -> Any:
        """優先順位に基づく最小値選択"""
        # 優先度マップ（小さいほど優先）
        priority_map = inputs.get('priority_map', {})
        if not priority_map:
            return None
        
        # 有効な（0でない）項目から最小優先度を選択
        valid_items = {k: v for k, v in priority_map.items() if v > 0}
        if not valid_items:
            return None
        
        return min(valid_items, key=valid_items.get)


class COFunction(PKGBaseFunction):
    """CO関数: カウント"""
    
    def evaluate(self, inputs: Dict[str, Any]) -> int:
        """条件を満たす数をカウント"""
        values = list(inputs.values())
        target = inputs.get('target', 1)
        return sum(1 for v in values if v == target)


# ==========================================
# PKGノード（DAGの各ノード）
# ==========================================
@dataclass
class PKGNode:
    """PKGノード: DAGの各ノードを表現"""
    pkg_id: str
    function: PKGBaseFunction
    dependencies: List[str]  # 依存する記号またはPKG ID
    formula: str  # 関数式の説明
    
    def evaluate(self, context: Dict[str, Any]) -> Any:
        """ノードの評価（純粋関数）"""
        # 依存データを収集
        inputs = {}
        for dep in self.dependencies:
            if dep.startswith('A'):  # 生データ記号
                inputs[dep] = context.get('raw_data', {}).get(dep, 0)
            elif '^' in dep:  # PKG ID
                inputs[dep] = context.get('pkg_cache', {}).get(dep, 0)
            else:
                inputs[dep] = context.get(dep, 0)
        
        # 関数評価
        return self.function.evaluate(inputs)


# ==========================================
# 階層1: 生データから基本判定
# ==========================================
class Layer1Nodes:
    """階層1のPKGノード群（生データのみ参照）"""
    
    @staticmethod
    def create_momi_detection_node() -> PKGNode:
        """191^1-101: もみ判定ノード"""
        
        class MomiFunction(PKGBaseFunction):
            def evaluate(self, inputs: Dict[str, Any]) -> int:
                """もみ判定: 1=もみなし, 3=もみあり"""
                range_val = inputs.get('CA001', 0)  # レンジ幅
                threshold = inputs.get('threshold', 0.3)
                
                if range_val < threshold:
                    return 3  # もみ（待機）
                return 1  # もみなし（取引可能）
        
        return PKGNode(
            pkg_id="191^1-101",
            function=MomiFunction(),
            dependencies=['CA001'],
            formula="SL(CA001<threshold, 3, 1)"
        )
    
    @staticmethod
    def create_price_direction_node() -> PKGNode:
        """191^1-102: 価格方向判定ノード"""
        
        class DirectionFunction(PKGBaseFunction):
            def evaluate(self, inputs: Dict[str, Any]) -> int:
                """価格方向: 1=上昇, 2=下降, 3=中立"""
                current = inputs.get('AA001', 0)
                prev = inputs.get('AA002', 0)
                
                if current > prev * 1.001:  # 0.1%以上上昇
                    return 1
                elif current < prev * 0.999:  # 0.1%以上下降
                    return 2
                return 3  # 中立
        
        return PKGNode(
            pkg_id="191^1-102",
            function=DirectionFunction(),
            dependencies=['AA001', 'AA002'],
            formula="SL(Z(AA001,AA002)>0.001, 1, SL(Z(AA001,AA002)<-0.001, 2, 3))"
        )
    
    @staticmethod
    def create_heikin_direction_node() -> PKGNode:
        """191^1-103: 平均足方向判定ノード"""
        
        class HeikinDirectionFunction(PKGBaseFunction):
            def evaluate(self, inputs: Dict[str, Any]) -> int:
                """平均足方向: 1=陽線, 2=陰線"""
                ha_close = inputs.get('AB304', 0)
                ha_open = inputs.get('AB301', 0)
                
                return 1 if ha_close > ha_open else 2
        
        return PKGNode(
            pkg_id="191^1-103",
            function=HeikinDirectionFunction(),
            dependencies=['AB301', 'AB304'],
            formula="SL(AB304>AB301, 1, 2)"
        )
    
    @staticmethod
    def create_kairi_detection_node() -> PKGNode:
        """191^1-104: 乖離検出ノード"""
        
        class KairiFunction(PKGBaseFunction):
            def evaluate(self, inputs: Dict[str, Any]) -> int:
                """乖離検出: 1=乖離なし, 2=乖離あり"""
                real_price = inputs.get('AA001', 0)
                ha_close = inputs.get('AB304', 0)
                base_line = inputs.get('base_line', 10.0)
                
                # 実勢と平均足が基準線の異なる側にある
                real_above = real_price > base_line
                ha_above = ha_close > base_line
                
                return 2 if (real_above != ha_above) else 1
        
        return PKGNode(
            pkg_id="191^1-104",
            function=KairiFunction(),
            dependencies=['AA001', 'AB304'],
            formula="SL((AA001>base)!=(AB304>base), 2, 1)"
        )


# ==========================================
# 階層2: 階層1の結果を組み合わせ
# ==========================================
class Layer2Nodes:
    """階層2のPKGノード群（階層1の結果を参照）"""
    
    @staticmethod
    def create_dokyaku_judgment_node() -> PKGNode:
        """191^2-201: 同逆判定ノード"""
        
        class DokyakuFunction(PKGBaseFunction):
            def evaluate(self, inputs: Dict[str, Any]) -> int:
                """同逆判定: 複数の方向判定を統合"""
                price_dir = inputs.get('191^1-102', 3)
                heikin_dir = inputs.get('191^1-103', 3)
                kairi = inputs.get('191^1-104', 1)
                
                # 乖離がある場合は逆方向の可能性
                if kairi == 2:
                    # 価格と平均足が逆方向
                    if price_dir != 3 and heikin_dir != 3:
                        if price_dir != heikin_dir:
                            return 3 if price_dir == 1 else 1  # 転換シグナル
                
                # 通常は方向一致を確認
                if price_dir == heikin_dir and price_dir != 3:
                    return price_dir
                
                return 3  # 判定不能
        
        return PKGNode(
            pkg_id="191^2-201",
            function=DokyakuFunction(),
            dependencies=['191^1-102', '191^1-103', '191^1-104'],
            formula="AND(191^1-102, 191^1-103, SL(191^1-104==2, INV, ID))"
        )
    
    @staticmethod
    def create_ikikaeri_pattern_node() -> PKGNode:
        """191^2-202: 行帰パターン判定ノード"""
        
        class IkikaeriFunction(PKGBaseFunction):
            def evaluate(self, inputs: Dict[str, Any]) -> int:
                """行帰パターン: トレンド継続性判定"""
                heikin_dir = inputs.get('191^1-103', 3)
                price_dir = inputs.get('191^1-102', 3)
                
                # 両方同じ方向なら行行（継続）
                if heikin_dir == price_dir and price_dir != 3:
                    return price_dir
                
                # 方向が異なれば帰戻（転換）の可能性
                if heikin_dir != price_dir and price_dir != 3:
                    return 3  # 待機
                
                return 3
        
        return PKGNode(
            pkg_id="191^2-202",
            function=IkikaeriFunction(),
            dependencies=['191^1-102', '191^1-103'],
            formula="SL(191^1-102==191^1-103, 191^1-102, 3)"
        )
    
    @staticmethod
    def create_breakout_detection_node() -> PKGNode:
        """191^2-203: ブレイクアウト判定ノード"""
        
        class BreakoutFunction(PKGBaseFunction):
            def evaluate(self, inputs: Dict[str, Any]) -> int:
                """ブレイクアウト: もみからの抜け"""
                momi = inputs.get('191^1-101', 1)
                price_dir = inputs.get('191^1-102', 3)
                
                # もみ状態（3）から方向が確定したらブレイクアウト
                if momi == 1 and price_dir != 3:  # もみ解消＋方向確定
                    return price_dir
                
                return 0  # ブレイクアウトなし
        
        return PKGNode(
            pkg_id="191^2-203",
            function=BreakoutFunction(),
            dependencies=['191^1-101', '191^1-102'],
            formula="SL(191^1-101==1 AND 191^1-102!=3, 191^1-102, 0)"
        )


# ==========================================
# 階層3: 最終統合判定
# ==========================================
class Layer3Nodes:
    """階層3のPKGノード群（最終判定）"""
    
    @staticmethod
    def create_final_signal_node() -> PKGNode:
        """191^3-301: 最終シグナル統合ノード"""
        
        class FinalSignalFunction(PKGBaseFunction):
            def evaluate(self, inputs: Dict[str, Any]) -> int:
                """最終シグナル: MN関数による優先順位判定"""
                momi = inputs.get('191^1-101', 1)
                dokyaku = inputs.get('191^2-201', 3)
                ikikaeri = inputs.get('191^2-202', 3)
                breakout = inputs.get('191^2-203', 0)
                
                # もみ判定が最優先（3なら即座に待機）
                if momi == 3:
                    return 3
                
                # 優先順位マップ（小さいほど優先）
                priority_signals = {}
                
                if breakout != 0:
                    priority_signals['breakout'] = (1, breakout)
                
                if dokyaku != 3 and ikikaeri != 3:
                    if dokyaku == ikikaeri:
                        priority_signals['strong'] = (2, dokyaku)
                
                if dokyaku != 3:
                    priority_signals['dokyaku'] = (3, dokyaku)
                
                # 最優先シグナルを選択
                if priority_signals:
                    min_key = min(priority_signals, key=lambda k: priority_signals[k][0])
                    return priority_signals[min_key][1]
                
                return 3  # デフォルトは待機
        
        return PKGNode(
            pkg_id="191^3-301",
            function=FinalSignalFunction(),
            dependencies=['191^1-101', '191^2-201', '191^2-202', '191^2-203'],
            formula="MN([191^1-101, 191^2-201, 191^2-202, 191^2-203])"
        )


# ==========================================
# PKG DAGマネージャー
# ==========================================
class PKGDAGManager:
    """PKG DAG全体を管理（ステートレス）"""
    
    def __init__(self):
        self.nodes = {}
        self._build_dag()
    
    def _build_dag(self):
        """DAGを構築"""
        # 階層1ノード
        self.nodes['191^1-101'] = Layer1Nodes.create_momi_detection_node()
        self.nodes['191^1-102'] = Layer1Nodes.create_price_direction_node()
        self.nodes['191^1-103'] = Layer1Nodes.create_heikin_direction_node()
        self.nodes['191^1-104'] = Layer1Nodes.create_kairi_detection_node()
        
        # 階層2ノード
        self.nodes['191^2-201'] = Layer2Nodes.create_dokyaku_judgment_node()
        self.nodes['191^2-202'] = Layer2Nodes.create_ikikaeri_pattern_node()
        self.nodes['191^2-203'] = Layer2Nodes.create_breakout_detection_node()
        
        # 階層3ノード
        self.nodes['191^3-301'] = Layer3Nodes.create_final_signal_node()
    
    def evaluate(self, raw_data: Dict[str, float]) -> Tuple[int, Dict[str, Any]]:
        """
        DAG全体を評価（純粋関数、ステートレス）
        
        Args:
            raw_data: 生データ記号の辞書
            
        Returns:
            (signal, debug_info): シグナル（1:買い, 2:売り, 3:待機）とデバッグ情報
        """
        context = {
            'raw_data': raw_data,
            'pkg_cache': {}
        }
        
        # トポロジカルソートに従って評価
        evaluation_order = [
            # 階層1（並列実行可能）
            ['191^1-101', '191^1-102', '191^1-103', '191^1-104'],
            # 階層2（並列実行可能）
            ['191^2-201', '191^2-202', '191^2-203'],
            # 階層3
            ['191^3-301']
        ]
        
        for layer in evaluation_order:
            for node_id in layer:
                if node_id in self.nodes:
                    result = self.nodes[node_id].evaluate(context)
                    context['pkg_cache'][node_id] = result
        
        # 最終シグナル
        final_signal = context['pkg_cache'].get('191^3-301', 3)
        
        # デバッグ情報
        debug_info = {
            'layer1': {k: v for k, v in context['pkg_cache'].items() if k.startswith('191^1')},
            'layer2': {k: v for k, v in context['pkg_cache'].items() if k.startswith('191^2')},
            'layer3': {k: v for k, v in context['pkg_cache'].items() if k.startswith('191^3')},
        }
        
        return final_signal, debug_info


# ==========================================
# 外部インターフェース
# ==========================================
class TradingSignalPKG:
    """取引シグナルPKGシステム（完全な関数型DAG）"""
    
    def __init__(self, pair: str = "USDJPY"):
        self.pair = pair
        self.dag_manager = PKGDAGManager()
        self._setup_thresholds()
    
    def _setup_thresholds(self):
        """通貨ペア別の閾値設定"""
        if self.pair == "USDJPY":
            self.momi_threshold = 0.30
        elif self.pair == "EURJPY":
            self.momi_threshold = 0.40
        elif self.pair == "EURUSD":
            self.momi_threshold = 0.0030
        else:
            self.momi_threshold = 0.50
    
    def generate_signal(self, candle: Dict, index: int, 
                       all_candles: List[Dict]) -> Tuple[int, Dict]:
        """
        シグナル生成（ステートレス）
        
        Returns:
            (signal, debug_info): シグナルとデバッグ情報
        """
        if index < 3:
            return 3, {}
        
        # 生データ記号の値を計算
        raw_data = self._calculate_raw_data(candle, index, all_candles)
        
        # DAG評価（純粋関数）
        signal, debug_info = self.dag_manager.evaluate(raw_data)
        
        return signal, debug_info
    
    def _calculate_raw_data(self, candle: Dict, index: int, 
                           all_candles: List[Dict]) -> Dict[str, float]:
        """生データ記号の値を計算"""
        prev = all_candles[index - 1] if index > 0 else candle
        prev2 = all_candles[index - 2] if index > 1 else prev
        
        # 平均足計算
        ha_prev = self._calc_heikin_ashi(prev2, None)
        ha_current = self._calc_heikin_ashi(prev, ha_prev)
        
        return {
            # 基本価格データ
            'AA001': candle['close'],  # 現在価格
            'AA002': prev['close'],     # 前足終値
            'AA003': candle['high'],    # 現在足高値
            'AA004': candle['low'],     # 現在足安値
            'AA005': candle['open'],    # 現在足始値
            
            # 派生価格データ（平均足）
            'AB301': ha_current['open'],
            'AB302': ha_current['high'],
            'AB303': ha_current['low'],
            'AB304': ha_current['close'],
            
            # 計算指標
            'CA001': candle['high'] - candle['low'],  # レンジ幅
            'CA002': (candle['close'] - prev['close']) / prev['close'] if prev['close'] != 0 else 0,  # 変化率
            
            # パラメータ
            'threshold': self.momi_threshold,
            'base_line': 10.0
        }
    
    def _calc_heikin_ashi(self, candle: Dict, prev_ha: Optional[Dict]) -> Dict:
        """平均足計算"""
        if prev_ha is None:
            ha_open = (candle['open'] + candle['close']) / 2
        else:
            ha_open = (prev_ha['open'] + prev_ha['close']) / 2
        
        ha_close = (candle['open'] + candle['high'] + 
                   candle['low'] + candle['close']) / 4
        ha_high = max(candle['high'], ha_open, ha_close)
        ha_low = min(candle['low'], ha_open, ha_close)
        
        return {
            'open': ha_open,
            'high': ha_high,
            'low': ha_low,
            'close': ha_close
        }