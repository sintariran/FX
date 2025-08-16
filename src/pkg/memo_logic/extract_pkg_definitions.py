#!/usr/bin/env python3
"""
initial_setting_list_os.xlsxからPKG定義を抽出
特に「階層構成」シートと「initial_setting_list_os_新」シートを解析
"""

import os
import sys
import zipfile
import xml.etree.ElementTree as ET
from collections import defaultdict
import re

def extract_shared_strings(xlsx):
    """共有文字列を抽出してインデックスマップを作成"""
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

def parse_cell_value(cell, string_map):
    """セルの値を解析"""
    ns = {'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    
    cell_type = cell.get('t', 'n')  # デフォルトは数値
    v_elem = cell.find('main:v', ns)
    
    if v_elem is None:
        return None
    
    value = v_elem.text
    
    if cell_type == 's':  # 文字列（共有文字列のインデックス）
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

def analyze_sheet(xlsx, sheet_path, string_map, sheet_name):
    """特定シートのデータを解析"""
    sheet_xml = xlsx.read(sheet_path)
    root = ET.fromstring(sheet_xml)
    
    ns = {'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    
    print(f"\n📊 シート: {sheet_name}")
    print("=" * 60)
    
    # すべての行を取得
    rows = root.findall('.//main:row', ns)
    
    # 最初の行（ヘッダー）を解析
    if rows:
        header_row = rows[0]
        headers = []
        cells = header_row.findall('main:c', ns)
        
        for cell in cells:
            value = parse_cell_value(cell, string_map)
            headers.append(value if value else "")
        
        print(f"ヘッダー（最初の20列）: {headers[:20]}")
        
        # データ行をサンプル表示（2-10行目）
        print("\nデータサンプル（2-10行目）:")
        for row_idx, row in enumerate(rows[1:10], start=2):
            cells = row.findall('main:c', ns)
            row_data = []
            
            for cell in cells[:10]:  # 最初の10列のみ
                value = parse_cell_value(cell, string_map)
                row_data.append(str(value) if value is not None else "")
            
            print(f"  Row {row_idx}: {row_data}")
        
        # PKG IDパターンを探す
        print("\nPKG IDパターン検索:")
        pkg_pattern = re.compile(r'\d{3,4}\^\d+-\w+')
        
        found_pkgs = []
        for row in rows[:100]:  # 最初の100行を検索
            cells = row.findall('main:c', ns)
            for cell in cells:
                value = parse_cell_value(cell, string_map)
                if value and isinstance(value, str):
                    if pkg_pattern.match(value):
                        found_pkgs.append(value)
                    elif 'AA' in value or 'BA' in value or 'CA' in value:
                        # 生データシンボルの可能性
                        if len(found_pkgs) < 10:
                            found_pkgs.append(f"Symbol: {value}")
        
        if found_pkgs:
            print(f"  見つかったPKG/シンボル（最初の10個）: {found_pkgs[:10]}")

def main():
    filepath = "/Users/ksato/Documents/GitHub/AI-Wolf/FX/initial_setting_list_os.xlsx"
    
    if not os.path.exists(filepath):
        print(f"ファイルが見つかりません: {filepath}")
        return
    
    print("=" * 60)
    print("PKG定義抽出 - initial_setting_list_os.xlsx")
    print("=" * 60)
    
    with zipfile.ZipFile(filepath, 'r') as xlsx:
        # 共有文字列を読み込み
        string_map = extract_shared_strings(xlsx)
        print(f"共有文字列数: {len(string_map)}")
        
        # 重要なシートを解析
        sheets_to_analyze = [
            ('xl/worksheets/sheet7.xml', 'initial_setting_list_os_新'),
            ('xl/worksheets/sheet4.xml', '階層構成'),
            ('xl/worksheets/sheet2.xml', '加工コード'),
            ('xl/worksheets/sheet5.xml', '最終出力')
        ]
        
        for sheet_path, sheet_name in sheets_to_analyze:
            if sheet_path in xlsx.namelist():
                analyze_sheet(xlsx, sheet_path, string_map, sheet_name)

if __name__ == "__main__":
    main()