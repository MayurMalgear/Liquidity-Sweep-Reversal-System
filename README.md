# Liquidity Sweep Reversal System

A Python-based algorithmic trading system implementing **Smart Money Concepts (SMC)** for detecting and trading institutional liquidity sweeps. The system ingests live market data, identifies high-probability reversal setups, applies dynamic position sizing, and produces a comprehensive backtest report with professional-grade performance metrics.

---

![Dashboard](screenshots/dashboard.png)

---

## Table of Contents

- [Overview](#overview)
- [Strategy Logic](#strategy-logic)
- [System Architecture](#system-architecture)
- [Screenshots](#screenshots)
- [Installation](#installation)
- [Usage](#usage)
- [Valid Timeframe Combinations](#valid-timeframe-combinations)
- [Parameter Reference](#parameter-reference)
- [Performance Benchmarks](#performance-benchmarks)
- [File Structure](#file-structure)
- [Tech Stack](#tech-stack)
- [Roadmap](#roadmap)
- [Disclaimer](#disclaimer)

---

## Overview

Institutional participants — banks, hedge funds, and proprietary trading desks — systematically engineer liquidity events by driving price through retail stop-loss clusters before reversing. This system identifies those events in real time, filters them through RSI and volume confirmation, and backtests a reversal strategy with fixed-fractional position sizing and ATR-derived stop levels.

**Core capabilities:**
- Live OHLCV data ingestion via Yahoo Finance (equities, crypto, forex, ETFs)
- Percentage-tolerance liquidity zone detection that works across any asset class and price range
- Multi-condition signal confirmation (price action + RSI + volume)
- Signal strength classification: Strong, Moderate, Weak
- ATR-based dynamic stop loss (adapts to realised volatility)
- Fixed fractional position sizing (risk compounds with equity growth)
- Real dollar P&L simulation with configurable starting capital
- Full performance suite: Sharpe ratio, Sortino ratio, Calmar ratio, profit factor, max drawdown, expectancy

---

## Strategy Logic

### 1. Liquidity Zone Identification

Equal highs and equal lows are identified using a rolling window approach with percentage-based price tolerance. Zones that have been tested multiple times are rated higher quality. This method is asset-agnostic — it produces valid zones on a $1 asset and a $50,000 asset without parameter changes.

### 2. Sweep Detection

A sweep is defined as:
- Price breaching a zone (intrabar)
- Closing back inside the zone within a configurable lookahead window

This identifies the classic stop-hunt pattern: price briefly violates a structural level to trigger resting orders, then reverses as the institutional order is filled.

### 3. Signal Confirmation

Raw sweeps are filtered by:

| Filter | Sell Sweep Condition | Buy Sweep Condition |
|--------|----------------------|---------------------|
| RSI (14) | > 55 (overbought exhaustion) | < 45 (oversold exhaustion) |
| Volume | Above 20-period rolling average | Above 20-period rolling average |

Both filters can be toggled independently for sensitivity analysis.

### 4. Trade Execution Model

```
Entry:   Close of the reversal candle
Stop:    Entry ± (ATR × 1.5)
Target:  Entry ∓ (Stop distance × Risk/Reward ratio)
```

If neither stop nor target is hit before the data ends, the trade is closed at the final bar's closing price and P&L is calculated proportionally.

### 5. Position Sizing — Fixed Fractional

```
Dollar Risk  = Current Equity × Risk %
Shares       = Dollar Risk / Stop Distance per Share
```

Position size scales with account equity, providing natural drawdown protection and return compounding.

---

## System Architecture

```
Yahoo Finance (yfinance)
        |
        v
   data.py          -- OHLCV ingestion, period validation, auto-capping
        |
        v
indicators.py        -- RSI, EMA 20/50/200, ATR, VWAP
        |
        v
   zones.py          -- Liquidity zone detection (equal highs/lows)
        |
        v
 detection.py        -- Sweep identification + RSI/volume filtering
        |
        v
 strategy.py         -- Trade simulation, position sizing, real dollar P&L
        |
        v
 backtest.py         -- Performance metrics computation
        |
        v
   app.py            -- Streamlit dashboard (charts, signals, report)
```

---

## Screenshots

The following screenshots should be taken with the app running on `AAPL`, `1 Day` interval, `6 Months` period, default settings.

| File | Content |
|------|---------|
| `screenshots/dashboard.png` | Full application view — sidebar, KPI row, and candlestick chart with zone lines and sweep markers visible |
| `screenshots/chart.png` | Zoomed chart section clearly showing horizontal zone lines, buy/sell triangles, and EMA overlays |
| `screenshots/signals.png` | Active Signals tab with 2-3 expanded signal cards showing RSI, volume ratio, and strength classification |
| `screenshots/backtest.png` | Backtest Report tab showing the performance summary grid and dual-panel equity curve |

**To capture on Windows:** `Win + Shift + S`, drag to select area, paste into Paint and save as `.png`.

Create a `screenshots/` directory in the project root and save all four images with the exact filenames listed above.

---

## Installation

**Requires Python 3.10+**

```bash
git clone https://github.com/YOURUSERNAME/liquidity-sweep-reversal-system.git
cd liquidity-sweep-reversal-system
pip install -r requirements.txt
python -m streamlit run app.py
```

Navigate to `http://localhost:8501` in your browser.

---

## Usage

1. Enter a ticker symbol in the sidebar (`AAPL`, `BTC-USD`, `EURUSD=X`, `SPY`)
2. Select a valid period and interval (see table below)
3. Set your starting capital for the demo account simulation
4. Configure detection parameters and strategy settings
5. Toggle RSI and volume confirmation filters as required
6. Click **Run Analysis**

Results are presented across three tabs:

- **Chart** — candlestick chart with liquidity zones, sweep signals, and indicator overlays
- **Active Signals** — ranked signal list with RSI, volume ratio, and strength classification
- **Backtest Report** — performance summary, dual equity curve, trade log, P&L distribution

---

## Valid Timeframe Combinations

Yahoo Finance restricts intraday data availability. The application automatically caps the period if an invalid combination is selected and displays a warning.

| Interval | 1 Month | 3 Months | 6 Months | 1 Year | 2 Years |
|----------|:-------:|:--------:|:--------:|:------:|:-------:|
| 5 Minutes | Yes | No | No | No | No |
| 15 Minutes | Yes | No | No | No | No |
| 1 Hour | Yes | Yes | Yes | Yes | Yes |
| 1 Day | Yes | Yes | Yes | Yes | Yes |

### Recommended Combinations

| Use Case | Interval | Period |
|----------|----------|--------|
| Intraday / scalping | 5 min or 15 min | 1 Month |
| Short-term swing | 1 Hour | 1–3 Months |
| Medium-term swing | 1 Day | 3–6 Months |
| Position trading | 1 Day | 1–2 Years |
| General starting point | 1 Day | 6 Months |

---

## Parameter Reference

### Detection Parameters

| Parameter | Description | Default | Effect of Increase |
|-----------|-------------|---------|-------------------|
| Zone Window | Bars on each side used to identify equal highs/lows | 10 | Fewer, higher-quality zones |
| Zone Tolerance | Price proximity threshold (%) for zone matching | 0.3% | More zones detected |
| Sweep Lookahead | Bars allowed for price to reverse after breach | 3 | More sweeps captured, higher noise risk |

### Strategy Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| Starting Capital | Demo account size in USD | $10,000 |
| Risk per Trade | Percentage of current equity risked per trade | 1% |
| Risk / Reward | Target as a multiple of stop distance | 2.0 |

### Recommended Settings by Asset Class

| Asset Class | Zone Window | Tolerance | Lookahead | Risk/Reward |
|-------------|-------------|-----------|-----------|-------------|
| Equities | 10–15 | 0.3% | 3 | 2.0 |
| Crypto | 8–12 | 0.5% | 4 | 2.5 |
| Forex | 8–10 | 0.2% | 3 | 1.5 |
| Indices / ETFs | 15–20 | 0.3% | 3 | 2.0 |

---

## Performance Benchmarks

The following thresholds are used to evaluate backtest quality. Results below the minimum threshold indicate the parameter set requires adjustment.

| Metric | Minimum | Target | Strong |
|--------|---------|--------|--------|
| Win Rate | 40% | 50% | 60%+ |
| Profit Factor | 1.2 | 1.5 | 2.0+ |
| Sharpe Ratio | 0.5 | 1.0 | 1.5+ |
| Sortino Ratio | 0.7 | 1.2 | 2.0+ |
| Max Drawdown | < 30% | < 20% | < 10% |
| Expectancy | > $0 | > $50 | > $100 |

---

## File Structure

```
liquidity-sweep-reversal-system/
|
|-- app.py              Streamlit dashboard — charts, signals, backtest report
|-- data.py             Yahoo Finance ingestion with interval-based period capping
|-- indicators.py       RSI (14), EMA 20/50/200, ATR (14), VWAP
|-- zones.py            Percentage-tolerance liquidity zone detection
|-- detection.py        Sweep identification with RSI and volume filters
|-- strategy.py         Trade simulation, fixed fractional sizing, real dollar P&L
|-- backtest.py         Sharpe, Sortino, Calmar, profit factor, drawdown, expectancy
|-- requirements.txt    Python dependencies
|-- screenshots/        Application screenshots for documentation
|-- README.md
```

---

## Tech Stack

| Library | Version | Purpose |
|---------|---------|---------|
| streamlit | >= 1.35 | Web dashboard and UI |
| plotly | >= 5.20 | Interactive charts and equity curve |
| yfinance | >= 0.2.40 | Live OHLCV data from Yahoo Finance |
| pandas | >= 2.0 | Data manipulation and trade log |
| numpy | >= 1.26 | Vectorised numerical computation |

---

## Roadmap

The following enhancements are planned for future development:

- Order Block detection — identify institutional supply and demand zones
- Fair Value Gap (FVG) identification — locate unfilled price inefficiencies
- Break of Structure (BOS) classification — confirm trend continuation or reversal
- Multi-timeframe confluence — higher timeframe trend filter on lower timeframe entries
- Live alerting — Telegram and email notifications on signal generation
- ML-based signal scoring — Random Forest or XGBoost classifier for signal quality prediction
- Portfolio-level backtesting — simultaneous testing across multiple instruments
- Walk-forward optimisation — out-of-sample validation to prevent overfitting
- Paper trading integration — live forward testing via Alpaca or Binance API
- Persistent storage — SQLite database for saving and comparing backtest runs

---

## Disclaimer

This project is intended for **educational and research purposes only**. Nothing in this repository constitutes financial or investment advice. Past backtest performance is not indicative of future results. Always conduct independent research before making any trading or investment decisions.

---

*Python · Smart Money Concepts · Algorithmic Trading · Quantitative Analysis*
