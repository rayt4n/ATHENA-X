"""Types of options data to collect (Stage 2 req 1.2).

Even metrics that require later computation (IV Rank, GEX, Max Pain,
Expected Move) — the RAW DATA required to derive them is collected now.
"""
from __future__ import annotations
from enum import Enum


class OptionsDataType(str, Enum):
    """16 types of options data to collect."""
    OPTION_CHAIN = "option_chain"
    OPEN_INTEREST = "open_interest"
    VOLUME = "volume"
    GREEKS = "greeks"
    IV = "iv"
    IV_RANK_RAW = "iv_rank_raw"           # raw IV history for IV Rank computation
    IV_PERCENTILE_RAW = "iv_percentile_raw"  # raw IV history for IV Percentile
    GAMMA_EXPOSURE_RAW = "gamma_exposure_raw"  # raw greeks for GEX computation
    GAMMA_FLIP_RAW = "gamma_flip_raw"      # raw greeks for gamma flip detection
    DEALER_POSITIONING_RAW = "dealer_positioning_raw"  # raw OI for dealer estimation
    MAX_PAIN_RAW = "max_pain_raw"          # raw OI for max pain computation
    EXPECTED_MOVE_RAW = "expected_move_raw"  # raw IV for expected move
    ZERO_DTE = "0dte"
    OPTION_FLOW = "option_flow"
    DARK_POOL = "dark_pool"
    SHORT_INTEREST = "short_interest"


# All 16 types — Stage 2 collects raw data for all
OPTIONS_DATA_TYPES = [t.value for t in OptionsDataType]
