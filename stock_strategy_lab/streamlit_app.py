"""Simple Buy and Hold stock comparison for a Python class."""
import pandas as pd
import streamlit as st
import yfinance as yf

st.set_page_config(page_title="Stock Backtesting Lab")
st.title("Stock Strategy Backtesting Lab")
st.write("A simple Buy and Hold investment simulator using historical data.")

assets = {
    "0050 - Taiwan 50 ETF": "0050.TW",
    "00631L - Taiwan 50 2x ETF": "00631L.TW",
    "S&P 500 Index": "^GSPC",
    "QQQ - Nasdaq 100 ETF": "QQQ",
    "Philadelphia Semiconductor Index": "^SOX",
}

stock = st.selectbox("Choose a stock or index", list(assets))
ticker = assets[stock]

@st.cache_data(ttl=3600)
def get_prices(symbol):
    data = yf.download(symbol, period="5y", interval="1wk",
                       auto_adjust=True, progress=False, threads=False)
    if data.empty:
        return pd.Series(dtype=float)
    prices = data["Close"]
    if isinstance(prices, pd.DataFrame):
        prices = prices.iloc[:, 0]
    return prices.dropna()

try:
    prices = get_prices(ticker)
except Exception:
    st.error("Could not load stock data. Please try again later.")
    st.stop()

if len(prices) < 2:
    st.warning("Not enough historical data. Please choose another asset.")
    st.stop()

# Buy at the first price and hold to the last price.
initial_money = 10000
portfolio = initial_money * prices / prices.iloc[0]
total_return = (portfolio.iloc[-1] / initial_money - 1) * 100
drawdown = (portfolio / portfolio.cummax() - 1).min() * 100

st.subheader("Buy and Hold results")
st.write(f"Period: {prices.index[0].date()} to {prices.index[-1].date()}")
st.write(f"Starting value: {initial_money:,.0f} units")
st.write(f"Final value: {portfolio.iloc[-1]:,.0f} units")
st.write(f"Total return: {total_return:.2f}%")
st.write(f"Maximum drawdown: {drawdown:.2f}%")
st.line_chart(portfolio.rename("Portfolio value"))

st.caption("Source: Yahoo Finance, approximately 5 years of weekly prices.")
st.caption("This simplified model assumes no transaction costs, taxes or currency conversion.")
st.caption("Index values (S&P 500 and SOX) are not directly investable; results are index-price simulations.")
st.caption("00631L is a daily leveraged ETF, not a guaranteed 2x long-term return.")
st.caption("Educational use only. Past returns do not predict future results.")
