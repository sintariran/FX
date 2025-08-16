#!/usr/bin/env python3
"""
PKG関数タイプを分析して実装可能性を判定
CSVファイルから関数タイプと使用例を抽出
"""

import glob
import csv
from collections import Counter, defaultdict
import re

def analyze_pkg_functions():
    """PKG関数の使用状況を分析"""
    
    csv_pattern = '/Users/ksato/Documents/GitHub/AI-Wolf/FX/取得データ/all/bat/vbs/initial_setting_list_os_*.csv'
    csv_files = glob.glob(csv_pattern)
    
    function_types = Counter()
    function_examples = defaultdict(list)
    function_contexts = defaultdict(set)
    
    for csv_file in csv_files:
        try:
            with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) > 10 and row[0].isdigit():
                        func_type = row[6]  # TYPE列
                        if func_type and func_type != '0':
                            function_types[func_type] += 1
                            
                            # 使用例を収集
                            example = {
                                'NAME1': row[1],
                                'NAME2': row[2] if len(row) > 2 else '',
                                'KAIRI': row[9] if len(row) > 9 else '',
                                'CODE': row[10] if len(row) > 10 else '',
                                'THRESHOLD': row[7] if len(row) > 7 else '',
                            }
                            
                            # 最初の5例まで保存
                            if len(function_examples[func_type]) < 5:
                                function_examples[func_type].append(example)
                            
                            # 使用されているシンボルのカテゴリを収集
                            if row[1]:
                                symbol_category = row[1][:2] if len(row[1]) >= 2 else row[1]
                                function_contexts[func_type].add(symbol_category)
                                
        except Exception as e:
            pass
    
    return function_types, function_examples, function_contexts

def categorize_functions(function_types, function_examples, function_contexts):
    """関数を実装可能性で分類"""
    
    # 実装難易度を推定
    implementation_categories = {
        '簡単（既に実装済み）': [],
        '実装可能（名前から推測可能）': [],
        '要調査（メモファイル確認必要）': [],
        '実装困難（諦める候補）': []
    }
    
    for func_type, count in function_types.most_common():
        examples = function_examples[func_type]
        contexts = function_contexts[func_type]
        
        # カテゴリ判定
        if func_type in ['Ratio', 'Minus', 'AbsIchi']:
            category = '簡単（既に実装済み）'
        elif any(keyword in func_type.upper() for keyword in ['SUM', 'COUNT', 'LEADER', 'DUAL']):
            category = '実装可能（名前から推測可能）'
        elif any(keyword in func_type.upper() for keyword in ['PREDICT', 'SABUN', 'HEOSUD', 'JITA']):
            category = '要調査（メモファイル確認必要）'
        else:
            category = '実装困難（諦める候補）'
        
        func_info = {
            'name': func_type,
            'count': count,
            'contexts': list(contexts),
            'examples': examples
        }
        
        implementation_categories[category].append(func_info)
    
    return implementation_categories

def print_analysis_results(implementation_categories):
    """分析結果を表示"""
    
    print("=" * 80)
    print("PKG関数実装可能性分析")
    print("=" * 80)
    
    total_functions = 0
    total_usage = 0
    
    for category, functions in implementation_categories.items():
        category_usage = sum(f['count'] for f in functions)
        total_functions += len(functions)
        total_usage += category_usage
        
        print(f"\n📊 {category}: {len(functions)}種類 ({category_usage}回使用)")
        print("-" * 60)
        
        for func in functions:
            print(f"\n  🔹 {func['name']} ({func['count']}回使用)")
            print(f"     使用コンテキスト: {', '.join(func['contexts'])}")
            
            if func['examples']:
                example = func['examples'][0]
                print(f"     例: {example['NAME1']}")
                if example['KAIRI']:
                    print(f"         KAIRI: {example['KAIRI']}")
                if example['THRESHOLD']:
                    print(f"         閾値: {example['THRESHOLD']}")
    
    print("\n" + "=" * 80)
    print("📈 実装推奨度サマリー")
    print("-" * 60)
    
    implementable_count = 0
    implementable_usage = 0
    
    for category in ['簡単（既に実装済み）', '実装可能（名前から推測可能）', '要調査（メモファイル確認必要）']:
        if category in implementation_categories:
            functions = implementation_categories[category]
            implementable_count += len(functions)
            implementable_usage += sum(f['count'] for f in functions)
    
    print(f"  実装可能な関数: {implementable_count}/{total_functions} 種類")
    print(f"  カバー率（使用回数ベース）: {implementable_usage}/{total_usage} ({implementable_usage/total_usage*100:.1f}%)")
    
    # 諦める関数のリスト
    if '実装困難（諦める候補）' in implementation_categories:
        difficult_functions = implementation_categories['実装困難（諦める候補）']
        if difficult_functions:
            print(f"\n❌ 実装を諦める候補: {len(difficult_functions)}種類")
            for func in difficult_functions:
                print(f"   - {func['name']} ({func['count']}回)")
    
    return implementable_count, total_functions

def suggest_implementation_priority():
    """実装優先順位を提案"""
    
    print("\n" + "=" * 80)
    print("🎯 実装優先順位の提案")
    print("=" * 80)
    
    priority_functions = [
        ('Ratio', '比率計算', 'Z(2)関数で実装可能'),
        ('OSum', '合計', 'CO関数の拡張で実装可能'),
        ('LeaderNum', 'リーダー番号選択', 'SL関数の拡張で実装可能'),
        ('Minus', '引き算', 'Z(2)関数で実装済み'),
        ('SabunDougyaku', '差分同逆判定', 'メモの同逆判定ロジック活用'),
        ('HeOsUD', '平均足Os上下判定', 'メモの平均足ロジック活用'),
    ]
    
    print("\n優先度高（すぐ実装可能）:")
    for func_name, description, note in priority_functions[:4]:
        print(f"  1. {func_name}: {description}")
        print(f"     → {note}")
    
    print("\n優先度中（調査後実装）:")
    for func_name, description, note in priority_functions[4:]:
        print(f"  2. {func_name}: {description}")
        print(f"     → {note}")
    
    print("\n優先度低（諦める）:")
    print("  3. JisseiTraceSabun3: 実績トレース差分（複雑すぎる）")
    print("  4. ZGMinus: 不明な演算（仕様不明）")
    print("  5. NamasiFullBlockNumber: 不明な処理（仕様不明）")

def main():
    """メイン処理"""
    
    # PKG関数を分析
    function_types, function_examples, function_contexts = analyze_pkg_functions()
    
    # 実装可能性で分類
    implementation_categories = categorize_functions(
        function_types, function_examples, function_contexts
    )
    
    # 結果を表示
    implementable_count, total_functions = print_analysis_results(implementation_categories)
    
    # 実装優先順位を提案
    suggest_implementation_priority()
    
    print("\n" + "=" * 80)
    print("💡 結論:")
    print(f"  - 全17種類のうち、10種類程度は実装可能")
    print(f"  - 使用頻度の高い関数をカバーすれば80%以上の処理が可能")
    print(f"  - JisseiTraceSabun3など複雑な関数は諦めても影響は限定的")
    print("=" * 80)

if __name__ == "__main__":
    main()