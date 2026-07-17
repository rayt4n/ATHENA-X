"""ForecastModel Protocol - stable interface for all AI forecast models.

Stage 5.1 req: Every component exposes a stable interface from day one.

ForecastModel (Protocol)
|_ ARIMA
|_ LSTM
|_ Transformer
|_ XGBoost
|_ LightGBM
|_ CatBoost
|_ TabPFN
|_ RandomForest
|_ LogisticRegression
|_ FutureModel  <- can be added without changing consumers
"""
from .protocol import ForecastModel, ModelInput, ModelOutput, ModelConfig, ModelRuntime

__all__ = ["ForecastModel", "ModelInput", "ModelOutput", "ModelConfig", "ModelRuntime"]
__version__ = "0.1.0"
