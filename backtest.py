import numpy as np
import pandas as pd


def performance_summary(trades: list, equity: list) -> dict:
    """
    Compute comprehensive performance metrics using real dollar P&L.
    """
    if not trades or len(equity) < 2:
        return {}

    equity_arr = np.array(equity, dtype=float)
    starting_capital = equity_arr[0]
    final_equity = equity_arr[-1]

    pnls = [t["pnl"] for t in trades]           # real dollar P&L
    r_multiples = [t["r_multiple"] for t in trades]

    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    breakeven = [p for p in pnls if p == 0]

    win_rate = len(wins) / len(pnls) if pnls else 0
    avg_win = float(np.mean(wins)) if wins else 0.0
    avg_loss = float(abs(np.mean(losses))) if losses else 0.0

    gross_profit = sum(wins)
    gross_loss = abs(sum(losses))
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else float("inf")

    total_return_pct = ((final_equity - starting_capital) / starting_capital) * 100
    total_return_dollar = final_equity - starting_capital

    # Max Drawdown
    running_max = np.maximum.accumulate(equity_arr)
    drawdowns = (running_max - equity_arr) / np.where(running_max > 0, running_max, 1)
    max_drawdown_pct = float(drawdowns.max() * 100)
    max_drawdown_dollar = float((running_max - equity_arr).max())

    # Returns as % of equity for ratio calculations
    returns = np.diff(equity_arr) / equity_arr[:-1]

    # Sharpe Ratio
    if len(returns) > 1 and returns.std() > 0:
        sharpe = float((returns.mean() / returns.std()) * np.sqrt(252))
    else:
        sharpe = 0.0

    # Sortino Ratio
    downside = returns[returns < 0]
    if len(downside) > 1:
        sortino = float((returns.mean() / downside.std()) * np.sqrt(252))
    elif len(downside) == 1:
        sortino = float((returns.mean() / abs(downside[0])) * np.sqrt(252))
    else:
        sortino = float("inf")

    # Calmar Ratio
    calmar = float(total_return_pct / max_drawdown_pct) if max_drawdown_pct > 0 else 0.0

    # Expectancy in dollars
    expectancy_dollar = win_rate * avg_win - (1 - win_rate) * avg_loss

    # Avg R multiple
    avg_r = float(np.mean(r_multiples)) if r_multiples else 0.0

    # Consecutive streaks
    max_wins = _max_streak(pnls, positive=True)
    max_losses = _max_streak(pnls, positive=False)

    def fmt_dollar(v):
        return f"${v:,.2f}"

    def fmt_pct(v):
        return f"{v:.2f}%"

    return {
        "Total Trades": len(trades),
        "Winning Trades": len(wins),
        "Losing Trades": len(losses),
        "Win Rate": fmt_pct(win_rate * 100),
        "Total Return": fmt_pct(total_return_pct),
        "Net Profit": fmt_dollar(total_return_dollar),
        "Final Equity": fmt_dollar(final_equity),
        "Max Drawdown": fmt_pct(max_drawdown_pct),
        "Max Drawdown $": fmt_dollar(max_drawdown_dollar),
        "Profit Factor": f"{profit_factor:.2f}" if profit_factor != float("inf") else "∞",
        "Sharpe Ratio": f"{sharpe:.2f}",
        "Sortino Ratio": f"{sortino:.2f}" if sortino != float("inf") else "∞",
        "Calmar Ratio": f"{calmar:.2f}",
        "Avg Win $": fmt_dollar(avg_win),
        "Avg Loss $": fmt_dollar(avg_loss),
        "Expectancy $": fmt_dollar(expectancy_dollar),
        "Avg R Multiple": f"{avg_r:.2f}R",
        "Max Consec. Wins": max_wins,
        "Max Consec. Losses": max_losses,
    }


def equity_dataframe(equity: list, trades: list) -> pd.DataFrame:
    """Return equity curve as a DataFrame."""
    if not trades or len(equity) < 2:
        return pd.DataFrame()
    dates = [t["entry_date"] for t in trades]
    eq_values = equity[1:]
    length = min(len(dates), len(eq_values))
    return pd.DataFrame({
        "Equity": eq_values[:length],
        "Date": dates[:length],
    }).set_index("Date")


def _max_streak(pnls, positive=True):
    max_s = current = 0
    for p in pnls:
        if (positive and p > 0) or (not positive and p < 0):
            current += 1
            max_s = max(max_s, current)
        else:
            current = 0
    return max_s
