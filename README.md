# Liquidity Sweep Reversal System v2

A fully rebuilt, production-grade Smart Money Concepts trading system with
live data, interactive charts, RSI/volume-confirmed signals, and
comprehensive backtesting.

## What's New vs v1

| Feature | v1 (original) | v2 (this) |
|---|---|---|
| Data source | Static CSV | Live via yfinance |
| Interface | matplotlib (static) | Streamlit web app |
| Charts | Basic 2D/3D | Interactive Plotly |
| Indicators | None | RSI, EMA 20/50/200, ATR, VWAP |
| Signal filter | None | RSI + Volume confirmation |
| Stop loss | Fixed % | ATR-based (dynamic) |
| Backtesting | Win rate + return | Sharpe, Sortino, Calmar, Profit Factor, Drawdown |
| Zone tolerance | Fixed pip | Percentage-based (works any asset) |

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Launch the app
streamlit run app.py
```

Then open http://localhost:8501 in your browser.

## How to Use

1. Enter any ticker in the sidebar: stocks (`AAPL`), crypto (`BTC-USD`), forex (`EURUSD=X`), ETFs (`SPY`)
2. Choose your period and interval
3. Tune detection sensitivity (window, tolerance, lookahead)
4. Toggle RSI and volume filters for signal quality
5. Set your risk/reward and risk % per trade
6. Click **▶ Run Analysis**

## File Structure

```
app.py          — Streamlit UI (main entry point)
data.py         — Live data fetching via yfinance
indicators.py   — RSI, EMA, ATR, VWAP
zones.py        — Liquidity zone detection
detection.py    — Sweep detection with confirmation filters
strategy.py     — ATR-based trade simulation
backtest.py     — Performance metrics
requirements.txt
```

## Disclaimer

This is for educational and research purposes only. Not financial advice.
