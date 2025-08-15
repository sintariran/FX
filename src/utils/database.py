"""
SQLite データベース管理クラス
価格データ、分析結果、取引履歴の永続化
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from contextlib import contextmanager
import os
import json


class DatabaseManager:
    """
    FX取引システム用データベース管理クラス
    """
    
    def __init__(self, db_path: str = "./data/fx_trading.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """データベース接続のコンテキストマネージャー"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 辞書形式でアクセス可能
        try:
            yield conn
        finally:
            conn.close()
    
    def init_database(self):
        """データベース初期化・テーブル作成"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 価格データテーブル
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS price_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    instrument TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    open REAL NOT NULL,
                    high REAL NOT NULL,
                    low REAL NOT NULL,
                    close REAL NOT NULL,
                    volume INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(instrument, timeframe, timestamp)
                )
            """)
            
            # 平均足データテーブル
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS heikin_ashi_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    instrument TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    ha_open REAL NOT NULL,
                    ha_high REAL NOT NULL,
                    ha_low REAL NOT NULL,
                    ha_close REAL NOT NULL,
                    ha_direction INTEGER NOT NULL,
                    ha_reversal INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(instrument, timeframe, timestamp)
                )
            """)
            
            # オペレーション判定結果テーブル
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS operation_signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    instrument TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    dokyaku_signal INTEGER,  -- 同逆判定結果
                    ikikaeri_signal INTEGER, -- 行帰判定結果
                    momi_signal INTEGER,     -- もみ判定結果
                    overshoot_signal INTEGER, -- オーバーシュート判定結果
                    overall_signal INTEGER,  -- 総合判定結果
                    confidence REAL,         -- 確信度
                    metadata TEXT,           -- JSON形式の追加情報
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(instrument, timeframe, timestamp)
                )
            """)
            
            # 取引履歴テーブル
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    instrument TEXT NOT NULL,
                    trade_type TEXT NOT NULL, -- BUY, SELL
                    entry_time DATETIME NOT NULL,
                    entry_price REAL NOT NULL,
                    exit_time DATETIME,
                    exit_price REAL,
                    units INTEGER NOT NULL,
                    profit_loss REAL,
                    stop_loss_price REAL,
                    take_profit_price REAL,
                    entry_signal_id INTEGER, -- operation_signalsテーブルへの参照
                    status TEXT DEFAULT 'OPEN', -- OPEN, CLOSED
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (entry_signal_id) REFERENCES operation_signals (id)
                )
            """)
            
            # バックテスト結果テーブル
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS backtest_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    test_name TEXT NOT NULL,
                    instrument TEXT NOT NULL,
                    start_date DATETIME NOT NULL,
                    end_date DATETIME NOT NULL,
                    total_trades INTEGER,
                    winning_trades INTEGER,
                    losing_trades INTEGER,
                    win_rate REAL,
                    total_profit_loss REAL,
                    max_drawdown REAL,
                    sharpe_ratio REAL,
                    profit_factor REAL,
                    parameters TEXT, -- JSON形式のパラメータ
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # パフォーマンス履歴テーブル
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS performance_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation_name TEXT NOT NULL,
                    execution_time REAL NOT NULL, -- ms
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # インデックス作成
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_price_data_lookup ON price_data (instrument, timeframe, timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_heikin_ashi_lookup ON heikin_ashi_data (instrument, timeframe, timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_operation_signals_lookup ON operation_signals (instrument, timeframe, timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_lookup ON trades (instrument, entry_time)")
            
            conn.commit()
            print("✅ データベース初期化完了")
    
    def save_price_data(self, instrument: str, timeframe: str, df: pd.DataFrame):
        """価格データ保存"""
        with self.get_connection() as conn:
            # DataFrameをSQLiteに保存
            records = []
            for timestamp, row in df.iterrows():
                records.append({
                    'instrument': instrument,
                    'timeframe': timeframe,
                    'timestamp': timestamp,
                    'open': row['open'],
                    'high': row['high'],
                    'low': row['low'],
                    'close': row['close'],
                    'volume': row.get('volume', 0)
                })
            
            # バッチ挿入（重複は無視）
            cursor = conn.cursor()
            cursor.executemany("""
                INSERT OR IGNORE INTO price_data 
                (instrument, timeframe, timestamp, open, high, low, close, volume)
                VALUES (:instrument, :timeframe, :timestamp, :open, :high, :low, :close, :volume)
            """, records)
            
            conn.commit()
            print(f"💾 価格データ保存: {instrument} {timeframe} ({len(records)} records)")
    
    def load_price_data(self, 
                        instrument: str, 
                        timeframe: str,
                        start_date: Optional[str] = None,
                        end_date: Optional[str] = None) -> pd.DataFrame:
        """価格データ読み込み"""
        with self.get_connection() as conn:
            query = """
                SELECT timestamp, open, high, low, close, volume 
                FROM price_data 
                WHERE instrument = ? AND timeframe = ?
            """
            params = [instrument, timeframe]
            
            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date)
            
            if end_date:
                query += " AND timestamp <= ?"
                params.append(end_date)
            
            query += " ORDER BY timestamp"
            
            df = pd.read_sql_query(query, conn, params=params, parse_dates=['timestamp'])
            
            if not df.empty:
                df.set_index('timestamp', inplace=True)
            
            return df
    
    def save_heikin_ashi_data(self, instrument: str, timeframe: str, df: pd.DataFrame):
        """平均足データ保存"""
        with self.get_connection() as conn:
            records = []
            for timestamp, row in df.iterrows():
                records.append({
                    'instrument': instrument,
                    'timeframe': timeframe,
                    'timestamp': timestamp,
                    'ha_open': row['ha_open'],
                    'ha_high': row['ha_high'],
                    'ha_low': row['ha_low'],
                    'ha_close': row['ha_close'],
                    'ha_direction': row['ha_direction'],
                    'ha_reversal': row.get('ha_reversal', 0)
                })
            
            cursor = conn.cursor()
            cursor.executemany("""
                INSERT OR REPLACE INTO heikin_ashi_data 
                (instrument, timeframe, timestamp, ha_open, ha_high, ha_low, ha_close, ha_direction, ha_reversal)
                VALUES (:instrument, :timeframe, :timestamp, :ha_open, :ha_high, :ha_low, :ha_close, :ha_direction, :ha_reversal)
            """, records)
            
            conn.commit()
            print(f"💾 平均足データ保存: {instrument} {timeframe} ({len(records)} records)")
    
    def save_operation_signal(self, 
                              instrument: str,
                              timeframe: str,
                              timestamp: datetime,
                              signals: Dict[str, Any],
                              confidence: float = 0.0,
                              metadata: Optional[Dict] = None) -> int:
        """オペレーション判定結果保存"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            metadata_json = json.dumps(metadata) if metadata else None
            
            cursor.execute("""
                INSERT OR REPLACE INTO operation_signals 
                (instrument, timeframe, timestamp, dokyaku_signal, ikikaeri_signal, 
                 momi_signal, overshoot_signal, overall_signal, confidence, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                instrument, timeframe, timestamp,
                signals.get('dokyaku', 0),
                signals.get('ikikaeri', 0),
                signals.get('momi', 0),
                signals.get('overshoot', 0),
                signals.get('overall', 0),
                confidence,
                metadata_json
            ))
            
            conn.commit()
            return cursor.lastrowid
    
    def save_trade(self, trade_data: Dict[str, Any]) -> int:
        """取引履歴保存"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO trades 
                (instrument, trade_type, entry_time, entry_price, exit_time, exit_price,
                 units, profit_loss, stop_loss_price, take_profit_price, entry_signal_id, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trade_data['instrument'],
                trade_data['trade_type'],
                trade_data['entry_time'],
                trade_data['entry_price'],
                trade_data.get('exit_time'),
                trade_data.get('exit_price'),
                trade_data['units'],
                trade_data.get('profit_loss'),
                trade_data.get('stop_loss_price'),
                trade_data.get('take_profit_price'),
                trade_data.get('entry_signal_id'),
                trade_data.get('status', 'OPEN')
            ))
            
            conn.commit()
            return cursor.lastrowid
    
    def save_backtest_result(self, result_data: Dict[str, Any]) -> int:
        """バックテスト結果保存"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            parameters_json = json.dumps(result_data.get('parameters', {}))
            
            cursor.execute("""
                INSERT INTO backtest_results 
                (test_name, instrument, start_date, end_date, total_trades, winning_trades,
                 losing_trades, win_rate, total_profit_loss, max_drawdown, sharpe_ratio,
                 profit_factor, parameters)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result_data['test_name'],
                result_data['instrument'],
                result_data['start_date'],
                result_data['end_date'],
                result_data['total_trades'],
                result_data['winning_trades'],
                result_data['losing_trades'],
                result_data['win_rate'],
                result_data['total_profit_loss'],
                result_data['max_drawdown'],
                result_data['sharpe_ratio'],
                result_data['profit_factor'],
                parameters_json
            ))
            
            conn.commit()
            return cursor.lastrowid
    
    def get_operation_signals(self, 
                              instrument: str,
                              timeframe: str,
                              start_date: Optional[str] = None,
                              end_date: Optional[str] = None) -> pd.DataFrame:
        """オペレーション判定結果取得"""
        with self.get_connection() as conn:
            query = """
                SELECT * FROM operation_signals 
                WHERE instrument = ? AND timeframe = ?
            """
            params = [instrument, timeframe]
            
            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date)
            
            if end_date:
                query += " AND timestamp <= ?"
                params.append(end_date)
            
            query += " ORDER BY timestamp"
            
            return pd.read_sql_query(query, conn, params=params, parse_dates=['timestamp'])
    
    def get_trades(self, 
                   instrument: Optional[str] = None,
                   status: Optional[str] = None) -> pd.DataFrame:
        """取引履歴取得"""
        with self.get_connection() as conn:
            query = "SELECT * FROM trades WHERE 1=1"
            params = []
            
            if instrument:
                query += " AND instrument = ?"
                params.append(instrument)
            
            if status:
                query += " AND status = ?"
                params.append(status)
            
            query += " ORDER BY entry_time DESC"
            
            return pd.read_sql_query(query, conn, params=params, 
                                   parse_dates=['entry_time', 'exit_time'])
    
    def get_backtest_results(self, test_name: Optional[str] = None) -> pd.DataFrame:
        """バックテスト結果取得"""
        with self.get_connection() as conn:
            query = "SELECT * FROM backtest_results"
            params = []
            
            if test_name:
                query += " WHERE test_name = ?"
                params.append(test_name)
            
            query += " ORDER BY created_at DESC"
            
            return pd.read_sql_query(query, conn, params=params, 
                                   parse_dates=['start_date', 'end_date', 'created_at'])
    
    def log_performance(self, operation_name: str, execution_time: float):
        """パフォーマンス記録"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO performance_log (operation_name, execution_time)
                VALUES (?, ?)
            """, (operation_name, execution_time))
            conn.commit()
    
    def get_database_stats(self) -> Dict[str, int]:
        """データベース統計情報"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            tables = ['price_data', 'heikin_ashi_data', 'operation_signals', 'trades', 'backtest_results']
            
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                stats[table] = cursor.fetchone()[0]
            
            return stats
    
    def cleanup_old_data(self, days_to_keep: int = 90):
        """古いデータのクリーンアップ"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # パフォーマンスログの古いデータ削除
            cursor.execute("""
                DELETE FROM performance_log 
                WHERE timestamp < datetime('now', '-{} days')
            """.format(days_to_keep))
            
            deleted_rows = cursor.rowcount
            conn.commit()
            
            print(f"🧹 古いパフォーマンスログ {deleted_rows} 件削除")


if __name__ == "__main__":
    # テスト実行
    print("🗄️  データベース管理クラス テスト開始")
    
    # データベース初期化
    db = DatabaseManager("./data/test_fx_trading.db")
    
    # テストデータ作成
    test_df = pd.DataFrame({
        'open': [150.0, 150.1, 150.2],
        'high': [150.1, 150.3, 150.4],
        'low': [149.9, 150.0, 150.1],
        'close': [150.1, 150.2, 150.3],
        'volume': [1000, 1100, 1200]
    }, index=pd.date_range('2024-01-01 00:00', periods=3, freq='1min'))
    
    # 価格データ保存テスト
    print("💾 価格データ保存テスト...")
    db.save_price_data("USD_JPY", "M1", test_df)
    
    # 価格データ読み込みテスト
    print("📂 価格データ読み込みテスト...")
    loaded_df = db.load_price_data("USD_JPY", "M1")
    print(f"✅ 読み込み: {len(loaded_df)} rows")
    print(loaded_df)
    
    # 統計情報テスト
    print("\n📊 データベース統計...")
    stats = db.get_database_stats()
    for table, count in stats.items():
        print(f"  {table}: {count} records")
    
    print("\n✅ データベーステスト完了！")
    
    # テストファイル削除
    os.remove("./data/test_fx_trading.db")
    print("🧹 テストファイル削除完了")