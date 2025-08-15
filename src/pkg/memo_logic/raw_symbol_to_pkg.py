#!/usr/bin/env python3
"""
生データシンボルをPKG ID体系に変換
AA001-329, BA-BB, CA001-142等をPKG IDフォーマットに変換

例:
- AA001 (1分足, 共通, USDJPY) → 191^0-AA001
- CA012 (15分足, 共通, USDJPY) → 391^0-CA012
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import logging

# PKG IDコンポーネント定義
TIMEFRAMES = {
    1: "1分足",
    2: "5分足", 
    3: "15分足",
    4: "30分足",
    5: "1時間足",
    6: "4時間足"
}

PERIODS = {
    9: "共通",  # 周期なし
    10: "TSML周期10",
    15: "TSML周期15",
    30: "TSML周期30",
    45: "TSML周期45",
    60: "TSML周期60",
    90: "TSML周期90",
    180: "TSML周期180"
}

CURRENCIES = {
    1: "USDJPY",
    2: "EURUSD",
    3: "EURJPY"
}

@dataclass
class RawSymbol:
    """生データシンボル定義"""
    symbol: str           # 例: AA001, CA012
    category: str        # 例: AA, CA
    number: int          # 例: 1, 12
    timeframe: int       # 時間足 (1-6)
    period: int          # 周期 (通常は9)
    currency: int        # 通貨ペア (1-3)
    
    def to_pkg_id(self) -> str:
        """PKG ID形式に変換"""
        return f"{self.timeframe}{self.period}{self.currency}^0-{self.symbol}"

class RawSymbolConverter:
    """生データシンボルのPKG ID変換器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.symbol_rules = self._init_symbol_rules()
        
    def _init_symbol_rules(self) -> Dict[str, Dict]:
        """
        シンボルカテゴリ毎のルール定義
        メモファイルとlist.txtから抽出した情報に基づく
        """
        return {
            'AA': {
                'range': (1, 329),
                'default_timeframe': 1,  # 1分足
                'description': 'Os乖離指標'
            },
            'BA': {
                'range': (1, 329), 
                'default_timeframe': 1,  # 1分足
                'description': 'OsMACD指標'
            },
            'BB': {
                'range': (1, 329),
                'default_timeframe': 1,  # 1分足
                'description': 'Os基準指標'
            },
            'CA': {
                'range': (1, 142),
                'default_timeframe': 3,  # 15分足（メモより）
                'description': '平均足ベース指標'
            },
            'DA': {
                'range': (1, 100),
                'default_timeframe': 3,  # 15分足
                'description': '特殊指標'
            },
            'SA': {
                'range': (1, 20),
                'default_timeframe': 3,  # 15分足
                'description': '階層1指標'
            },
            'SB': {
                'range': (1, 20),
                'default_timeframe': 3,  # 15分足
                'description': '階層2指標'
            }
        }
    
    def parse_symbol(self, symbol: str, 
                    timeframe: Optional[int] = None,
                    period: int = 9,
                    currency: int = 1) -> Optional[RawSymbol]:
        """
        生データシンボルをパース
        
        Args:
            symbol: シンボル名 (例: "AA001", "CA012")
            timeframe: 時間足 (1-6) Noneの場合はデフォルト値使用
            period: 周期 (デフォルト9=共通)
            currency: 通貨ペア (デフォルト1=USDJPY)
        """
        # シンボルパターンのマッチング
        match = re.match(r'^([A-Z]{2})(\d{1,3})$', symbol)
        if not match:
            self.logger.warning(f"無効なシンボル形式: {symbol}")
            return None
            
        category = match.group(1)
        number = int(match.group(2))
        
        # カテゴリ別のルール適用
        if category not in self.symbol_rules:
            self.logger.warning(f"未知のカテゴリ: {category}")
            return None
            
        rule = self.symbol_rules[category]
        min_num, max_num = rule['range']
        
        if not (min_num <= number <= max_num):
            self.logger.warning(f"範囲外の番号: {symbol} (範囲: {min_num}-{max_num})")
            return None
        
        # 時間足の決定
        if timeframe is None:
            timeframe = rule['default_timeframe']
            
        return RawSymbol(
            symbol=symbol,
            category=category,
            number=number,
            timeframe=timeframe,
            period=period,
            currency=currency
        )
    
    def convert_batch(self, symbols: List[str],
                     default_timeframe: Optional[int] = None,
                     default_period: int = 9,
                     default_currency: int = 1) -> Dict[str, str]:
        """
        複数のシンボルを一括変換
        
        Returns:
            Dict[symbol, pkg_id]のマッピング
        """
        results = {}
        
        for symbol in symbols:
            raw_symbol = self.parse_symbol(
                symbol,
                timeframe=default_timeframe,
                period=default_period,
                currency=default_currency
            )
            
            if raw_symbol:
                results[symbol] = raw_symbol.to_pkg_id()
                self.logger.debug(f"変換: {symbol} → {raw_symbol.to_pkg_id()}")
                
        return results
    
    def extract_from_kairi_string(self, kairi_str: str) -> List[str]:
        """
        KAIRI列の文字列からシンボルを抽出
        例: "CA011_CA038_CA048_CA058" → ["CA011", "CA038", "CA048", "CA058"]
        """
        symbols = []
        
        # アンダースコア区切りまたはカンマ区切り
        parts = re.split(r'[_,\s]+', kairi_str)
        
        for part in parts:
            # シンボルパターンにマッチするもののみ抽出
            if re.match(r'^[A-Z]{2}\d{1,3}$', part):
                symbols.append(part)
                
        return symbols


def demo_conversion():
    """変換デモ"""
    logging.basicConfig(level=logging.DEBUG,
                       format='%(levelname)s: %(message)s')
    
    converter = RawSymbolConverter()
    
    print("=" * 60)
    print("生データシンボル → PKG ID変換デモ")
    print("=" * 60)
    
    # 個別変換テスト
    test_symbols = [
        "AA001",  # Os乖離
        "CA012",  # 平均足ベース
        "SA001",  # 階層1
        "BB100",  # Os基準
    ]
    
    print("\n個別シンボル変換:")
    for symbol in test_symbols:
        raw_sym = converter.parse_symbol(symbol)
        if raw_sym:
            print(f"  {symbol:6} → {raw_sym.to_pkg_id():15} ({TIMEFRAMES[raw_sym.timeframe]})")
    
    # KAIRI文字列からの抽出
    kairi_examples = [
        "CA011_CA038_CA048_CA058",
        "CA117_CA124_CA131_CA138",
        "AA001,AA002,AA003"
    ]
    
    print("\nKAIRI文字列からの抽出:")
    for kairi in kairi_examples:
        symbols = converter.extract_from_kairi_string(kairi)
        print(f"  {kairi}")
        print(f"    → 抽出: {symbols}")
        
        # PKG ID変換
        pkg_ids = converter.convert_batch(symbols)
        for sym, pkg_id in pkg_ids.items():
            print(f"      {sym} → {pkg_id}")
    
    # 一括変換テスト
    print("\n一括変換（異なる時間足）:")
    batch_symbols = ["AA001", "AA002", "BA001", "CA001"]
    
    # 1分足として変換
    m1_results = converter.convert_batch(batch_symbols, default_timeframe=1)
    print("  1分足:")
    for sym, pkg_id in m1_results.items():
        print(f"    {sym} → {pkg_id}")
    
    # 15分足として変換
    m15_results = converter.convert_batch(batch_symbols, default_timeframe=3)
    print("  15分足:")
    for sym, pkg_id in m15_results.items():
        print(f"    {sym} → {pkg_id}")
    
    print("\n✅ 変換完了")


if __name__ == "__main__":
    demo_conversion()