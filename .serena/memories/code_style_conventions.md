# Code Style and Conventions

## Python Style
- **Line Length**: 88 characters (configured in pyproject.toml)
- **Target Version**: Python 3.11+
- **Formatter**: Black 23.0.0+
- **Linter**: Flake8 6.0.0+
- **Type Checker**: MyPy 1.6.0+ with strict settings

## Type Hints
- **Required**: `disallow_untyped_defs = true` in mypy config
- **Return Types**: `warn_return_any = true`
- All function definitions must include type hints

## Code Organization Patterns
### Imports
```python
# Standard library imports first
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple

# Third-party imports
import pandas as pd
import numpy as np

# Local imports last
from utils.database import DatabaseManager
```

### Class Definitions
- Use dataclasses for data containers (`@dataclass`)
- Use Enums for constants and categorical values
- Abstract base classes for interfaces (`ABC, @abstractmethod`)

### Naming Conventions
- **Classes**: PascalCase (`OperationLogicEngine`, `BaseIndicators`)
- **Functions/Methods**: snake_case (`calculate_heikin_ashi`, `get_price_data`)
- **Constants**: UPPER_SNAKE_CASE (`PERFORMANCE_TARGETS`, `DEFAULT_TIMEFRAMES`)
- **Enums**: PascalCase for class, UPPER_CASE for values (`Direction.UP`, `TimeFrame.M1`)

### Documentation
- **Docstrings**: Japanese comments for business logic, English for technical details
- **File Headers**: Include purpose and main concepts
- **Inline Comments**: Explain complex trading logic and memo file references

## Project-Specific Conventions
### PKG System
- ID format: `[時間足][周期][通貨]^[階層]-[連番]` (e.g., `191^2-126`)
- Function naming follows memo file terminology (Dokyaku, Ikikaeri, etc.)

### Error Handling
- Use structured logging (`structlog`)
- Comprehensive error tracking for trading operations
- Performance monitoring with `PerformanceTracker` class

### File Encoding
- **Source Code**: UTF-8
- **Original Memo Files**: Shift-JIS/CP932 (preserved for reference)
- **Documentation**: UTF-8 (converted from memo files)