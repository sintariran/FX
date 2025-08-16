#!/usr/bin/env python3
"""
initial_setting_list_os.xlsxからPKG定義を抽出してDAGグラフを構築
加工コードシートから実際のPKG関数定義を読み取り、DAGエンジンに登録
"""

import os
import sys
import zipfile
import xml.etree.ElementTree as ET
from collections import defaultdict, OrderedDict
import re
import logging
from typing import Dict, List, Tuple, Optional, Set

# 既存モジュールのインポート
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from dag_engine_v2 import DAGEngine
from raw_symbol_to_pkg import RawSymbolConverter

class ExcelPKGExtractor:
    """ExcelファイルからPKG定義を抽出"""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.logger = logging.getLogger(__name__)
        self.shared_strings = {}
        self.pkg_definitions = []
        self.raw_symbols = set()
        
    def extract_shared_strings(self, xlsx):
        """共有文字列を抽出"""
        if 'xl/sharedStrings.xml' not in xlsx.namelist():
            return {}
        
        strings_xml = xlsx.read('xl/sharedStrings.xml')
        root = ET.fromstring(strings_xml)
        
        ns = {'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        string_items = root.findall('.//main:si', ns)
        
        string_map = {}
        for i, si in enumerate(string_items):
            t_elem = si.find('.//main:t', ns)
            if t_elem is not None:
                string_map[str(i)] = t_elem.text if t_elem.text else ""
        
        return string_map
    
    def parse_cell_value(self, cell, string_map):
        """セルの値を解析"""
        ns = {'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        
        cell_type = cell.get('t', 'n')
        v_elem = cell.find('main:v', ns)
        
        if v_elem is None:
            return None
        
        value = v_elem.text
        
        if cell_type == 's':  # 文字列
            return string_map.get(value, value)
        elif cell_type == 'b':  # ブール
            return value == '1'
        else:  # 数値
            try:
                if '.' in value:
                    return float(value)
                else:
                    return int(value)
            except:
                return value
    
    def extract_kaiko_code_sheet(self, xlsx):
        """加工コードシートからPKG定義を抽出"""
        # sheet2.xml = 加工コードシート
        sheet_path = 'xl/worksheets/sheet2.xml'
        
        if sheet_path not in xlsx.namelist():
            self.logger.warning(f"シートが見つかりません: {sheet_path}")
            return
        
        sheet_xml = xlsx.read(sheet_path)
        root = ET.fromstring(sheet_xml)
        
        ns = {'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        rows = root.findall('.//main:row', ns)
        
        # ヘッダー行をスキップして、データ行を処理
        for row_idx, row in enumerate(rows[1:], start=2):
            cells = row.findall('main:c', ns)
            if len(cells) < 10:
                continue
                
            row_data = []
            for cell in cells[:15]:  # 必要な列だけ取得
                value = self.parse_cell_value(cell, self.shared_strings)
                row_data.append(value)
            
            # 有効なデータ行をパース
            if len(row_data) >= 10 and row_data[1]:  # NAME1が存在
                self.process_kaiko_row(row_data)
    
    def process_kaiko_row(self, row_data):
        """加工コード行を処理してPKG定義を作成"""
        # カラム定義（Excelシートの構造に基づく）
        # 0: No., 1: NAME1, 2: NAME2, 3: ASI1, 4: ASI2, 5: Price
        # 6: TYPE, 7: THRESHOLD, 8: NUMBER, 9: KAIRI, 10: CODE
        
        name1 = row_data[1] if row_data[1] else None
        name2 = row_data[2] if row_data[2] else None
        asi1 = row_data[3] if row_data[3] else 3  # デフォルト15分足
        asi2 = row_data[4] if row_data[4] else None
        price = row_data[5] if row_data[5] else 1
        func_type = row_data[6] if row_data[6] else None
        threshold = row_data[7] if row_data[7] else None
        number = row_data[8] if row_data[8] else None
        kairi = row_data[9] if row_data[9] else None
        
        if not name1 or not func_type:
            return
        
        # 生データシンボルを収集
        if isinstance(name1, str) and re.match(r'^[A-Z]{2}\d{1,3}$', name1):
            self.raw_symbols.add(name1)
        
        # KAIRI列からシンボルを抽出
        if kairi and isinstance(kairi, str):
            kairi_symbols = self.extract_symbols_from_kairi(kairi)
            self.raw_symbols.update(kairi_symbols)
            
            # PKG定義を作成
            pkg_def = {
                'name': name1,
                'function_type': func_type,
                'input_symbols': kairi_symbols,
                'timeframe': asi1,
                'threshold': threshold,
                'group_number': number
            }
            self.pkg_definitions.append(pkg_def)
            
            self.logger.debug(f"PKG定義: {name1} = {func_type}({kairi_symbols})")
    
    def extract_symbols_from_kairi(self, kairi_str: str) -> List[str]:
        """KAIRI文字列からシンボルを抽出"""
        symbols = []
        
        # アンダースコア区切りまたはカンマ区切り
        parts = re.split(r'[_,\s]+', kairi_str)
        
        for part in parts:
            # シンボルパターンにマッチ
            if re.match(r'^[A-Z]{2}\d{1,3}$', part):
                symbols.append(part)
        
        return symbols
    
    def extract_all(self):
        """すべての情報を抽出"""
        with zipfile.ZipFile(self.filepath, 'r') as xlsx:
            # 共有文字列を読み込み
            self.shared_strings = self.extract_shared_strings(xlsx)
            
            # 加工コードシートを解析
            self.extract_kaiko_code_sheet(xlsx)
            
        return self.pkg_definitions, self.raw_symbols


class PKGGraphBuilder:
    """PKG定義からDAGグラフを構築"""
    
    def __init__(self):
        self.dag_engine = DAGEngine()
        self.symbol_converter = RawSymbolConverter()
        self.logger = logging.getLogger(__name__)
        self.registered_symbols = set()
        self.registered_pkgs = set()
        
    def build_from_definitions(self, pkg_definitions: List[Dict], 
                             raw_symbols: Set[str],
                             default_timeframe: int = 3,
                             default_currency: int = 1):
        """PKG定義からDAGグラフを構築"""
        
        # Step 1: 生データシンボルを登録
        self.logger.info(f"生データシンボル登録: {len(raw_symbols)}個")
        for symbol in raw_symbols:
            self.register_raw_symbol(symbol, default_timeframe, default_currency)
        
        # Step 2: PKG関数を階層順に登録
        self.logger.info(f"PKG関数登録: {len(pkg_definitions)}個")
        
        # 階層を推定（入力数が少ないものから）
        sorted_defs = sorted(pkg_definitions, 
                           key=lambda x: len(x.get('input_symbols', [])))
        
        for pkg_def in sorted_defs:
            self.register_pkg_function(pkg_def, default_currency)
        
        return self.dag_engine
    
    def register_raw_symbol(self, symbol: str, timeframe: int, currency: int):
        """生データシンボルをDAGに登録"""
        if symbol in self.registered_symbols:
            return
            
        # デフォルト値（実際のデータがない場合）
        default_value = 100.0
        
        # PKG ID形式で登録
        self.dag_engine.register_raw_data(
            symbol=symbol,
            timeframe=timeframe,
            period=9,  # 共通
            currency=currency,
            value=default_value
        )
        
        self.registered_symbols.add(symbol)
        self.logger.debug(f"生データ登録: {symbol} → {timeframe}9{currency}^0-{symbol}")
    
    def register_pkg_function(self, pkg_def: Dict, currency: int):
        """PKG関数をDAGに登録"""
        name = pkg_def['name']
        func_type = pkg_def['function_type']
        input_symbols = pkg_def.get('input_symbols', [])
        timeframe = pkg_def.get('timeframe', 3)
        
        if not input_symbols:
            self.logger.warning(f"入力シンボルなし: {name}")
            return
        
        # PKG IDを生成（階層を推定）
        layer = self.estimate_layer(name)
        sequence = self.extract_sequence(name)
        pkg_id = f"{timeframe}9{currency}^{layer}-{sequence}"
        
        # 入力参照をPKG ID形式に変換
        input_refs = []
        for inp_symbol in input_symbols:
            if inp_symbol in self.registered_symbols:
                # 生データシンボル
                input_refs.append(f"{timeframe}9{currency}^0-{inp_symbol}")
            elif inp_symbol in self.registered_pkgs:
                # 他のPKG関数（簡略化のため同じ階層と仮定）
                inp_layer = self.estimate_layer(inp_symbol)
                inp_seq = self.extract_sequence(inp_symbol)
                input_refs.append(f"{timeframe}9{currency}^{inp_layer}-{inp_seq}")
        
        if not input_refs:
            self.logger.warning(f"有効な入力参照なし: {name}")
            return
        
        # 関数タイプをマッピング
        mapped_func_type = self.map_function_type(func_type)
        
        # DAGエンジンに登録
        self.dag_engine.register_function(
            pkg_id=pkg_id,
            function_type=mapped_func_type,
            input_refs=input_refs
        )
        
        self.registered_pkgs.add(name)
        self.logger.debug(f"PKG関数登録: {pkg_id} = {mapped_func_type}({input_refs[:2]}...)")
    
    def estimate_layer(self, name: str) -> int:
        """シンボル名から階層を推定"""
        # SAxx = Layer 1, SBxx = Layer 2, etc.
        if name.startswith('SA'):
            return 1
        elif name.startswith('SB'):
            return 2
        elif name.startswith('SC'):
            return 3
        elif name.startswith('SD'):
            return 4
        elif name.startswith('SE'):
            return 5
        elif name.startswith('SF'):
            return 6
        else:
            # CAxx, AAxx等は生データ扱い
            return 0
    
    def extract_sequence(self, name: str) -> str:
        """シンボル名から連番を抽出"""
        match = re.search(r'\d+', name)
        if match:
            return match.group()
        return name
    
    def map_function_type(self, excel_type: str) -> str:
        """Excel関数タイプをPKG関数タイプにマッピング"""
        type_map = {
            'Ratio': 'Z',      # 比率計算
            'AbsIchi': 'Z',    # 絶対値距離
            'Jita': 'SL',      # 自通貨他通貨選択
            'SELECT': 'SL',    # 選択
            'COUNT': 'CO',     # カウント
            'ROUND': 'RO',     # 丸め
            'MINUTE': 'MN',    # 分取得
        }
        
        return type_map.get(excel_type, 'Z')  # デフォルトはZ関数


def main():
    """メイン処理"""
    logging.basicConfig(level=logging.INFO,
                       format='%(levelname)s: %(message)s')
    
    filepath = "/Users/ksato/Documents/GitHub/AI-Wolf/FX/initial_setting_list_os.xlsx"
    
    if not os.path.exists(filepath):
        print(f"ファイルが見つかりません: {filepath}")
        return
    
    print("=" * 60)
    print("PKGグラフ構築 - initial_setting_list_os.xlsx")
    print("=" * 60)
    
    # Step 1: Excelから定義を抽出
    print("\n📊 Excel解析中...")
    extractor = ExcelPKGExtractor(filepath)
    pkg_definitions, raw_symbols = extractor.extract_all()
    
    print(f"  抽出完了:")
    print(f"    生データシンボル: {len(raw_symbols)}個")
    print(f"    PKG定義: {len(pkg_definitions)}個")
    
    # サンプル表示
    if raw_symbols:
        print(f"    生データ例: {list(raw_symbols)[:5]}")
    if pkg_definitions:
        print(f"    PKG定義例: {pkg_definitions[0] if pkg_definitions else 'なし'}")
    
    # Step 2: DAGグラフを構築
    print("\n🔧 DAGグラフ構築中...")
    builder = PKGGraphBuilder()
    dag_engine = builder.build_from_definitions(pkg_definitions, raw_symbols)
    
    # Step 3: グラフ構造を表示
    print("\n📈 DAGグラフ構造:")
    print(dag_engine.visualize_graph())
    
    # Step 4: サンプル評価（最初の5個のPKG）
    if builder.registered_pkgs:
        print("\n🎯 サンプル評価:")
        sample_pkgs = list(builder.registered_pkgs)[:3]
        
        for pkg_name in sample_pkgs:
            layer = builder.estimate_layer(pkg_name)
            seq = builder.extract_sequence(pkg_name)
            pkg_id = f"391^{layer}-{seq}"
            
            try:
                results = dag_engine.evaluate([pkg_id])
                if pkg_id in results:
                    print(f"  {pkg_name} ({pkg_id}) = {results[pkg_id]}")
            except Exception as e:
                print(f"  {pkg_name}: 評価エラー - {e}")
    
    print("\n✅ グラフ構築完了")


if __name__ == "__main__":
    main()