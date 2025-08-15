# FX取引システム 開発ロードマップ
## ローカル構築からロジック改善まで

## 📋 概要

メモファイルに記載されているオペレーションロジック（取引判断の本質）を正しく理解・実装し、それをベースに段階的に取引精度を改善していくための実践的ロードマップです。

## 🎯 最終目標

**「メモ記載のオペレーションロジックを正しく実装し、バックテストで取引精度を改善できる環境」**

## 📅 開発フェーズ

### Phase 1: ローカル環境構築（Week 1-2）

#### Week 1: 基盤準備
```yaml
目標: 開発環境整備とデータ準備

タスク:
  day1-2:
    - Python開発環境構築（poetry, pandas, numpy）
    - 既存CSVデータの分析・整理
    - メモファイルからPKG関数仕様の抽出
    
  day3-4:
    - メモファイル徹底分析（オペレーションロジック抽出）
    - 取引判断のコアロジック整理
    - OANDAデモ口座開設・API接続テスト
    
  day5-7:
    - SQLiteローカルDB構築
    - ヒストリカルデータ取り込み
    - メモ記載の指標定義（平均足、OsMA、レンジ等）

成果物:
  - requirements.txt / pyproject.toml
  - data/historical/ （ヒストリカルデータ）
  - docs/operation_logic_analysis.md （メモ分析結果）
  - scripts/oanda_client.py
```

#### Week 2: オペレーションロジック実装
```yaml
目標: メモ記載の取引判断ロジックを実装

タスク:
  day8-10:
    - 基本指標実装（平均足、OsMA、レンジ判定）
    - 「同逆」「行帰」の概念実装
    - エントリー/エグジット基本条件
    
  day11-12:
    - 時間足連携ロジック（1M, 5M, 15M, 30M）
    - 「前足」「今足」「先足」の状態管理
    - 「もみ」「オーバーシュート」判定
    
  day13-14:
    - 簡単なバックテストフレームワーク
    - オペレーションロジックの動作確認
    - ログ出力と結果検証

成果物:
  - src/operation_logic.py （メモベースロジック）
  - src/indicators.py
  - src/backtest_engine.py
  - tests/test_operation_logic.py
```

### Phase 2: 実データ検証（Week 3-4）

#### Week 3: メモベース取引ルール実装
```yaml
目標: メモ記載の取引判断を完全に理解・実装

タスク:
  day15-17:
    - 詳細エントリー条件実装
      - 「10の上/下で方向合致」
      - 「前足の平均足が陰線になっていなければエントリーしない」
      - 「先足が返してきていない状態で前足まで逆方向転換したら決済」
    
  day18-19:
    - 複雑なエグジット条件
      - 「平均足/OPFFが転換している場合の決済ルール」
      - 「1分の揃いと前足以前のOPFFの揃い」
      - レンジ抜け判定（足レンジ、価格レンジ）
    
  day20-21:
    - 時間結合ロジック
      - 「他時間足の動きを用いてオーバーシュート判断」
      - 「どの時刻のどの時間足を見るかを特定」
      - 周期の揃い・方向揃い判定

成果物:
  - src/trading_rules.py（メモベース）
  - src/timeframe_coordination.py
  - tests/memo_logic_validation.py
  - reports/operation_logic_implementation.md
```

#### Week 4: オペレーションロジック分析
```yaml
目標: 実装したロジックの有効性と問題点を分析

タスク:
  day22-24:
    - メモ記載のパフォーマンス目標との比較
      - 「全体19ms」「もみ77ms」等の処理時間
      - 想定されていた取引精度
    - 2020-2024年フルバックテスト実行
    
  day25-26:
    - オペレーション条件別の成績分析
      - 「同逆」条件のヒット率・成功率
      - 「もみ」「オーバーシュート」の判定精度
      - 時間足連携の有効性測定
    
  day27-28:
    - メモで言及されている問題点の検証
      - 「乖離/確認ポイント」の効果
      - 「加速ポイントの導出（OP）」の実装
      - ダッシュボード作成（Streamlit）

成果物:
  - analysis/operation_performance.py
  - reports/memo_vs_implementation.md
  - dashboard/operation_dashboard.py
  - docs/logic_improvement_candidates.md
```

### Phase 3: ロジック改善実装（Week 5-6）

#### Week 5: 改善実験
```yaml
目標: 特定した問題点の改善案を実装・テスト

タスク:
  day29-31:
    - 誤シグナル削減ロジック実装
    - 新しいPKG関数の追加
    - パラメータ最適化実装
    
  day32-33:
    - A/Bテストフレームワーク構築
    - 改善案vs既存ロジック比較
    - 統計的有意性検定
    
  day34-35:
    - 最適なパラメータセット決定
    - ウォークフォワード分析
    - アウトオブサンプルテスト

成果物:
  - src/improved_logic.py
  - src/optimization.py
  - src/ab_testing.py
  - reports/improvement_results.md
```

#### Week 6: 改善版完成
```yaml
目標: 改善されたロジックの完成と検証

タスク:
  day36-38:
    - 改善版オペレーションロジック完成
    - 全期間バックテスト実行
    - メモ記載の目標精度達成度確認
    
  day39-40:
    - ライブテスト環境構築
    - デモ口座での動作テスト
    - エラーハンドリング強化
    
  day41-42:
    - 最終レポート作成
    - 改善前後比較
    - 次フェーズ計画策定

成果物:
  - src/final_system.py
  - tests/integration_tests.py
  - reports/final_performance.md
  - docs/next_phase_plan.md
```

## 🛠 技術スタック

### 開発環境
```yaml
language: Python 3.11+
package_manager: Poetry
database: SQLite → PostgreSQL
visualization: matplotlib, plotly, streamlit
testing: pytest
linting: black, flake8, mypy

libraries:
  data: pandas, numpy, polars
  finance: yfinance, ta-lib, quantlib
  api: oandapyV20
  ml: scikit-learn (後期)
  web: fastapi, streamlit
```

### ディレクトリ構造
```
fx-trading-system/
├── src/
│   ├── pkg_system.py      # PKG関数システム
│   ├── indicators.py      # 技術指標計算
│   ├── trading_rules.py   # 取引ルール
│   ├── backtest_engine.py # バックテストエンジン
│   ├── risk_management.py # リスク管理
│   └── oanda_client.py    # OANDA API
├── data/
│   ├── historical/        # ヒストリカルデータ
│   ├── processed/         # 加工済みデータ
│   └── results/          # バックテスト結果
├── tests/
│   ├── test_pkg_system.py
│   ├── test_indicators.py
│   └── excel_comparison.py
├── analysis/
│   ├── performance_analysis.py
│   └── optimization.py
├── dashboard/
│   └── streamlit_dashboard.py
├── reports/
│   └── weekly_reports/
└── docs/
    └── api_documentation.md
```

## 📊 マイルストーン

### Week 2 完了時点
- [ ] PKG関数が動作している
- [ ] 簡単なバックテストが実行できる
- [ ] Excel結果と一致することを確認

### Week 4 完了時点
- [ ] 既存ロジックを完全に再現
- [ ] 現在のパフォーマンスを数値化
- [ ] 改善すべき点を特定

### Week 6 完了時点
- [ ] 改善されたロジックが動作
- [ ] 統計的に有意な改善を確認
- [ ] ライブテスト可能な状態

## 🎯 重要な検証ポイント

### 精度検証
```python
# メモ記載ロジック vs 実装 検証
def validate_operation_logic():
    """
    - 「同逆」「行帰」判定の正確性
    - エントリー/エグジット条件の実装正確性
    - 時間足連携ロジックの動作確認
    - メモ記載の想定成績との比較
    """
    pass

# パフォーマンス検証
def validate_performance():
    """
    - 勝率：現在値と比較
    - プロフィットファクター：改善度測定
    - 最大ドローダウン：リスク評価
    - シャープレシオ：リスク調整済みリターン
    """
    pass
```

### 改善効果測定
```python
metrics = {
    'win_rate': '勝率向上',
    'profit_factor': 'PF改善',
    'max_drawdown': 'DD削減',
    'sharpe_ratio': 'シャープレシオ向上',
    'calmar_ratio': 'カルマーレシオ向上'
}
```

## 📈 成功指標

### Phase 1 (Week 2)
- オペレーションロジック基本実装
- 基本バックテスト実行
- メモ記載条件の動作確認

### Phase 2 (Week 4)
- 完全なオペレーションロジック実装
- 4年間のバックテスト完了
- メモ vs 実装の差異明確化

### Phase 3 (Week 6)
- 統計的有意な改善（p < 0.05）
- シャープレシオ 10%以上向上
- 最大DD 20%以上削減

## 🚨 リスク対策

### 技術リスク
- **メモ理解不足**: 不明点は早期エスカレーション、段階的実装
- **データ品質問題**: 複数ソースでの検証
- **パフォーマンス劣化**: プロファイリング、最適化

### スケジュールリスク
- **遅延対応**: 毎週金曜に進捗確認、必要に応じて優先度調整
- **技術的ハードル**: 早期エスカレーション、代替案検討

## 🔄 次フェーズ予定

### Phase 4: Cloudflare移行 (Week 7-10)
- Workers実装
- D1/R2データ移行
- 本番環境構築

### Phase 5: AI統合 (Week 11-14)
- Claude API統合
- マルチタイムフレーム分析
- 動的戦略選択

---

**最終更新日**: 2025年1月  
**バージョン**: 1.1（オペレーションロジック重視版）  
**想定期間**: 6週間（42日）  
**必要スキル**: Python, pandas, 金融知識, メモ解読能力  