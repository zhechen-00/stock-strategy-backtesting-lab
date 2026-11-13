"""Simple stock and index buy-and-hold comparison for a programming class."""
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

from backtest import run_backtest

st.set_page_config(page_title="Stock Strategy Backtesting Lab", layout="centered")
st.title("Stock Strategy Backtesting Lab")
st.write("Explore historical prices and compare Buy and Hold with a simple moving-average strategy.")

# The original classroom examples are stored locally. Additional markets use
# actual historical prices retrieved from Yahoo Finance.
LOCAL_FILE = Path(__file__).parent / "data" / "plotly_weekly_stocks_2018_2019.csv"
ASSETS = {
    "Taiwan 50 ETF (0050)": ("0050.TW", "ETF"),
    "Taiwan 50 2x ETF (00631L)": ("00631L.TW", "Leveraged ETF"),
    "S&P 500 Index": ("^GSPC", "Index"),
    "Nasdaq 100 ETF (QQQ)": ("QQQ", "ETF"),
    "Philadelphia Semiconductor Index (SOX)": ("^SOX", "Index"),
    "Apple (AAPL) - sample": ("AAPL", "Local sample"),
    "Microsoft (MSFT) - sample": ("MSFT", "Local sample"),
    "Google (GOOG) - sample": ("GOOG", "Local sample"),
    "Amazon (AMZN) - sample": ("AMZN", "Local sample"),
}


@st.cache_data(ttl=3600, show_spinner=False)
def get_prices(symbol, kind):
    """Return one weekly historical closing-price series."""
    if kind == "Local sample":
        data = pd.read_csv(LOCAL_FILE, parse_dates=["date"])
        return pd.Series(data[symbol].to_numpy(dtype=float), index=data["date"], name=symbol)

    # auto_adjust=True adjusts ETF prices for distributions and splits where
    # Yahoo provides adjustments. It does NOT turn a price index into a
    # dividend-reinvested total-return index.
    history = yf.download(
        symbol, period="5y", interval="1wk", auto_adjust=True,
        progress=False, threads=False
    )
    if history.empty:
        raise ValueError("No historical prices were returned by Yahoo Finance.")
    close = history["Close"]
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]
    close = pd.to_numeric(close, errors="coerce").dropna()
    close.index = pd.to_datetime(close.index).tz_localize(None)
    close = close[~close.index.duplicated(keep="last")].sort_index()
    if len(close) < 25:
        raise ValueError("Not enough valid weekly prices for the comparison.")
    return close.rename(symbol)


st.subheader("1. Select a stock or index")
selected = st.selectbox("Stock or index", ASSETS, index=0)
symbol, kind = ASSETS[selected]
st.write("Ticker:", symbol)
if kind == "Local sample":
    st.caption("Offline teaching sample: 2018-2019 weekly normalized historical prices.")
else:
    st.caption("Source: Yahoo Finance historical weekly prices, approximately the last five years. Prices are not live quotes.")

try:
    with st.spinner("Loading historical prices..."):
        prices = get_prices(symbol, kind)
except Exception as exc:
    st.error("Historical data could not be loaded. Please try again later or select an offline sample.")
    st.caption(f"Data issue: {type(exc).__name__}: {exc}")
    st.stop()

st.write(f"Available dates: {prices.index.min():%Y-%m-%d} to {prices.index.max():%Y-%m-%d}")

st.subheader("2. Choose a strategy")
strategy = st.radio(
    "Display", ["Buy and Hold only", "Compare with Moving Average"],
    horizontal=True
)
st.caption("Buy and Hold means investing once and staying invested. Moving Average uses fixed 4-week and 16-week averages.")

# All curves start from a hypothetical 10,000 units of portfolio value.
# This avoids confusing Taiwan dollars, US dollars, and index points.
settings = {"periods_per_year": 52, "cost_bps": 10, "start_cash": 10000}
buy_hold = run_backtest(prices, "Buy & hold", **settings)
results = {"Buy and Hold": buy_hold}
if strategy == "Compare with Moving Average":
    results["Moving Average"] = run_backtest(
        prices, "Moving-average crossover", fast=4, slow=16, **settings
    )

st.subheader("3. Backtest results")
rows = []
for name, result in results.items():
    stats = result["stats"]
    rows.append({
        "Strategy": name,
        "Total return": f'{stats["Total return"]:.1%}',
        "Maximum drawdown": f'{stats["Max drawdown"]:.1%}',
        "Final value (units)": f'{result["frame"]["Equity"].iloc[-1]:,.0f}',
    })
st.table(pd.DataFrame(rows).set_index("Strategy"))

fig = go.Figure()
for name, result in results.items():
    fig.add_trace(go.Scatter(
        x=result["frame"].index,
        y=result["frame"]["Equity"],
        mode="lines", name=name
    ))
fig.update_layout(
    height=370, margin=dict(l=0, r=0, t=15, b=0),
    xaxis_title="Date", yaxis_title="Portfolio value (starting at 10,000)"
)
st.plotly_chart(fig, use_container_width=True)

st.subheader("4. Conclusion")
if len(results) == 1:
    st.write("This graph shows how a hypothetical Buy and Hold investment changed over the selected period.")
else:
    bh = buy_hold["stats"]["Total return"]
    ma = results["Moving Average"]["stats"]["Total return"]
    better = "Moving Average" if ma > bh else "Buy and Hold"
    st.write(f"{better} achieved the higher total return for this period. Compare maximum drawdowns to understand risk.")

st.caption("Assumptions: weekly closing prices, 0.1% transaction cost for each trade, and a one-bar delay for execution. Results are hypothetical.")
if kind == "Index":
    st.caption("Important: Index values are price-only proxies and cannot be purchased directly. Dividends, ETF tracking differences and real execution are not included.")
elif kind == "Leveraged ETF":
    st.caption("Important: This 2x daily leveraged ETF can diverge from twice the index's long-term return. Historical performance is not a forecast.")
elif kind == "Local sample":
    st.caption("Note: This sample uses normalized historical prices and may not reflect dividends.")
else:
    st.caption("For ETFs, Yahoo Finance adjusted prices are used where available. Returns may differ from a real brokerage account.")
st.caption("Educational demonstration only. Not investment advice.")
