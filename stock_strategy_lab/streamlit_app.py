"""A small and reproducible stock backtesting classroom project."""
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from backtest import run_backtest

st.set_page_config(page_title="Stock Strategy Backtesting Lab", layout="centered")
st.title("Stock Strategy Backtesting Lab")
st.write("Compare a moving-average strategy with buying and holding a stock.")

DATA_FILE = Path(__file__).parent / "data" / "plotly_weekly_stocks_2018_2019.csv"
STOCKS = {"Apple (AAPL)": "AAPL", "Microsoft (MSFT)": "MSFT",
          "Google (GOOG)": "GOOG", "Amazon (AMZN)": "AMZN"}

@st.cache_data
def historical_prices(symbol):
    """Read published weekly historical data bundled with the project."""
    data = pd.read_csv(DATA_FILE, parse_dates=["date"])
    return pd.Series(data[symbol].to_numpy(float), index=data["date"], name=symbol)

st.subheader("1. Choose a stock")
chosen = st.selectbox("Stock", list(STOCKS))
symbol = STOCKS[chosen]
prices = historical_prices(symbol)
st.caption("Historical weekly data: 2018 to 2019. Prices are normalized, not live quotes.")

st.subheader("2. Compare strategies")
st.write("Buy and Hold: stay invested throughout the period.")
st.write("Moving Average: invest when the 4-week average exceeds the 16-week average; otherwise hold cash.")
st.write("Starting capital: $10,000. Estimated trading cost: 0.1% per transaction.")

# The shared backtesting engine delays execution by one bar to avoid using
# information from the future. Both strategies use the same price observations.
common = {"periods_per_year": 52, "cost_bps": 10, "start_cash": 10000}
buy_hold = run_backtest(prices, "Buy & hold", **common)
moving_average = run_backtest(prices, "Moving-average crossover", fast=4, slow=16, **common)
results = {"Buy and Hold": buy_hold, "Moving Average": moving_average}

st.subheader("3. Results")
rows = []
for name, result in results.items():
    stats = result["stats"]
    rows.append({"Strategy": name,
                 "Total return": f'{stats["Total return"]:.1%}',
                 "Maximum drawdown": f'{stats["Max drawdown"]:.1%}',
                 "Final value ($)": f'{result["frame"]["Equity"].iloc[-1]:,.0f}'})
st.table(pd.DataFrame(rows).set_index("Strategy"))

fig = go.Figure()
for name, result in results.items():
    fig.add_trace(go.Scatter(x=result["frame"].index,
                             y=result["frame"]["Equity"],
                             name=name, mode="lines"))
fig.update_layout(height=370, margin=dict(l=0, r=0, t=10, b=0),
                  xaxis_title="Date", yaxis_title="Portfolio value (USD)")
st.plotly_chart(fig, use_container_width=True)

st.subheader("4. What does this show?")
bh = buy_hold["stats"]["Total return"]
ma = moving_average["stats"]["Total return"]
if ma > bh:
    st.write("For this stock and period, the moving-average strategy had a higher total return.")
else:
    st.write("For this stock and period, buying and holding had a higher total return.")
st.write("Higher return does not always mean lower risk. Compare the maximum drawdowns above.")
st.caption("Data source: Plotly historical weekly stocks dataset. Model: long or cash, next-bar closing execution, with assumed costs. Normalized prices may exclude dividends. This is a teaching demonstration, not investment advice.")
