# System Architecture and Design Patterns

## Overall Architecture
The FX trading system follows a **functional DAG (Directed Acyclic Graph)** architecture with hierarchical processing layers.

## Core Components

### 1. PKG System (Package Functions)
- **Location**: `src/pkg/`
- **Purpose**: Hierarchical function evaluation system
- **ID Format**: `[時間足][周期][通貨]^[階層]-[連番]`
  - Example: `191^2-126` = 1分足(1), 周期なし(9), USDJPY(1), 第2階層(2), 126番
- **Key Functions**: Z(2), Z(8), SL, OR, AND, CO, SG, AS, MN

### 2. Operation Logic Engine
- **Location**: `src/operation_logic/`
- **Purpose**: Core trading concepts from 97 memo files
- **Key Concepts**:
  - **Dokyaku (同逆)**: Same/reverse direction judgment
  - **Ikikaeri (行帰)**: Go/return pattern analysis  
  - **Momi**: Range trading detection
  - **Overshoot**: Breakout detection

### 3. Indicators System
- **Location**: `src/indicators/`
- **Purpose**: Technical analysis calculations
- **Key Indicators**: Heikin Ashi, OsMA, Parabolic SAR, Range detection

### 4. Data Management
- **Location**: `src/utils/database.py`
- **Database**: SQLite (local), PostgreSQL (production)
- **Tables**: price_data, heikin_ashi_data, operation_signals, trades, backtest_results

### 5. OANDA Integration
- **Location**: `src/utils/oanda_client.py` 
- **Purpose**: Live data feeds and trade execution
- **Configuration**: Environment-based (.env file)

## Design Patterns

### 1. Factory Pattern
- **Usage**: PKG function creation (`src/pkg/function_factory.py`)
- **Benefit**: Dynamic function instantiation based on PKG IDs

### 2. Strategy Pattern  
- **Usage**: Different trading strategies based on market conditions
- **Implementation**: Abstract base classes with concrete implementations

### 3. Observer Pattern
- **Usage**: Real-time data processing and event handling
- **Implementation**: Event-driven architecture for price updates

### 4. Command Pattern
- **Usage**: Trade execution and rollback capabilities
- **Implementation**: Encapsulated trading operations

## Multi-Timeframe Processing
- **Parallel Processing**: 6 timeframes (M1, M5, M15, M30, H1, H4)
- **Synchronization**: Time-based coordination between timeframes
- **Integration**: Hierarchical decision making across timeframes

## Performance Optimization
- **Caching**: DAG computation results (`src/utils/dag_cache.py`)
- **Profiling**: Performance tracking (`src/utils/performance_profiler.py`)
- **Async Processing**: Non-blocking I/O operations

## Error Handling
- **Structured Logging**: Using structlog for comprehensive logging
- **Error Recovery**: Graceful degradation for API failures
- **Monitoring**: Real-time system health monitoring

## Security Architecture
- **API Key Management**: Environment variable based
- **Trade Validation**: Multi-layer verification before execution
- **Demo Mode**: Safe testing environment