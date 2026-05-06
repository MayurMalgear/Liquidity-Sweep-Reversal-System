import yfinance as yf
import pandas as pd

MAX_PERIOD = {
    "5m":  "1mo",
    "15m": "1mo",
    "1h":  "2y",
    "1d":  "5y",
}

INTERVAL_LIMITS = {
    "5m":  "1 Month",
    "15m": "1 Month",
    "1h":  "2 Years",
    "1d":  "5 Years",
}

PERIOD_RANK = {"1mo": 1, "3mo": 2, "6mo": 3, "1y": 4, "2y": 5, "5y": 6}


def fetch_data(ticker: str, period: str = "6mo", interval: str = "1d"):
    max_allowed = MAX_PERIOD.get(interval, "5y")
    capped = False

    if PERIOD_RANK.get(period, 0) > PERIOD_RANK.get(max_allowed, 99):
        period = max_allowed
        capped = True

    raw = yf.download(
        ticker,
        period=period,
        interval=interval,
        auto_adjust=True,
        progress=False,
    )

    if raw.empty:
        raise ValueError(
            f"No data returned for '{ticker}'. "
            "Please check the ticker symbol (e.g. AAPL, BTC-USD, EURUSD=X)."
        )

    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)

    df = raw[["Open", "High", "Low", "Close", "Volume"]].copy()
    df.dropna(inplace=True)
    df.index = pd.to_datetime(df.index)

    return df, capped, period


INTERVAL_OPTIONS = {
    "1 Day":      "1d",
    "1 Hour":     "1h",
    "15 Minutes": "15m",
    "5 Minutes":  "5m",
}

PERIOD_OPTIONS = {
    "1 Month":  "1mo",
    "3 Months": "3mo",
    "6 Months": "6mo",
    "1 Year":   "1y",
    "2 Years":  "2y",
}
