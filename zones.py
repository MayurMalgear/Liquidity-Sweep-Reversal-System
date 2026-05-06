import pandas as pd
import numpy as np


def find_liquidity_zones(
    df: pd.DataFrame,
    window: int = 10,
    tolerance_pct: float = 0.002,
    min_touches: int = 2,
):
    """
    Identify liquidity zones (equal highs / equal lows) using percentage-based
    tolerance instead of a fixed pip value — works for any asset and price range.

    Args:
        df:            OHLCV DataFrame
        window:        bars on each side to look for matching levels
        tolerance_pct: price must be within this % to be considered "equal"
        min_touches:   minimum times level must be touched to qualify

    Returns:
        resistance_levels: list of (index, price)
        support_levels:    list of (index, price)
    """
    resistance_levels = []
    support_levels = []

    for i in range(window, len(df) - window):
        high = df["High"].iloc[i]
        low = df["Low"].iloc[i]

        high_slice = df["High"].iloc[i - window : i + window]
        low_slice = df["Low"].iloc[i - window : i + window]

        # Percentage distance rather than absolute
        high_tol = high * tolerance_pct
        low_tol = low * tolerance_pct

        touches_high = np.sum(np.abs(high_slice - high) < high_tol)
        touches_low = np.sum(np.abs(low_slice - low) < low_tol)

        if touches_high >= min_touches:
            resistance_levels.append((i, high))
        if touches_low >= min_touches:
            support_levels.append((i, low))

    # Deduplicate nearby levels (merge zones within 0.5% of each other)
    resistance_levels = _merge_close_levels(resistance_levels, tolerance_pct * 2)
    support_levels = _merge_close_levels(support_levels, tolerance_pct * 2)

    return resistance_levels, support_levels


def _merge_close_levels(levels, tolerance_pct):
    """Merge levels that are very close together to avoid duplicate zones."""
    if not levels:
        return levels
    merged = [levels[0]]
    for idx, price in levels[1:]:
        last_price = merged[-1][1]
        if abs(price - last_price) / last_price > tolerance_pct:
            merged.append((idx, price))
    return merged
