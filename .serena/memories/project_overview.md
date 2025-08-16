# FX Trading System - Project Overview

## Purpose
This is a sophisticated FX (Foreign Exchange) trading system that implements proprietary trading methodologies extracted from 97 Japanese memo files. The system uses a functional DAG (Directed Acyclic Graph) architecture with a hierarchical PKG (Package) system to process multi-timeframe trading signals.

## Core Architecture
- **Functional DAG Architecture**: Hierarchical ID system with format `[時間足][周期][通貨]^[階層]-[連番]`
- **PKG System**: Package-based signal processing with specific naming conventions
- **Multi-timeframe Processing**: Parallel processing of 6 timeframes (M1, M5, M15, M30, H1, H4)
- **Operation Logic**: Core concepts extracted from memo files: Dokyaku (same/reverse judgment), Ikikaeri (go/return judgment), Momi (range detection), Overshoot detection

## Key Features
- Real-time trading signal generation
- OANDA API integration for live trading
- Backtesting capabilities with 80% prediction accuracy target
- Comprehensive risk management
- Performance monitoring and optimization

## Target Performance (from memo files)
- Overall execution: 19ms
- Momi processing: 77ms
- OP branching: 101.3ms
- Overshoot: 550.6ms
- Time combination: 564.9ms

## Current Development Status
- Week 1 (Day 1-2): Completed - Basic infrastructure, OANDA client, core indicators
- Week 3: Real-time trading system implementation
- Target: 6-week development roadmap with incremental improvements