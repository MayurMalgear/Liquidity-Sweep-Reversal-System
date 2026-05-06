import pandas as pd
import numpy as np


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add RSI, EMA(20/50/200), ATR, and VWAP to the DataFrame."""
    df = df.copy()

    # ── RSI (14) ──────────────────────────────────────────────────────────────
    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=13, adjust=False).mean()
    avg_loss = loss.ewm(com=13, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    df["RSI"] = 100 - (100 / (1 + rs))

    # ── EMAs ──────────────────────────────────────────────────────────────────
    df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
    df["EMA50"] = df["Close"].ewm(span=50, adjust=False).mean()
    df["EMA200"] = df["Close"].ewm(span=200, adjust=False).mean()

    # ── ATR (14) ──────────────────────────────────────────────────────────────
    high_low = df["High"] - df["Low"]
    high_prev = (df["High"] - df["Close"].shift(1)).abs()
    low_prev = (df["Low"] - df["Close"].shift(1)).abs()
    tr = pd.concat([high_low, high_prev, low_prev], axis=1).max(axis=1)
    df["ATR"] = tr.rolling(14).mean()

    # ── VWAP (rolling session approximation) ──────────────────────────────────
    typical_price = (df["High"] + df["Low"] + df["Close"]) / 3
    df["VWAP"] = (typical_price * df["Volume"]).cumsum() / df["Volume"].cumsum()

    return df
