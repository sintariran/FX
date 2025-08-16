"""
統一PKG ID体系による完全なシステム実装
生データ層も含めてすべてPKG ID形式で管理
"""

from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


# ==========================================
# 統一PKG ID体系
# ==========================================
@dataclass
class UnifiedPKGID:
    """
    統一PKG ID: [時間足][周期][通貨]^[階層]-[連番]
    
    階層0: 生データ層（旧AA系、AB系など）
    階層1: 基本判定層（生データのみ参照）
    階層2: 統合判定層（階層1を参照）
    階層3: 最終判定層（階層2を参照）
    """
    timeframe: int    # 1=1分, 2=5分, 3=15分, 4=30分, 5=1時間, 6=4時間, 9=全時間共通
    period: int       # 9=共通(周期なし), 1-8=TSML周期
    currency: int     # 1=USDJPY, 2=EURUSD, 3=EURJPY, 4=GBPJPY, 9=全通貨共通
    hierarchy: int    # 0=生データ, 1=基本判定, 2=統合判定, 3=最終判定
    sequence: int     # 連番（データ種別を示す）
    
    def __str__(self):
        return f"{self.timeframe}{self.period}{self.currency}^{self.hierarchy}-{self.sequence:03d}"
    
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
    
    def for_currency(self, currency: int) -> 'UnifiedPKGID':
        """特定通貨用のIDを生成"""
        return UnifiedPKGID(
            timeframe=self.timeframe,
            period=self.period,
            currency=currency,
            hierarchy=self.hierarchy,
            sequence=self.sequence
        )
    
    def for_timeframe(self, timeframe: int) -> 'UnifiedPKGID':
        """特定時間足用のIDを生成"""
        return UnifiedPKGID(
            timeframe=timeframe,
            period=self.period,
            currency=self.currency,
            hierarchy=self.hierarchy,
            sequence=self.sequence
        )


# ==========================================
# 生データ層の定義（階層0）
# ==========================================
class RawDataSequence:
    """生データ層の連番定義"""
    # 価格データ（001-099）
    CURRENT_PRICE = 1      # 現在価格
    PREV_CLOSE = 2         # 前足終値
    CURRENT_HIGH = 3       # 現在足高値
    CURRENT_LOW = 4        # 現在足安値
    CURRENT_OPEN = 5       # 現在足始値
    
    # 平均足データ（101-199）
    HA_OPEN = 101         # 平均足始値
    HA_HIGH = 102         # 平均足高値
    HA_LOW = 103          # 平均足安値
    HA_CLOSE = 104        # 平均足終値
    
    # 計算指標（201-299）
    RANGE_WIDTH = 201     # レンジ幅
    CHANGE_RATE = 202     # 変化率
    KAIRI_RATE = 203      # 乖離率
    
    # ボリューム（301-399）
    VOLUME = 301          # 出来高
    
    @classmethod
    def get_name(cls, sequence: int) -> str:
        """連番から名称を取得"""
        names = {
            1: "現在価格",
            2: "前足終値",
            3: "現在足高値",
            4: "現在足安値",
            5: "現在足始値",
            101: "平均足始値",
            102: "平均足高値",
            103: "平均足安値",
            104: "平均足終値",
            201: "レンジ幅",
            202: "変化率",
            203: "乖離率",
            301: "出来高"
        }
        return names.get(sequence, f"データ{sequence}")


# ==========================================
# PKG ID生成ヘルパー
# ==========================================
class PKGIDFactory:
    """PKG ID生成ファクトリー"""
    
    @staticmethod
    def raw_data(data_type: int, timeframe: int = 9, 
                 currency: int = 9, period: int = 9) -> str:
        """
        生データ層のID生成
        
        Args:
            data_type: RawDataSequenceの値
            timeframe: 時間足（9=全時間共通）
            currency: 通貨（9=全通貨共通）
            period: 周期（9=共通）
        """
        return UnifiedPKGID(
            timeframe=timeframe,
            period=period,
            currency=currency,
            hierarchy=0,
            sequence=data_type
        ).__str__()
    
    @staticmethod
    def layer1(function_type: int, timeframe: int = 3, 
               currency: int = 1, period: int = 9) -> str:
        """階層1（基本判定）のID生成"""
        return UnifiedPKGID(
            timeframe=timeframe,
            period=period,
            currency=currency,
            hierarchy=1,
            sequence=function_type
        ).__str__()
    
    @staticmethod
    def layer2(function_type: int, timeframe: int = 3,
               currency: int = 1, period: int = 9) -> str:
        """階層2（統合判定）のID生成"""
        return UnifiedPKGID(
            timeframe=timeframe,
            period=period,
            currency=currency,
            hierarchy=2,
            sequence=function_type
        ).__str__()
    
    @staticmethod
    def layer3(function_type: int, timeframe: int = 3,
               currency: int = 1, period: int = 9) -> str:
        """階層3（最終判定）のID生成"""
        return UnifiedPKGID(
            timeframe=timeframe,
            period=period,
            currency=currency,
            hierarchy=3,
            sequence=function_type
        ).__str__()


# ==========================================
# 統一PKGシステム
# ==========================================
class UnifiedPKGSystem:
    """統一ID体系によるPKGシステム"""
    
    def __init__(self, pair: str = "USDJPY", timeframe: str = "15M"):
        self.pair = pair
        self.timeframe = timeframe
        self.currency_code = self._get_currency_code(pair)
        self.timeframe_code = self._get_timeframe_code(timeframe)
        self.nodes = {}
        self._build_dag()
    
    def _get_currency_code(self, pair: str) -> int:
        """通貨ペアコード取得"""
        return {
            "USDJPY": 1,
            "EURUSD": 2,
            "EURJPY": 3,
            "GBPJPY": 4
        }.get(pair, 1)
    
    def _get_timeframe_code(self, timeframe: str) -> int:
        """時間足コード取得"""
        return {
            "1M": 1,
            "5M": 2,
            "15M": 3,
            "30M": 4,
            "1H": 5,
            "4H": 6
        }.get(timeframe, 3)
    
    def _build_dag(self):
        """DAG構築"""
        # 通貨と時間足を考慮したID生成
        tf = self.timeframe_code
        cur = self.currency_code
        
        # 生データ層（階層0）のノード登録
        # 通貨別データ
        self.nodes[f"{tf}9{cur}^0-001"] = {
            'name': '現在価格',
            'type': 'raw_data',
            'dependencies': []
        }
        self.nodes[f"{tf}9{cur}^0-002"] = {
            'name': '前足終値',
            'type': 'raw_data',
            'dependencies': []
        }
        self.nodes[f"{tf}9{cur}^0-101"] = {
            'name': '平均足始値',
            'type': 'raw_data',
            'dependencies': []
        }
        self.nodes[f"{tf}9{cur}^0-104"] = {
            'name': '平均足終値',
            'type': 'raw_data',
            'dependencies': []
        }
        self.nodes[f"{tf}9{cur}^0-201"] = {
            'name': 'レンジ幅',
            'type': 'raw_data',
            'dependencies': []
        }
        
        # 階層1（基本判定）のノード
        self.nodes[f"{tf}9{cur}^1-101"] = {
            'name': 'もみ判定',
            'type': 'function',
            'dependencies': [f"{tf}9{cur}^0-201"]  # レンジ幅参照
        }
        self.nodes[f"{tf}9{cur}^1-102"] = {
            'name': '価格方向判定',
            'type': 'function',
            'dependencies': [f"{tf}9{cur}^0-001", f"{tf}9{cur}^0-002"]  # 現在価格、前足終値
        }
        self.nodes[f"{tf}9{cur}^1-103"] = {
            'name': '平均足方向判定',
            'type': 'function',
            'dependencies': [f"{tf}9{cur}^0-101", f"{tf}9{cur}^0-104"]  # 平均足始値、終値
        }
        
        # 階層2（統合判定）のノード
        self.nodes[f"{tf}9{cur}^2-201"] = {
            'name': '同逆判定',
            'type': 'function',
            'dependencies': [f"{tf}9{cur}^1-102", f"{tf}9{cur}^1-103"]
        }
        self.nodes[f"{tf}9{cur}^2-202"] = {
            'name': '行帰パターン',
            'type': 'function',
            'dependencies': [f"{tf}9{cur}^1-102", f"{tf}9{cur}^1-103"]
        }
        
        # 階層3（最終判定）のノード
        self.nodes[f"{tf}9{cur}^3-301"] = {
            'name': '最終シグナル',
            'type': 'function',
            'dependencies': [f"{tf}9{cur}^1-101", f"{tf}9{cur}^2-201", f"{tf}9{cur}^2-202"]
        }
    
    def get_node_for_currency(self, base_id: str, target_currency: str) -> str:
        """
        異なる通貨用のノードIDを取得
        
        例: 
        base_id = "391^1-101" (15分,USDJPY,もみ判定)
        target_currency = "EURUSD"
        → "392^1-101" (15分,EURUSD,もみ判定)
        """
        parsed = UnifiedPKGID.parse(base_id)
        target_code = self._get_currency_code(target_currency)
        new_id = parsed.for_currency(target_code)
        return str(new_id)
    
    def get_node_for_timeframe(self, base_id: str, target_timeframe: str) -> str:
        """
        異なる時間足用のノードIDを取得
        
        例:
        base_id = "391^1-101" (15分,USDJPY,もみ判定)
        target_timeframe = "1H"
        → "591^1-101" (1時間,USDJPY,もみ判定)
        """
        parsed = UnifiedPKGID.parse(base_id)
        target_code = self._get_timeframe_code(target_timeframe)
        new_id = parsed.for_timeframe(target_code)
        return str(new_id)
    
    def evaluate_multi_currency(self, raw_data: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
        """
        複数通貨の同時評価
        
        Args:
            raw_data: {
                "USDJPY": {"current_price": 110.5, ...},
                "EURUSD": {"current_price": 1.18, ...},
                ...
            }
        """
        results = {}
        
        for pair, data in raw_data.items():
            currency_code = self._get_currency_code(pair)
            tf = self.timeframe_code
            
            # 通貨別の生データIDで値を設定
            context = {
                f"{tf}9{currency_code}^0-001": data.get('current_price', 0),
                f"{tf}9{currency_code}^0-002": data.get('prev_close', 0),
                f"{tf}9{currency_code}^0-101": data.get('ha_open', 0),
                f"{tf}9{currency_code}^0-104": data.get('ha_close', 0),
                f"{tf}9{currency_code}^0-201": data.get('range_width', 0),
            }
            
            # DAG評価（簡略版）
            # 実際は各ノードの関数を評価
            final_signal_id = f"{tf}9{currency_code}^3-301"
            
            results[pair] = {
                'signal_id': final_signal_id,
                'signal': self._evaluate_node(final_signal_id, context),
                'currency_code': currency_code
            }
        
        return results
    
    def _evaluate_node(self, node_id: str, context: Dict[str, Any]) -> Any:
        """ノード評価（簡略版）"""
        # 実際の実装では各ノードの関数を実行
        # ここでは簡略化
        parsed = UnifiedPKGID.parse(node_id)
        
        if parsed.hierarchy == 3:  # 最終判定
            return 3  # 待機（デモ）
        elif parsed.hierarchy == 2:  # 統合判定
            return 1  # 買い（デモ）
        elif parsed.hierarchy == 1:  # 基本判定
            return 1  # 判定あり（デモ）
        else:  # 生データ
            return context.get(node_id, 0)
    
    def show_dag_structure(self):
        """DAG構造を表示"""
        print("=" * 70)
        print(f"📊 DAG構造 (通貨: {self.pair}, 時間足: {self.timeframe})")
        print("=" * 70)
        
        # 階層別に表示
        for hierarchy in range(4):
            nodes_in_layer = [
                (id, info) for id, info in self.nodes.items()
                if UnifiedPKGID.parse(id).hierarchy == hierarchy
            ]
            
            if nodes_in_layer:
                print(f"\n階層{hierarchy}:")
                for node_id, info in sorted(nodes_in_layer):
                    deps = ", ".join(info['dependencies']) if info['dependencies'] else "なし"
                    print(f"  {node_id}: {info['name']}")
                    print(f"    依存: {deps}")


# ==========================================
# 使用例
# ==========================================
def demonstrate_unified_system():
    """統一PKGシステムのデモンストレーション"""
    print("=" * 70)
    print("🔧 統一PKG ID体系デモンストレーション")
    print("=" * 70)
    
    # 1. ID生成例
    print("\n📝 ID生成例:")
    print("-" * 40)
    
    # 生データ層
    price_id = PKGIDFactory.raw_data(
        RawDataSequence.CURRENT_PRICE,
        timeframe=3,  # 15分
        currency=1    # USDJPY
    )
    print(f"USDJPY 15分足 現在価格: {price_id}")
    
    # 同じデータの別通貨
    eurusd_price_id = PKGIDFactory.raw_data(
        RawDataSequence.CURRENT_PRICE,
        timeframe=3,  # 15分
        currency=2    # EURUSD
    )
    print(f"EURUSD 15分足 現在価格: {eurusd_price_id}")
    
    # 2. システム構築
    print("\n📊 システム構築:")
    print("-" * 40)
    
    system = UnifiedPKGSystem(pair="USDJPY", timeframe="15M")
    system.show_dag_structure()
    
    # 3. 通貨切り替え
    print("\n🔄 通貨切り替え例:")
    print("-" * 40)
    
    base_id = "391^1-101"  # USDJPY もみ判定
    eurusd_id = system.get_node_for_currency(base_id, "EURUSD")
    print(f"USDJPY もみ判定: {base_id}")
    print(f"EURUSD もみ判定: {eurusd_id}")
    
    # 4. 時間足切り替え
    print("\n⏰ 時間足切り替え例:")
    print("-" * 40)
    
    hourly_id = system.get_node_for_timeframe(base_id, "1H")
    print(f"15分足 もみ判定: {base_id}")
    print(f"1時間足 もみ判定: {hourly_id}")
    
    # 5. 複数通貨評価
    print("\n🌍 複数通貨同時評価:")
    print("-" * 40)
    
    multi_data = {
        "USDJPY": {
            "current_price": 110.50,
            "prev_close": 110.45,
            "ha_open": 110.43,
            "ha_close": 110.48,
            "range_width": 0.20
        },
        "EURUSD": {
            "current_price": 1.1850,
            "prev_close": 1.1845,
            "ha_open": 1.1843,
            "ha_close": 1.1848,
            "range_width": 0.0015
        }
    }
    
    results = system.evaluate_multi_currency(multi_data)
    for pair, result in results.items():
        print(f"{pair}: シグナルID={result['signal_id']}, "
              f"結果={result['signal']}")


if __name__ == "__main__":
    demonstrate_unified_system()