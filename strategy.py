import pandas as pd
import numpy as np


def run_strategy(
    df: pd.DataFrame,
    sweeps: list,
    rr: float = 2.0,
    risk_pct: float = 0.01,
    starting_capital: float = 10000.0,
):
    """
    Simulate trades with real dollar P&L and dynamic position sizing.

    Position sizing method: Fixed Fractional Risk
      - Risk exactly X% of CURRENT equity on every trade
      - Shares = (Equity * risk_pct) / stop_distance_per_share
      - This compounds correctly — account grows faster during winning streaks
        and automatically reduces size during drawdowns

    Returns:
        trades:  list of trade dicts with real dollar P&L
        equity:  list of equity values in dollars (starts at starting_capital)
    """
    trades = []
    equity = [starting_capital]
    current_equity = starting_capital

    for signal in sweeps:
        entry_idx = signal["index"]
        entry_price = float(signal["price"])
        zone = float(signal["zone"])

        # ── Stop distance ──────────────────────────────────────────────────────
        atr = df["ATR"].iloc[entry_idx] if "ATR" in df.columns else None
        atr = float(atr) if atr is not None and not np.isnan(atr) else None

        fallback_stop_dist = abs(entry_price - zone) * 1.2
        if fallback_stop_dist < entry_price * 0.001:
            fallback_stop_dist = entry_price * 0.001

        stop_dist = (atr * 1.5) if atr else fallback_stop_dist
        stop_dist = max(stop_dist, entry_price * 0.001)  # min 0.1%

        # ── Stop / Target prices ───────────────────────────────────────────────
        if signal["type"] == "sell":
            stop = entry_price + stop_dist
            target = entry_price - rr * stop_dist
        else:
            stop = entry_price - stop_dist
            target = entry_price + rr * stop_dist

        # ── Position sizing: Fixed Fractional ─────────────────────────────────
        # Dollar risk = how much $ we're willing to lose on this trade
        dollar_risk = current_equity * risk_pct
        # Shares = dollar risk / risk per share
        shares = dollar_risk / stop_dist
        shares = max(round(shares, 4), 0.0001)  # minimum viable position

        # ── Simulate the trade ─────────────────────────────────────────────────
        exit_price, exit_reason = _simulate_trade(
            df, entry_idx, entry_price, stop, target, signal["type"]
        )

        # ── Actual P&L in dollars ──────────────────────────────────────────────
        if signal["type"] == "sell":
            raw_pnl = (entry_price - exit_price) * shares
        else:
            raw_pnl = (exit_price - entry_price) * shares

        # R multiple for reference (how many R did this trade return)
        r_multiple = raw_pnl / dollar_risk if dollar_risk > 0 else 0.0
        r_multiple = round(max(-1.0, min(r_multiple, rr + 0.1)), 3)

        current_equity = max(current_equity + raw_pnl, 0.01)
        equity.append(round(current_equity, 2))

        trades.append({
            "type": signal["type"],
            "entry_idx": entry_idx,
            "entry_date": df.index[entry_idx],
            "entry": round(entry_price, 4),
            "exit": round(exit_price, 4),
            "stop": round(stop, 4),
            "target": round(target, 4),
            "shares": round(shares, 4),
            "dollar_risk": round(dollar_risk, 2),
            "pnl": round(raw_pnl, 2),         # real dollar P&L
            "r_multiple": r_multiple,           # R multiple for reference
            "exit_reason": exit_reason,         # "Stop", "Target", "Open"
            "zone": zone,
            "rsi": signal.get("rsi"),
            "volume_ratio": signal.get("volume_ratio"),
            "strength": signal.get("strength", "—"),
        })

    return trades, equity


def _simulate_trade(df, entry_idx, entry_price, stop, target, side):
    """
    Walk forward bar by bar until stop or target is hit.
    Returns (exit_price, exit_reason).
    """
    for i in range(entry_idx + 1, len(df)):
        high = float(df["High"].iloc[i])
        low = float(df["Low"].iloc[i])

        if side == "sell":
            if high >= stop:
                return stop, "Stop"
            if low <= target:
                return target, "Target"
        else:
            if low <= stop:
                return stop, "Stop"
            if high >= target:
                return target, "Target"

    # Trade still open — close at last price
    last_close = float(df["Close"].iloc[-1])
    return last_close, "Open"
