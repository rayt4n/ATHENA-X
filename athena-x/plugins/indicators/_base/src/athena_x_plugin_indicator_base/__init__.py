"""TechnicalIndicator Protocol - stable interface for all TA indicators.

Stage 5.1 req: Every component exposes a stable interface from day one.

TechnicalIndicator (Protocol)
|_ EMA
|_ RSI
|_ MACD
|_ SMA
|_ VWAP
|_ ADX
|_ ATR
|_ BollingerBands
|_ Fibonacci
|_ Stochastic
|_ CCI
|_ WilliamsR
|_ Ichimoku
|_ OBV
|_ FutureIndicator  <- can be added without changing consumers
"""
from .protocol import TechnicalIndicator, IndicatorInput, IndicatorOutput, IndicatorParams

__all__ = ["TechnicalIndicator", "IndicatorInput", "IndicatorOutput", "IndicatorParams"]
__version__ = "0.1.0"
