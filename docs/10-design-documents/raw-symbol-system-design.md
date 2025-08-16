# 生データ記号システム設計書
## 2700記号体系による基盤データ管理

### 1. 概要

生データ記号システムは、PKGシステムの基盤となる2700以上の記号を管理し、市場データから各記号の値を提供するシステムです。

### 2. 記号体系（list.txt）

#### 2.1 記号分類
```
総数: 2700以上

主要カテゴリ:
┌─────────────────────────────────────────────┐
│ 記号範囲    │ 分類        │ 説明              │
├─────────────────────────────────────────────┤
│ 0ZZ002-004  │ システム    │ システム予約記号   │
│ AA001-329   │ 基本価格    │ OHLC等基本価格    │
│ AB301-312   │ 派生価格    │ 計算済み価格データ │
│ AC301-312   │ 価格統計    │ 価格統計値        │
│ AD301-312   │ 価格指標    │ 価格指標値        │
│ Asa003-021  │ 1分足データ │ 時系列データ(M1)  │
│ Asb001-021  │ 5分足データ │ 時系列データ(M5)  │
│ Asc001-021  │ 15分足データ│ 時系列データ(M15) │
│ Asd001-021  │ 30分足データ│ 時系列データ(M30) │
│ Ase001-021  │ 1時間データ │ 時系列データ(H1)  │
│ Asf001-021  │ 4時間データ │ 時系列データ(H4)  │
│ BA018-142   │ ボリューム  │ 出来高・取引量    │
│ BB018-142   │ ボリューム2 │ 追加ボリューム    │
│ CA011-142   │ 計算指標    │ 技術指標計算値    │
│ SU003-092   │ 統計データ  │ 統計計算結果      │
│ ZA001-110   │ 集計データ  │ 最終集計値        │
└─────────────────────────────────────────────┘
```

#### 2.2 命名規則
```
[カテゴリ][サブカテゴリ][連番]

例:
AA001: 基本価格(A) + サブセットA + 連番001
Asa003: 時系列(As) + 1分足(a) + 連番003  
BA018: ボリューム(B) + サブセットA + 連番018
CA042: 計算値(C) + サブセットA + 連番042
```

### 3. データソース定義（initial_setting_list_os.xlsx）

#### 3.1 記号定義シート
| 記号 | データ種別 | 計算式/ソース | 更新頻度 | 説明 |
|------|-----------|--------------|----------|------|
| AA001 | 価格 | OANDA.bid | リアルタイム | 現在ビッド価格 |
| AA002 | 価格 | previous_close | 足確定時 | 前足終値 |
| AA003 | 価格 | high[0] | リアルタイム | 現在足高値 |
| AA004 | 価格 | low[0] | リアルタイム | 現在足安値 |
| Asa003 | 平均足 | heikin_ashi_close | 足確定時 | 1分足平均足終値 |
| BA018 | 出来高 | volume[0] | リアルタイム | 現在足出来高 |
| CA001 | 指標 | SMA(AA001, 20) | リアルタイム | 20期間移動平均 |

#### 3.2 パラメータ設定シート
| パラメータ名 | デフォルト値 | 説明 |
|-------------|-------------|------|
| SMA_PERIOD_1 | 20 | 短期移動平均期間 |
| SMA_PERIOD_2 | 50 | 長期移動平均期間 |
| ATR_PERIOD | 14 | ATR計算期間 |
| RANGE_THRESHOLD | 0.003 | レンジ判定閾値(0.3%) |

### 4. 実装アーキテクチャ

#### 4.1 データ管理クラス
```python
class RawSymbolManager:
    """生データ記号管理システム"""
    
    def __init__(self, config_path: str):
        self.symbol_definitions = self._load_definitions(config_path)
        self.cache = {}
        self.update_handlers = {}
        self.data_sources = {}
        
    def _load_definitions(self, config_path: str) -> Dict[str, SymbolDefinition]:
        """Excel設定ファイルから記号定義を読み込み"""
        definitions = {}
        
        # initial_setting_list_os.xlsxを読み込み
        workbook = load_workbook(config_path)
        
        # 記号定義シート
        symbols_sheet = workbook['Symbol_Definitions']
        for row in symbols_sheet.iter_rows(min_row=2, values_only=True):
            symbol, data_type, formula, frequency, description = row
            definitions[symbol] = SymbolDefinition(
                symbol=symbol,
                data_type=data_type,
                formula=formula,
                update_frequency=frequency,
                description=description
            )
        
        return definitions
    
    def get_value(self, symbol: str, context: Dict = None) -> float:
        """記号の現在値を取得"""
        
        # キャッシュチェック
        if symbol in self.cache:
            cached_data = self.cache[symbol]
            if self._is_cache_valid(cached_data):
                return cached_data['value']
        
        # 値を計算または取得
        definition = self.symbol_definitions.get(symbol)
        if not definition:
            raise ValueError(f"Unknown symbol: {symbol}")
        
        value = self._calculate_symbol_value(definition, context)
        
        # キャッシュ更新
        self.cache[symbol] = {
            'value': value,
            'timestamp': time.time(),
            'ttl': self._get_cache_ttl(definition.update_frequency)
        }
        
        return value
```

#### 4.2 記号定義データクラス
```python
@dataclass
class SymbolDefinition:
    """記号定義"""
    symbol: str              # 記号名 (例: AA001)
    data_type: str          # データ種別 (price, volume, indicator)
    formula: str            # 計算式またはデータソース
    update_frequency: str   # 更新頻度 (realtime, tick, 1min, 5min)
    description: str        # 説明
    dependencies: List[str] = field(default_factory=list)  # 依存記号
    
class MarketDataSource:
    """市場データソース"""
    
    def get_current_price(self, symbol: str) -> float:
        """現在価格取得"""
        pass
    
    def get_volume(self, symbol: str) -> float:
        """現在出来高取得"""
        pass
    
    def get_historical_data(self, symbol: str, period: int) -> List[float]:
        """履歴データ取得"""
        pass
```

#### 4.3 データ計算エンジン
```python
class SymbolCalculationEngine:
    """記号値計算エンジン"""
    
    def __init__(self, data_source: MarketDataSource):
        self.data_source = data_source
        self.indicators = TechnicalIndicators()
        
    def calculate_symbol_value(self, definition: SymbolDefinition, 
                             context: Dict = None) -> float:
        """記号値を計算"""
        
        formula = definition.formula
        
        # データソース直接参照
        if formula.startswith('OANDA.'):
            return self._get_oanda_data(formula)
        
        # 技術指標計算
        elif formula.startswith('SMA('):
            return self._calculate_sma(formula)
        elif formula.startswith('EMA('):
            return self._calculate_ema(formula)
        elif formula.startswith('ATR('):
            return self._calculate_atr(formula)
        
        # 平均足計算
        elif formula.startswith('heikin_ashi_'):
            return self._calculate_heikin_ashi(formula)
        
        # 四則演算
        elif any(op in formula for op in ['+', '-', '*', '/']):
            return self._evaluate_arithmetic(formula, context)
        
        # 直接値
        else:
            try:
                return float(formula)
            except ValueError:
                raise ValueError(f"Cannot evaluate formula: {formula}")
    
    def _calculate_sma(self, formula: str) -> float:
        """SMA計算: SMA(symbol, period)"""
        # 例: SMA(AA001, 20)
        match = re.match(r'SMA\((\w+),\s*(\d+)\)', formula)
        if not match:
            raise ValueError(f"Invalid SMA formula: {formula}")
        
        base_symbol, period = match.groups()
        period = int(period)
        
        # 履歴データ取得
        historical_data = self.data_source.get_historical_data(base_symbol, period)
        
        # SMA計算
        return sum(historical_data[-period:]) / period
```

#### 4.4 リアルタイム更新システム
```python
class RealTimeUpdateManager:
    """リアルタイム更新管理"""
    
    def __init__(self, symbol_manager: RawSymbolManager):
        self.symbol_manager = symbol_manager
        self.update_queue = asyncio.Queue()
        self.subscribers = defaultdict(list)
        
    async def start_updates(self):
        """更新プロセス開始"""
        
        # 各更新頻度別のタスク起動
        tasks = [
            self._realtime_update_loop(),    # リアルタイム更新
            self._minute_update_loop(),      # 1分更新
            self._tick_update_loop()         # ティック更新
        ]
        
        await asyncio.gather(*tasks)
    
    async def _realtime_update_loop(self):
        """リアルタイム更新ループ"""
        while True:
            # リアルタイム更新対象の記号を更新
            realtime_symbols = self._get_symbols_by_frequency('realtime')
            
            for symbol in realtime_symbols:
                try:
                    new_value = self.symbol_manager.get_value(symbol)
                    await self._notify_subscribers(symbol, new_value)
                except Exception as e:
                    logger.error(f"Failed to update {symbol}: {e}")
            
            await asyncio.sleep(0.1)  # 100ms間隔
    
    def subscribe(self, symbol: str, callback: Callable):
        """記号の更新を購読"""
        self.subscribers[symbol].append(callback)
    
    async def _notify_subscribers(self, symbol: str, value: float):
        """購読者に通知"""
        for callback in self.subscribers[symbol]:
            try:
                await callback(symbol, value)
            except Exception as e:
                logger.error(f"Subscriber callback failed: {e}")
```

### 5. パフォーマンス最適化

#### 5.1 キャッシング戦略
```python
class SymbolCache:
    """記号値キャッシュ"""
    
    CACHE_TTL = {
        'realtime': 0.1,    # 100ms
        'tick': 1.0,        # 1秒
        '1min': 60.0,       # 1分
        '5min': 300.0,      # 5分
        'static': 3600.0    # 1時間
    }
    
    def __init__(self):
        self.cache = {}
        self.access_count = defaultdict(int)
        
    def get(self, symbol: str) -> Optional[Dict]:
        """キャッシュから取得"""
        if symbol in self.cache:
            data = self.cache[symbol]
            if time.time() - data['timestamp'] < data['ttl']:
                self.access_count[symbol] += 1
                return data
            else:
                del self.cache[symbol]
        return None
    
    def set(self, symbol: str, value: float, frequency: str):
        """キャッシュに設定"""
        ttl = self.CACHE_TTL.get(frequency, 1.0)
        self.cache[symbol] = {
            'value': value,
            'timestamp': time.time(),
            'ttl': ttl
        }
```

#### 5.2 依存関係解決
```python
class DependencyResolver:
    """記号間依存関係解決"""
    
    def __init__(self, symbol_manager: RawSymbolManager):
        self.symbol_manager = symbol_manager
        self.dependency_graph = self._build_dependency_graph()
        
    def _build_dependency_graph(self) -> nx.DiGraph:
        """依存関係グラフ構築"""
        graph = nx.DiGraph()
        
        for symbol, definition in self.symbol_manager.symbol_definitions.items():
            graph.add_node(symbol)
            
            # 計算式から依存記号を抽出
            dependencies = self._extract_dependencies(definition.formula)
            for dep in dependencies:
                graph.add_edge(dep, symbol)
        
        # 循環依存チェック
        if not nx.is_directed_acyclic_graph(graph):
            cycles = list(nx.simple_cycles(graph))
            raise ValueError(f"Circular dependencies detected: {cycles}")
        
        return graph
    
    def get_update_order(self, symbols: List[str]) -> List[str]:
        """更新順序取得（トポロジカルソート）"""
        subgraph = self.dependency_graph.subgraph(symbols)
        return list(nx.topological_sort(subgraph))
```

### 6. エラー処理・監視

#### 6.1 データ品質チェック
```python
class DataQualityChecker:
    """データ品質チェック"""
    
    def validate_symbol_value(self, symbol: str, value: float) -> bool:
        """記号値の妥当性チェック"""
        
        # 価格データのレンジチェック
        if symbol.startswith('AA'):  # 価格系
            if not (50.0 <= value <= 200.0):  # USDJPY想定
                logger.warning(f"Price out of range: {symbol}={value}")
                return False
        
        # ボリュームの非負チェック
        elif symbol.startswith('BA'):  # ボリューム系
            if value < 0:
                logger.warning(f"Negative volume: {symbol}={value}")
                return False
        
        # NaN/Infチェック
        if not math.isfinite(value):
            logger.error(f"Invalid value: {symbol}={value}")
            return False
        
        return True
```

### 7. 設定ファイル仕様（initial_setting_list_os.xlsx）

#### 7.1 シート構成
```
1. Symbol_Definitions    # 記号定義
2. Parameters           # パラメータ設定
3. Data_Sources         # データソース設定
4. Update_Frequencies   # 更新頻度定義
5. Validation_Rules     # 検証ルール
```

#### 7.2 Symbol_Definitionsシート
| 列 | 項目 | 説明 | 例 |
|----|------|------|-----|
| A | Symbol | 記号名 | AA001 |
| B | Data_Type | データ種別 | price |
| C | Formula | 計算式 | OANDA.bid |
| D | Update_Frequency | 更新頻度 | realtime |
| E | Description | 説明 | 現在ビッド価格 |
| F | Dependencies | 依存記号 | AA002,AA003 |
| G | Validation_Rule | 検証ルール | range(50,200) |

### 8. テスト戦略

#### 8.1 単体テスト
```python
def test_symbol_calculation():
    """記号計算テスト"""
    
    # モックデータソース
    mock_source = MockMarketDataSource()
    mock_source.set_price('USDJPY', 110.50)
    
    # 計算エンジン
    engine = SymbolCalculationEngine(mock_source)
    
    # AA001(現在価格)テスト
    definition = SymbolDefinition(
        symbol='AA001',
        data_type='price',
        formula='OANDA.bid',
        update_frequency='realtime',
        description='現在ビッド価格'
    )
    
    value = engine.calculate_symbol_value(definition)
    assert value == 110.50
```

#### 8.2 統合テスト
```python
def test_full_symbol_system():
    """記号システム全体テスト"""
    
    manager = RawSymbolManager('test_config.xlsx')
    
    # 全記号の値取得テスト
    for symbol in ['AA001', 'AA002', 'BA018', 'CA001']:
        value = manager.get_value(symbol)
        assert isinstance(value, float)
        assert math.isfinite(value)
    
    # 依存関係テスト
    # CA001(SMA)がAA001(価格)に依存
    aa001_value = manager.get_value('AA001')
    ca001_value = manager.get_value('CA001')
    
    # SMAは価格と同程度の値であるべき
    assert abs(ca001_value - aa001_value) < aa001_value * 0.1
```

### 9. まとめ

生データ記号システムは、PKGシステムの基盤として2700以上の記号を効率的に管理し、リアルタイムで値を提供します。階層1のPKG関数は、この記号システムから直接データを取得して処理を行います。