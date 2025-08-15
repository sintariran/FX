#!/usr/bin/env python3
"""
xlsmファイルからVBAコードを抽出
oletoolsを使用してPKG計算モジュールの実装を取得
"""

import os
import sys
from oletools.olevba import VBA_Parser

def extract_vba_from_xlsm(xlsm_path, output_dir=None):
    """
    xlsmファイルからVBAコードを抽出
    
    Args:
        xlsm_path: xlsmファイルのパス
        output_dir: 出力ディレクトリ（Noneの場合はコンソール出力）
    """
    if not os.path.exists(xlsm_path):
        print(f"ファイルが見つかりません: {xlsm_path}")
        return
    
    print(f"VBAコード抽出: {xlsm_path}")
    print("=" * 60)
    
    try:
        # VBAパーサーを初期化
        vbaparser = VBA_Parser(xlsm_path)
        
        # すべてのVBAモジュールを抽出
        vba_modules = vbaparser.extract_all_macros()
        
        if not vba_modules:
            print("VBAマクロが見つかりませんでした")
            return
        
        module_count = 0
        function_list = []
        
        for filename, stream_path, vba_filename, vba_code in vba_modules:
            module_count += 1
            
            # モジュール情報を表示
            print(f"\n📄 モジュール {module_count}: {vba_filename}")
            print(f"   ストリーム: {stream_path}")
            print(f"   サイズ: {len(vba_code)} bytes")
            
            # 関数名を抽出
            lines = vba_code.split('\n')
            for line in lines:
                line_upper = line.upper().strip()
                if line_upper.startswith('FUNCTION ') or line_upper.startswith('SUB ') or \
                   'FUNCTION ' in line_upper or 'SUB ' in line_upper:
                    try:
                        # Private/Publicを除去
                        clean_line = line.strip()
                        if 'FUNCTION' in clean_line.upper():
                            parts = clean_line.upper().split('FUNCTION')
                            if len(parts) > 1:
                                func_name = parts[1].split('(')[0].strip()
                            else:
                                continue
                        elif 'SUB' in clean_line.upper():
                            parts = clean_line.upper().split('SUB')
                            if len(parts) > 1:
                                func_name = parts[1].split('(')[0].strip()
                            else:
                                continue
                        else:
                            continue
                        
                        if func_name and not func_name.startswith('_'):
                            function_list.append((vba_filename, func_name))
                            print(f"   🔧 {func_name}")
                    except Exception as e:
                        pass  # 個々のエラーは無視
            
            # 出力ディレクトリが指定されている場合はファイルに保存
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
                output_path = os.path.join(output_dir, f"{vba_filename}.bas")
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(vba_code)
                print(f"   💾 保存: {output_path}")
        
        # サマリー
        print("\n" + "=" * 60)
        print(f"📊 抽出結果サマリー:")
        print(f"   モジュール数: {module_count}")
        print(f"   関数/サブルーチン数: {len(function_list)}")
        
        # 関数タイプ別に分類
        pkg_functions = [f for _, f in function_list if any(
            keyword in f.upper() for keyword in 
            ['RATIO', 'HEOSUD', 'OSUM', 'PREDICT', 'LEADER', 'SABUN', 'JISSEI']
        )]
        
        if pkg_functions:
            print(f"\n🎯 PKG関連の関数:")
            for func in sorted(set(pkg_functions)):
                print(f"   - {func}")
        
        # クローズ
        vbaparser.close()
        
    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()

def main():
    """メイン処理"""
    
    # 対象のxlsmファイル
    xlsm_files = [
        "/Users/ksato/Documents/GitHub/AI-Wolf/FX/取得データ/PKG配置_エクセル作成分登録用.xlsm",
        "/Users/ksato/Documents/GitHub/AI-Wolf/FX/取得データ/all/bat/test.xlsm",
        "/Users/ksato/Documents/GitHub/AI-Wolf/FX/取得データ/取引用信号分岐.xlsm"
    ]
    
    # 出力ディレクトリ
    output_base = "/Users/ksato/Documents/GitHub/AI-Wolf/FX/src/pkg/extracted_vba"
    
    for xlsm_file in xlsm_files:
        if os.path.exists(xlsm_file):
            # ファイル名から出力ディレクトリを作成
            file_base = os.path.splitext(os.path.basename(xlsm_file))[0]
            output_dir = os.path.join(output_base, file_base)
            
            print(f"\n{'='*60}")
            print(f"処理中: {os.path.basename(xlsm_file)}")
            print(f"{'='*60}")
            
            extract_vba_from_xlsm(xlsm_file, output_dir)

if __name__ == "__main__":
    main()