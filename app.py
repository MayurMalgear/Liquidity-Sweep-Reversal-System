import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from data import fetch_data, INTERVAL_OPTIONS, PERIOD_OPTIONS
from indicators import add_indicators
from zones import find_liquidity_zones
from detection import detect_sweeps
from strategy import run_strategy
from backtest import performance_summary, equity_dataframe

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Liquidity Sweep Reversal System",
    page_icon="📈",
    layout="wide",
)

st.title("📈 Liquidity Sweep Reversal System")
st.caption("Smart Money Concepts · Live Data · Interactive Analysis")

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Settings")

    ticker = st.text_input("Ticker Symbol", value="AAPL", help="e.g. AAPL, BTC-USD, EURUSD=X, SPY")

    col1, col2 = st.columns(2)
    with col1:
        period_label = st.selectbox("Period", list(PERIOD_OPTIONS.keys()), index=2)
    with col2:
        interval_label = st.selectbox("Interval", list(INTERVAL_OPTIONS.keys()), index=0)

    st.divider()
    st.subheader("🔍 Detection")
    window = st.slider("Zone Window (bars)", 3, 30, 10)
    tolerance = st.slider("Zone Tolerance (%)", 0.1, 1.0, 0.3, step=0.05) / 100
    lookahead = st.slider("Sweep Lookahead (bars)", 1, 10, 3)
    use_rsi_filter = st.toggle("RSI Confirmation", value=True)
    use_vol_filter = st.toggle("Volume Confirmation", value=True)

    st.divider()
    st.subheader("💰 Strategy")
    starting_capital = st.number_input(
        "Starting Capital ($)", min_value=100, max_value=10_000_000,
        value=10_000, step=1000,
        help="Your demo account size in dollars"
    )
    rr = st.slider("Risk : Reward", 1.0, 5.0, 2.0, step=0.5)
    risk_pct = st.slider("Risk per Trade (%)", 0.5, 5.0, 1.0, step=0.5) / 100

    st.divider()
    st.subheader("📊 Chart Display")
    show_ema20 = st.toggle("EMA 20", value=True)
    show_ema50 = st.toggle("EMA 50", value=True)
    show_ema200 = st.toggle("EMA 200", value=False)
    show_vwap = st.toggle("VWAP", value=False)

    run_btn = st.button("▶ Run Analysis", type="primary", use_container_width=True)

# ── Load & process data ───────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_and_process(ticker, period, interval, window, tolerance, lookahead,
                     use_rsi, use_vol, rr, risk_pct, starting_capital):
    df, capped, used_period = fetch_data(ticker, period=period, interval=interval)
    df = add_indicators(df)
    resistance, support = find_liquidity_zones(df, window=window, tolerance_pct=tolerance)
    sweeps = detect_sweeps(df, resistance, support, lookahead=lookahead,
                           use_rsi_filter=use_rsi, use_volume_filter=use_vol)
    trades, equity = run_strategy(df, sweeps, rr=rr, risk_pct=risk_pct,
                                  starting_capital=starting_capital)
    stats = performance_summary(trades, equity)
    return df, resistance, support, sweeps, trades, equity, stats, capped, used_period


if run_btn or "df" not in st.session_state:
    if run_btn:
        load_and_process.clear()
    with st.spinner(f"Fetching {ticker} data…"):
        try:
            period = PERIOD_OPTIONS[period_label]
            interval = INTERVAL_OPTIONS[interval_label]
            (st.session_state.df, st.session_state.resistance,
             st.session_state.support, st.session_state.sweeps,
             st.session_state.trades, st.session_state.equity,
             st.session_state.stats,
             st.session_state.capped,
             st.session_state.used_period) = load_and_process(
                ticker, period, interval, window, tolerance, lookahead,
                use_rsi_filter, use_vol_filter, rr, risk_pct, starting_capital
            )
            st.session_state.ticker = ticker
        except Exception as e:
            st.error(f"❌ {e}")
            st.stop()

df = st.session_state.df
resistance = st.session_state.resistance
support = st.session_state.support
sweeps = st.session_state.sweeps
trades = st.session_state.trades
equity = st.session_state.equity
stats = st.session_state.stats
disp_ticker = st.session_state.get("ticker", ticker)

# Show warning if period was automatically capped
if st.session_state.get("capped"):
    from data import INTERVAL_LIMITS
    interval_val = INTERVAL_OPTIONS[interval_label]
    st.warning(
        f"⚠️ Yahoo Finance only allows **{INTERVAL_LIMITS.get(interval_val, '60 days')}** "
        f"of data for the **{interval_label}** interval. "
        f"Period has been automatically adjusted."
    )

# ── KPI row ───────────────────────────────────────────────────────────────────
if stats:
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("Total Trades", stats.get("Total Trades", 0))
    k2.metric("Win Rate", stats.get("Win Rate", "—"))
    k3.metric("Total Return", stats.get("Total Return", "—"))
    k4.metric("Max Drawdown", stats.get("Max Drawdown", "—"))
    k5.metric("Sharpe Ratio", stats.get("Sharpe Ratio", "—"))
    k6.metric("Profit Factor", stats.get("Profit Factor", "—"))

st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_chart, tab_signals, tab_backtest = st.tabs(["📊 Chart", "🚨 Active Signals", "📋 Backtest Report"])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — CHART
# ═══════════════════════════════════════════════════════════════════════════════
with tab_chart:
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        row_heights=[0.6, 0.2, 0.2],
        vertical_spacing=0.03,
        subplot_titles=(f"{disp_ticker} Price", "Volume", "RSI (14)"),
    )

    # Candlesticks
    fig.add_trace(
        go.Candlestick(
            x=df.index, open=df["Open"], high=df["High"],
            low=df["Low"], close=df["Close"],
            name="Price",
            increasing_line_color="#26a69a",
            decreasing_line_color="#ef5350",
        ),
        row=1, col=1,
    )

    # EMAs
    if show_ema20:
        fig.add_trace(go.Scatter(x=df.index, y=df["EMA20"], name="EMA 20",
                                 line=dict(color="#f5a623", width=1.2)), row=1, col=1)
    if show_ema50:
        fig.add_trace(go.Scatter(x=df.index, y=df["EMA50"], name="EMA 50",
                                 line=dict(color="#7b68ee", width=1.2)), row=1, col=1)
    if show_ema200:
        fig.add_trace(go.Scatter(x=df.index, y=df["EMA200"], name="EMA 200",
                                 line=dict(color="#ff6b6b", width=1.5, dash="dot")), row=1, col=1)
    if show_vwap:
        fig.add_trace(go.Scatter(x=df.index, y=df["VWAP"], name="VWAP",
                                 line=dict(color="#00bcd4", width=1.2, dash="dash")), row=1, col=1)

    # Resistance zones
    for idx, level in resistance:
        fig.add_hline(y=level, line=dict(color="rgba(239,83,80,0.35)", width=1, dash="dot"),
                      row=1, col=1)

    # Support zones
    for idx, level in support:
        fig.add_hline(y=level, line=dict(color="rgba(38,166,154,0.35)", width=1, dash="dot"),
                      row=1, col=1)

    # Sweep markers
    for s in sweeps:
        color = "#ef5350" if s["type"] == "sell" else "#26a69a"
        symbol = "triangle-down" if s["type"] == "sell" else "triangle-up"
        label = f"{'SELL' if s['type']=='sell' else 'BUY'} Sweep<br>RSI: {s['rsi']:.1f}" \
                f"<br>Vol: {s['volume_ratio']:.1f}x<br>Strength: {s['strength']}" \
                if s['rsi'] else f"{'SELL' if s['type']=='sell' else 'BUY'} Sweep"
        fig.add_trace(
            go.Scatter(
                x=[df.index[s["index"]]],
                y=[s["price"]],
                mode="markers",
                marker=dict(symbol=symbol, size=14, color=color, line=dict(width=1, color="white")),
                name=f"{s['type'].upper()} sweep",
                text=label,
                hovertemplate="%{text}<extra></extra>",
                showlegend=False,
            ),
            row=1, col=1,
        )

    # Trade entry/exit markers
    for t in trades:
        color = "#26a69a" if t["type"] == "buy" else "#ef5350"
        fig.add_trace(
            go.Scatter(
                x=[t["entry_date"]],
                y=[t["entry"]],
                mode="markers",
                marker=dict(symbol="circle", size=8, color=color, opacity=0.7),
                hovertemplate=f"{t['type'].upper()} @ {t['entry']:.4f}<br>PnL: {t['pnl']:.1f}R<extra></extra>",
                showlegend=False,
            ),
            row=1, col=1,
        )

    # Volume bars
    vol_colors = ["#26a69a" if c >= o else "#ef5350"
                  for c, o in zip(df["Close"], df["Open"])]
    fig.add_trace(
        go.Bar(x=df.index, y=df["Volume"], name="Volume",
               marker_color=vol_colors, showlegend=False),
        row=2, col=1,
    )

    # RSI
    fig.add_trace(
        go.Scatter(x=df.index, y=df["RSI"], name="RSI",
                   line=dict(color="#7b68ee", width=1.5)),
        row=3, col=1,
    )
    fig.add_hline(y=70, line=dict(color="rgba(239,83,80,0.5)", dash="dash"), row=3, col=1)
    fig.add_hline(y=30, line=dict(color="rgba(38,166,154,0.5)", dash="dash"), row=3, col=1)
    fig.add_hrect(y0=70, y1=100, fillcolor="rgba(239,83,80,0.05)", row=3, col=1, line_width=0)
    fig.add_hrect(y0=0, y1=30, fillcolor="rgba(38,166,154,0.05)", row=3, col=1, line_width=0)

    fig.update_layout(
        height=750,
        template="plotly_dark",
        xaxis_rangeslider_visible=False,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=0, r=0, t=30, b=0),
        hovermode="x unified",
    )
    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)
    fig.update_yaxes(title_text="RSI", row=3, col=1, range=[0, 100])

    st.plotly_chart(fig, use_container_width=True)

    col_r, col_s = st.columns(2)
    col_r.metric("Resistance Zones Found", len(resistance))
    col_s.metric("Support Zones Found", len(support))

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — ACTIVE SIGNALS
# ═══════════════════════════════════════════════════════════════════════════════
with tab_signals:
    st.subheader("🚨 Latest Sweep Signals")

    if not sweeps:
        st.info("No sweep signals detected. Try adjusting window or tolerance in the sidebar.")
    else:
        # Show most recent signals first
        recent = sorted(sweeps, key=lambda x: x["index"], reverse=True)

        for s in recent[:10]:
            date = df.index[s["index"]]
            color = "🔴" if s["type"] == "sell" else "🟢"
            strength_badge = {"Strong": "🔥 Strong", "Moderate": "⚡ Moderate", "Weak": "💤 Weak"}.get(
                s["strength"], s["strength"]
            )
            with st.expander(f"{color} **{s['type'].upper()} Sweep** — {date.strftime('%Y-%m-%d')}  |  {strength_badge}", expanded=(s == recent[0])):
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Entry Price", f"{s['price']:.4f}")
                c2.metric("Zone Level", f"{s['zone']:.4f}")
                c3.metric("RSI", f"{s['rsi']:.1f}" if s["rsi"] else "—")
                c4.metric("Volume Ratio", f"{s['volume_ratio']:.1f}x" if s["volume_ratio"] else "—")

                action = "SHORT (Sell)" if s["type"] == "sell" else "LONG (Buy)"
                st.info(f"**Signal:** {action} — Price reversed from {'resistance' if s['type']=='sell' else 'support'} zone after sweep.")

        # Latest signal alert box
        latest = recent[0]
        latest_date = df.index[latest["index"]]
        if latest["index"] == len(df) - 1 or latest["index"] == len(df) - 2:
            st.success(
                f"⚡ **FRESH SIGNAL on {latest_date.strftime('%Y-%m-%d')}:** "
                f"{latest['type'].upper()} sweep at {latest['price']:.4f} — "
                f"Strength: {latest['strength']}"
            )

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — BACKTEST REPORT
# ═══════════════════════════════════════════════════════════════════════════════
with tab_backtest:
    if not trades:
        st.info("No trades to report. Signals may be filtered out — try loosening RSI/volume filters.")
    else:
        st.subheader("📋 Performance Summary")

        # Stats grid — 3 columns
        col_a, col_b, col_c = st.columns(3)
        items = list(stats.items())
        third = len(items) // 3
        with col_a:
            for k, v in items[:third]:
                st.metric(k, v)
        with col_b:
            for k, v in items[third:third*2]:
                st.metric(k, v)
        with col_c:
            for k, v in items[third*2:]:
                st.metric(k, v)

        st.divider()

        # ── Equity Curve ──────────────────────────────────────────────────────
        st.subheader("💹 Equity Curve")
        eq_df = equity_dataframe(equity, trades)
        if not eq_df.empty:
            start_cap = float(equity[0])
            final_cap = float(equity[-1])
            line_color = "#26a69a" if final_cap >= start_cap else "#ef5350"
            fill_color = "rgba(38,166,154,0.1)" if final_cap >= start_cap else "rgba(239,83,80,0.1)"

            fig_eq = make_subplots(
                rows=2, cols=1,
                shared_xaxes=True,
                row_heights=[0.65, 0.35],
                vertical_spacing=0.06,
                subplot_titles=("Account Value ($)", "Return (%)"),
            )

            # Top — dollar equity
            fig_eq.add_trace(
                go.Scatter(
                    x=eq_df.index, y=eq_df["Equity"],
                    fill="tozeroy",
                    line=dict(color=line_color, width=2),
                    fillcolor=fill_color,
                    name="Equity $",
                    hovertemplate="%{x}<br>Account: $%{y:,.2f}<extra></extra>",
                ),
                row=1, col=1,
            )
            fig_eq.add_hline(y=start_cap, line=dict(color="white", dash="dash", width=1), row=1, col=1)

            # Bottom — % return
            pct_return = ((eq_df["Equity"] - start_cap) / start_cap) * 100
            fig_eq.add_trace(
                go.Bar(
                    x=eq_df.index,
                    y=pct_return,
                    marker_color=[line_color if v >= 0 else "#ef5350" for v in pct_return],
                    name="Return %",
                    hovertemplate="%{x}<br>Return: %{y:.2f}%<extra></extra>",
                ),
                row=2, col=1,
            )
            fig_eq.add_hline(y=0, line=dict(color="white", dash="dash", width=1), row=2, col=1)

            fig_eq.update_layout(
                template="plotly_dark", height=420,
                margin=dict(l=0, r=0, t=30, b=0),
                showlegend=False,
            )
            fig_eq.update_yaxes(title_text="Account ($)", tickprefix="$", row=1, col=1)
            fig_eq.update_yaxes(title_text="Return (%)", ticksuffix="%", row=2, col=1)
            st.plotly_chart(fig_eq, use_container_width=True)
        else:
            st.info("Not enough trades to draw equity curve.")

        st.divider()

        # ── Trade Log ─────────────────────────────────────────────────────────
        st.subheader("📝 Trade Log")
        trade_cols = ["entry_date", "type", "entry", "exit", "stop", "target",
                      "shares", "dollar_risk", "pnl", "r_multiple", "exit_reason", "strength"]
        # Only include columns that exist (backward compat)
        available = [c for c in trade_cols if c in trades[0]]
        trade_df = pd.DataFrame(trades)[available].copy()

        rename_map = {
            "entry_date": "Date", "type": "Type", "entry": "Entry",
            "exit": "Exit", "stop": "Stop", "target": "Target",
            "shares": "Shares", "dollar_risk": "Risk ($)",
            "pnl": "P&L ($)", "r_multiple": "R", "exit_reason": "Result", "strength": "Strength"
        }
        trade_df.rename(columns={k: v for k, v in rename_map.items() if k in trade_df.columns}, inplace=True)
        trade_df["Date"] = pd.to_datetime(trade_df["Date"]).dt.strftime("%Y-%m-%d")

        def color_pnl(val):
            try:
                color = "#26a69a" if float(val) > 0 else "#ef5350"
                return f"color: {color}"
            except:
                return ""

        style_cols = ["P&L ($)", "R"] if "P&L ($)" in trade_df.columns else []
        styled = trade_df.style
        for col in style_cols:
            if col in trade_df.columns:
                styled = styled.map(color_pnl, subset=[col])

        st.dataframe(styled, use_container_width=True, hide_index=True)

        st.divider()

        # ── P&L Distribution ──────────────────────────────────────────────────
        st.subheader("📊 P&L Distribution")
        pnl_col = "pnl" if "pnl" in trades[0] else "r_multiple"
        pnls_dollar = [t[pnl_col] for t in trades]

        fig_dist = make_subplots(
            rows=1, cols=2,
            subplot_titles=("P&L in Dollars ($)", "P&L in R Multiples"),
            horizontal_spacing=0.1,
        )

        # Dollar P&L histogram
        fig_dist.add_trace(
            go.Histogram(
                x=pnls_dollar,
                nbinsx=15,
                marker_color=["#26a69a" if p > 0 else "#ef5350" for p in pnls_dollar],
                name="P&L $",
                hovertemplate="P&L: $%{x:.2f}<br>Count: %{y}<extra></extra>",
            ),
            row=1, col=1,
        )
        fig_dist.add_vline(x=0, line=dict(color="white", dash="dash"), row=1, col=1)

        # R multiple histogram
        r_vals = [t.get("r_multiple", t.get("pnl", 0)) for t in trades]
        fig_dist.add_trace(
            go.Histogram(
                x=r_vals,
                nbinsx=15,
                marker_color=["#26a69a" if r > 0 else "#ef5350" for r in r_vals],
                name="R Multiple",
                hovertemplate="R: %{x:.2f}<br>Count: %{y}<extra></extra>",
            ),
            row=1, col=2,
        )
        fig_dist.add_vline(x=0, line=dict(color="white", dash="dash"), row=1, col=2)

        fig_dist.update_layout(
            template="plotly_dark", height=320,
            margin=dict(l=0, r=0, t=30, b=0),
            showlegend=False,
        )
        fig_dist.update_xaxes(title_text="P&L ($)", tickprefix="$", row=1, col=1)
        fig_dist.update_xaxes(title_text="R Multiple", row=1, col=2)
        fig_dist.update_yaxes(title_text="Count", row=1, col=1)
        st.plotly_chart(fig_dist, use_container_width=True)

