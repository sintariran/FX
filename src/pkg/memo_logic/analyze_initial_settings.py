#!/usr/bin/env python3
"""
initial_setting_list_os.xlsxの構造解析
PKG定義の抽出と理解
"""

import os
import sys
import csv
import zipfile
import xml.etree.ElementTree as ET
from collections import defaultdict

def analyze_excel_structure():
    """
    Excelファイルの構造を解析（pandas不要版）
    .xlsxはzip形式なので、直接XMLを読む
    """
    
    filepath = "/Users/ksato/Documents/GitHub/AI-Wolf/FX/initial_setting_list_os.xlsx"
    
    if not os.path.exists(filepath):
        print(f"ファイルが見つかりません: {filepath}")
        return
    
    print("=" * 60)
    print("initial_setting_list_os.xlsx 構造解析")
    print("=" * 60)
    
    # xlsxファイルはzipアーカイブ
    with zipfile.ZipFile(filepath, 'r') as xlsx:
        # ファイル構造を確認
        file_list = xlsx.namelist()
        
        print("\n📁 Excelファイル内部構造:")
        sheets = [f for f in file_list if f.startswith('xl/worksheets/')]
        for sheet in sheets:
            print(f"  - {sheet}")
        
        # workbook.xmlから シート名を取得
        if 'xl/workbook.xml' in file_list:
            workbook_xml = xlsx.read('xl/workbook.xml')
            root = ET.fromstring(workbook_xml)
            
            print("\n📊 シート一覧:")
            # XMLネームスペースの処理
            ns = {'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
            sheets_elem = root.find('.//main:sheets', ns)
            
            if sheets_elem is not None:
                sheet_info = []
                for sheet in sheets_elem.findall('main:sheet', ns):
                    name = sheet.get('name')
                    sheet_id = sheet.get('sheetId')
                    sheet_info.append((sheet_id, name))
                    print(f"  Sheet {sheet_id}: {name}")
                
                # 最初のシートのデータをサンプル表示
                if sheets and sheet_info:
                    print(f"\n📝 最初のシート '{sheet_info[0][1]}' のサンプルデータ:")
                    sheet1_path = 'xl/worksheets/sheet1.xml'
                    if sheet1_path in file_list:
                        analyze_sheet_data(xlsx, sheet1_path)
        
        # sharedStrings.xmlから文字列データを取得
        if 'xl/sharedStrings.xml' in file_list:
            strings_xml = xlsx.read('xl/sharedStrings.xml')
            strings_root = ET.fromstring(strings_xml)
            
            ns = {'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
            string_items = strings_root.findall('.//main:si', ns)
            
            print(f"\n📄 文字列データ数: {len(string_items)}")
            
            # 最初の20個の文字列を表示（PKG定義のヒントを探る）
            print("\n最初の20個の文字列データ:")
            for i, si in enumerate(string_items[:20]):
                t_elem = si.find('.//main:t', ns)
                if t_elem is not None and t_elem.text:
                    print(f"  [{i}]: {t_elem.text}")

def analyze_sheet_data(xlsx, sheet_path):
    """シートデータの構造を解析"""
    sheet_xml = xlsx.read(sheet_path)
    root = ET.fromstring(sheet_xml)
    
    ns = {'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    
    # 行データを取得
    rows = root.findall('.//main:row', ns)
    print(f"  総行数: {len(rows)}")
    
    if rows:
        # 最初の数行を解析
        print("\n  最初の5行のセル構造:")
        for i, row in enumerate(rows[:5]):
            row_num = row.get('r', '?')
            cells = row.findall('main:c', ns)
            cell_refs = []
            for cell in cells:
                cell_ref = cell.get('r', '?')  # セル参照（A1, B1など）
                cell_type = cell.get('t', 'n')  # タイプ（s=文字列, n=数値）
                v_elem = cell.find('main:v', ns)
                value = v_elem.text if v_elem is not None else 'empty'
                
                # タイプに応じた表示
                if cell_type == 's':
                    cell_refs.append(f"{cell_ref}(str:{value})")
                else:
                    cell_refs.append(f"{cell_ref}({value})")
            
            print(f"    Row {row_num}: {', '.join(cell_refs[:10])}")  # 最初の10列まで
    
    # 列の範囲を確認
    all_cells = root.findall('.//main:c', ns)
    if all_cells:
        cell_refs = [cell.get('r', '') for cell in all_cells if cell.get('r')]
        if cell_refs:
            # 列の範囲を特定
            import re
            columns = set()
            for ref in cell_refs:
                match = re.match(r'([A-Z]+)\d+', ref)
                if match:
                    columns.add(match.group(1))
            
            sorted_cols = sorted(columns)
            print(f"\n  使用列範囲: {sorted_cols[0]} 〜 {sorted_cols[-1]} ({len(sorted_cols)}列)")
            
            # どんな列があるか
            print(f"  列リスト（最初の20列）: {sorted_cols[:20]}")

if __name__ == "__main__":
    analyze_excel_structure()