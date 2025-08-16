# CLAUDE.md

**重要: このプロジェクトでは必ず日本語で応答してください。すべてのコミュニケーションは日本語で行います。**

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## システム概要

これは97個の日本語メモファイルに記載された独自のトレーディング手法を実装したFX（外国為替）取引システムです。関数型DAG（有向非巡回グラフ）アーキテクチャと階層的PKG（パッケージ）システムを使用して、マルチタイムフレームの取引信号を処理します。

## コアアーキテクチャ

### PKGシステム（関数型DAG）
関数型DAGアーキテクチャに基づく階層的ID体系：
- **ID形式**: `[時間足][周期][通貨]^[階層]-[連番]`
  - 例: `191^2-126` = 1分足(1), 周期なし(9), USDJPY(1), 第2階層(2), 126番
  - 時間足: 1=1分, 2=5分, 3=15分, 4=30分, 5=1時間, 6=4時間
  - 周期: 9=共通(周期なし), その他=TSML周期（10,15,30,45,60,90,180）
  - 通貨: 1=USDJPY, 2=EURUSD, 3=EURJPY

### 主要関数
- `Z(2)`, `Z(8)`: 算術演算
- `SL`, `OR`, `AND`: 選択・論理演算
- `CO`, `SG`, `AS`: 集計処理
- `MN`: 最小値選択
- 階層レベル: 1=基本指標, 2=演算結果, 3以降=統合判断

## メモファイルから抽出した核心概念

### 4つの主要オペレーション概念

1. **同逆判定（Dokyaku）**: 前々足乖離による方向判断
   - 勝率: 55.7%～56.1%
   - MHIH/MJIH、MMHMH/MMJMHの方向一致性評価

2. **行帰判定（Ikikaeri）**: 前足の動きから今足の方向予測
   - 行行：継続、行帰：一時的戻り、帰行：戻りから再進行、帰戻：完全転換
   - 平均足転換点と基準線による判定

3. **もみ・オーバーシュート判定**: レンジ相場とブレイクアウト検出
   - もみ判定：レンジ幅3pips未満
   - オーバーシュート：前足Os残足が今足換算で2以上

4. **時間結合**: マルチタイムフレーム統合
   - 1M, 5M, 15M, 30M, 1H, 4Hの並列処理
   - 内包関係による統合判断

## ドキュメント構造

### docs/フォルダの詳細構成

```
docs/
├── 00-project-planning/         # プロジェクト計画・アーキテクチャ
│   ├── development-roadmap.md   # 6週間の開発ロードマップ
│   ├── broker-api-comparison-2025.md  # ブローカーAPI比較
│   └── fx-architecture-2025-august.md # 最新アーキテクチャ設計
│
├── 01-fundamentals/             # 基礎理論（メモから抽出）
│   ├── core-concepts/           # 核となる概念
│   │   ├── operation-definition.md  # オペレーション定義
│   │   └── market-theory.md    # 通貨間相対価値理論
│   └── analysis-methods/        # 分析手法
│       ├── deviation-analysis.md    # 乖離判断
│       └── prediction-logic.md      # 予知ロジック
│
├── 02-operation-logic/          # オペレーションロジック（最重要）
│   ├── basic-logic/             # 基本ロジック
│   │   ├── operation-overview.md    # ロジック整理・まとめ
│   │   └── judgment-sequence.md     # 判断フロー
│   ├── time-analysis/           # 時間分析
│   │   └── time-combination.md      # 時間結合ロジック
│   ├── aggregation/             # 集計・評価
│   │   ├── backtest-logic-enhancement.md  # 80%予測精度達成方法
│   │   └── logic-verification.md    # 論理確認方法
│   ├── operation_logic_analysis.md  # メモ分析結果（核心概念）
│   └── trading_rules_extract.md     # 取引ルール詳細抽出
│
├── 03-trading-system/           # 取引システム
│   ├── trading-rules/           # 取引ルール
│   │   ├── entry-exit-rules.md      # エントリー・エグジット
│   │   └── hedge-strategies.md      # ヘッジ戦略
│   └── market-conditions/       # 市場条件
│       ├── range-trading.md         # レンジ判定式
│       └── volatility-handling.md   # もみ検討
│
├── 04-implementation/           # システム実装
│   ├── mt4-system/              # MT4システム
│   ├── system-settings/         # 設定ファイル
│   │   └── package-calculation-types.md  # PKG計算タイプ
│   └── trading-logic/           # 取引ロジック実装
│       └── pkg-placement-signals.md      # PKG配置信号
│
├── 05-operations/               # 運用・保守
│   ├── daily-operations/        # 日次運用
│   └── monitoring/              # 監視・ログ
│       └── economic-indicators.md   # 経済指標対応
│
├── 10-design-documents/         # 設計書（最新）
│   ├── 01-system-overview-design.md     # 全体設計
│   ├── 05-pkg-system-design.md          # PKGシステム詳細設計
│   ├── 06-infrastructure-design.md      # インフラ設計（Cloudflare）
│   └── 07-backtest-forward-test-optimization-design.md  # バックテスト設計
│
└── MEMO_PROCESSING_CHECKLIST.md # 97メモファイルの処理状況
```

## 開発コマンド

### テスト実行
```bash
# 基本システムテスト（外部依存なし）
python3 simple_test.py

# 統合テスト（pandas, numpy必要）
python3 test_system_integration.py
```

### データベース操作
```bash
# データベース初期化
python3 -c "from src.utils.database import DatabaseManager; DatabaseManager('./data/fx_trading.db')"
```

### OANDA API設定
```bash
# .envファイルをテンプレートから作成
cp .env.template .env
# .envを編集してOANDAデモアカウント情報を設定:
# OANDA_API_KEY=your_api_key
# OANDA_ACCOUNT_ID=your_account_id
# OANDA_ENV=practice
```

## プロジェクト構造

```
FX/
├── src/
│   ├── indicators/          # テクニカル指標（平均足、OsMA等）
│   │   └── base_indicators.py
│   ├── operation_logic/     # メモから抽出したコア取引ロジック
│   │   └── key_concepts.py  # 同逆判定、行帰判定、もみ判定実装
│   └── utils/
│       ├── database.py      # SQLite管理
│       └── oanda_client.py  # OANDA APIクライアント
├── docs/                    # 体系化されたドキュメント（97メモファイルから）
├── メモ/                    # オリジナル97メモファイル（Shift-JISエンコード）
├── data/                    # ヒストリカルデータとデータベース
└── 取得データ/              # CSVヒストリカルデータ
```

## パフォーマンス目標

メモファイルから抽出した実行時間目標：
- 全体: 19ms
- もみ: 77ms  
- OP分岐: 101.3ms
- オーバーシュート: 550.6ms
- 時間結合: 564.9ms

## 重要な実装上の注意事項

### 文字エンコーディング
- メモファイルはShift-JIS/CP932エンコーディング
- docs/内はすべてUTF-8に変換済み
- 必要に応じて`iconv -f CP932 -t UTF-8`で変換

### マルチタイムフレーム処理
6つの時間足を並列処理：
- M1（1分）、M5（5分）、M15（15分）、M30（30分）、H1（1時間）、H4（4時間）

### データベーススキーマ
SQLiteの主要テーブル：
- `price_data`: OHLCV価格データ
- `heikin_ashi_data`: 平均足計算結果
- `operation_signals`: 取引信号（同逆、行帰、もみ等）
- `trades`: 取引履歴
- `backtest_results`: バックテスト結果

### 取引ロジック実装優先順位
1. エントリールール
2. エグジットルール
3. ヘッジ戦略
4. 特殊状況対応

## 現在の開発状況

**Week 1（Day 1-2）完了:**
- Python環境構築
- 基本指標実装
- OANDA APIクライアント
- データベース管理システム
- オペレーションロジック核心概念

**次のステップ（Week 1 Day 3-4）:**
- メモファイル徹底分析の継続
- コア取引ロジックの改良
- ヒストリカルデータのインポートとテスト

## インフラストラクチャ目標

コスト効率的なCloudflareデプロイメント：
- Workers: APIエンドポイント
- D1: SQLiteデータベース
- R2: ヒストリカルデータストレージ
- 推定コスト: $5-50/月

## 重要な注意点

1. **メモベースのオペレーションロジックに集中** - Excelロジックの複製ではない
2. **関数型DAGアーキテクチャを維持** - 分岐探索パターンは使わない
3. **階層的IDシステムのフォーマットを厳守**
4. **システム検証完了までデモアカウントのみ使用**
5. **文字エンコーディング**: オリジナルメモのShift-JISに常に注意
6. **バックテスト目標**: 80%の予測精度達成（メモ記載の方法論に従う）