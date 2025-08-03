# FX取引システム ドキュメント

## 📚 ドキュメント構成

### 01-fundamentals/ - 基礎理論
- **core-concepts/** - 核となる概念
  - operation-definition.md - オペレーションとは何か
  - market-theory.md - 通貨間相対価値・市場理論
  - vs-traditional.md - 理論と一般との違い

- **analysis-methods/** - 分析手法
  - deviation-analysis.md - 乖離判断
  - prediction-logic.md - 予知ロジック
  - trend-flow.md - 価格による流れの判断

### 02-operation-logic/ - オペレーションロジック
- **basic-logic/** - 基本ロジック
  - operation-overview.md - オペレーションロジック整理・まとめ
  - judgment-sequence.md - 見る順番・判断フロー
  - detailed-view.md - 細かい見方

- **time-analysis/** - 時間分析
  - time-combination.md - 時間単体及び時間結合
  - period-cycles.md - 周期分析
  - situation-states.md - 状況状態の考え方・見る順番

- **aggregation/** - 集計手法
  - aggregation-methods.md - 集計の仕方
  - logic-verification.md - 論理の確認方法
  - evaluation-methods.md - ロジック評価

### 03-trading-system/ - 取引システム
- **trading-rules/** - 取引ルール
  - entry-exit-rules.md - 取引ルール
  - hedge-strategies.md - ヘッジ戦略
  - position-consideration.md - 取引の考え方・内容確認

- **market-conditions/** - 市場条件
  - range-trading.md - レンジの判定式
  - line-analysis.md - 線への到達率・行帰の見方
  - volatility-handling.md - もみ検討
  - sudden-moves.md - 突発対応

- **technical-indicators/** - テクニカル指標
  - parabolic-evaluation.md - パラボ評価
  - acceleration-coefficient.md - 加速度係数
  - top-filtering.md - トップ絞り込み

### 04-implementation/ - システム実装
- **mt4-system/** - MT4システム
  - mt4-programs.md - MT4取引プログラム
  - ea-development.md - EA開発・修正
  - operation-test.md - EA動作テスト

- **display-system/** - 表示器システム
  - display-specs.md - 表示器内容・仕様
  - comment-system.md - 表示器へのコメント

- **data-management/** - データ管理
  - configuration.md - 設定ファイル管理
  - package-management.md - パッケージ照合・階層数調整
  - data-requirements.md - データ洗い出し

### 05-operations/ - 運用・保守
- **daily-operations/** - 日次運用
  - work-procedures.md - 作業順番・進め方
  - system-checks.md - システムチェック
  - material-verification.md - 素材のチェック

- **monitoring/** - 監視
  - real-operation.md - リアル動作確認
  - economic-indicators.md - 経済指標発表時の流れ
  - classification.md - 区分切り分け

- **support/** - サポート
  - data-collection.md - データ収集（Java等）
  - collateral-management.md - 担保管理

### 06-miscellaneous/ - その他・雑記
- development-notes.md - 開発メモ・技術ノート
- operation-analysis-notes.md - オペレーション分析・実装ノート
- project-tasks-notes.md - プロジェクトタスク・作業メモ

---

## 🚀 クイックスタート

1. **基礎理論の理解**: `01-fundamentals/` から開始
2. **オペレーション習得**: `02-operation-logic/` で詳細学習
3. **取引実践**: `03-trading-system/` で実践的知識習得
4. **システム運用**: `04-implementation/` と `05-operations/` で運用知識習得

## 📝 メモファイルの対応

このドキュメント構造は、メモフォルダ内の97個のテキストファイルの内容を体系的に整理したものです。各マークダウンファイルには、対応する元メモファイルの内容が統合・整理されています。

### 📋 処理状況
- ✅ **全97ファイルの処理が完了しました！**
- 詳細な処理状況は `MEMO_PROCESSING_CHECKLIST.md` を参照してください