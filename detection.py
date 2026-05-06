import pandas as pd
import numpy as np


def detect_sweeps(
    df: pd.DataFrame,
    resistance_levels,
    support_levels,
    lookahead: int = 3,
    use_rsi_filter: bool = True,
    use_volume_filter: bool = True,
):
    """
    Detect liquidity sweeps with optional RSI and volume confirmation.

    A SELL sweep:
      - Price spikes above a resistance level (fake breakout)
      - Then closes back below it within `lookahead` bars
      - Confirmed by RSI > 65 (overbought) and/or above-average volume

    A BUY sweep:
      - Price dips below a support level (stop hunt)
      - Then closes back above it within `lookahead` bars
      - Confirmed by RSI < 35 (oversold) and/or above-average volume

    Returns:
        List of dicts: {type, index, price, zone, rsi, volume_ratio, strength}
    """
    sweeps = []
    avg_volume = df["Volume"].rolling(20).mean()

    for idx, level in resistance_levels:
        if idx + 1 >= len(df):
            continue
        # Spike above resistance
        if df["High"].iloc[idx + 1] > level:
            for j in range(1, lookahead + 1):
                if idx + j >= len(df):
                    break
                if df["Close"].iloc[idx + j] < level:
                    rsi = df["RSI"].iloc[idx + j] if "RSI" in df.columns else None
                    vol_ratio = (
                        df["Volume"].iloc[idx + j] / avg_volume.iloc[idx + j]
                        if avg_volume.iloc[idx + j] > 0
                        else 1.0
                    )

                    # Apply filters
                    rsi_ok = (rsi is None) or (not use_rsi_filter) or (rsi > 55)
                    vol_ok = (not use_volume_filter) or (vol_ratio > 1.0)

                    if rsi_ok and vol_ok:
                        strength = _sweep_strength(rsi, vol_ratio, "sell")
                        sweeps.append(
                            {
                                "type": "sell",
                                "index": idx + j,
                                "price": df["Close"].iloc[idx + j],
                                "zone": level,
                                "rsi": rsi,
                                "volume_ratio": vol_ratio,
                                "strength": strength,
                            }
                        )
                    break

    for idx, level in support_levels:
        if idx + 1 >= len(df):
            continue
        # Spike below support
        if df["Low"].iloc[idx + 1] < level:
            for j in range(1, lookahead + 1):
                if idx + j >= len(df):
                    break
                if df["Close"].iloc[idx + j] > level:
                    rsi = df["RSI"].iloc[idx + j] if "RSI" in df.columns else None
                    vol_ratio = (
                        df["Volume"].iloc[idx + j] / avg_volume.iloc[idx + j]
                        if avg_volume.iloc[idx + j] > 0
                        else 1.0
                    )

                    rsi_ok = (rsi is None) or (not use_rsi_filter) or (rsi < 45)
                    vol_ok = (not use_volume_filter) or (vol_ratio > 1.0)

                    if rsi_ok and vol_ok:
                        strength = _sweep_strength(rsi, vol_ratio, "buy")
                        sweeps.append(
                            {
                                "type": "buy",
                                "index": idx + j,
                                "price": df["Close"].iloc[idx + j],
                                "zone": level,
                                "rsi": rsi,
                                "volume_ratio": vol_ratio,
                                "strength": strength,
                            }
                        )
                    break

    return sweeps


def _sweep_strength(rsi, vol_ratio, side):
    """Rate signal strength: 'Strong', 'Moderate', 'Weak'."""
    score = 0
    if vol_ratio and vol_ratio > 1.5:
        score += 2
    elif vol_ratio and vol_ratio > 1.0:
        score += 1

    if rsi:
        if side == "sell" and rsi > 70:
            score += 2
        elif side == "sell" and rsi > 60:
            score += 1
        elif side == "buy" and rsi < 30:
            score += 2
        elif side == "buy" and rsi < 40:
            score += 1

    if score >= 3:
        return "Strong"
    elif score >= 1:
        return "Moderate"
    return "Weak"
