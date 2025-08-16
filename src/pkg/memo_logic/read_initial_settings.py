#!/usr/bin/env python3
"""
初期設定リスト（initial_setting_list_os.xlsx）の読み込みテスト
生データシンボルとPKG定義の確認
"""

import os
import sys

def read_excel_basic():
    """Excelファイルの基本情報を表示（pandas不要版）"""
    
    filepath = "/Users/ksato/Documents/GitHub/AI-Wolf/FX/initial_setting_list_os.xlsx"
    
    if not os.path.exists(filepath):
        print(f"ファイルが見つかりません: {filepath}")
        return
    
    print(f"ファイル確認: {filepath}")
    print(f"ファイルサイズ: {os.path.getsize(filepath):,} bytes")
    
    # pandasがない場合は基本情報のみ
    print("\nExcelファイルの読み込みにはpandasとopenpyxlが必要です")
    print("内容を確認するには以下を実行してください:")
    print("pip install pandas openpyxl")
    
    # list.txtとの比較
    list_file = "./取得データ/all/bat/list.txt"
    if os.path.exists(list_file):
        with open(list_file, 'r') as f:
            symbols = f.read().strip().split('\n')
        print(f"\nlist.txt内のシンボル数: {len(symbols)}")
        print(f"最初の10個: {symbols[:10]}")
        
        # AAで始まるシンボルをカウント
        aa_symbols = [s for s in symbols if s.startswith('AA')]
        ba_symbols = [s for s in symbols if s.startswith('BA')]
        ca_symbols = [s for s in symbols if s.startswith('CA')]
        
        print(f"\nシンボル分類:")
        print(f"  AA系: {len(aa_symbols)}個")
        print(f"  BA系: {len(ba_symbols)}個")
        print(f"  CA系: {len(ca_symbols)}個")

if __name__ == "__main__":
    read_excel_basic()