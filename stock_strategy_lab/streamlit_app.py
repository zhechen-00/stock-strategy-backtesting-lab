import streamlit as st
import yfinance as yf

st.title("Stock Strategy Backtesting Lab")
st.write("A simple Buy and Hold simulation using historical prices.")

stocks = {
    "0050 - Taiwan 50 ETF": "0050.TW",
    "00631L - Taiwan 50 2x ETF": "00631L.TW",
    "S&P 500 Index": "^GSPC",
    "QQQ - Nasdaq 100 ETF": "QQQ",
    "Philadelphia Semiconductor Index": "^SOX"
}

choice = st.selectbox("Choose an investment", list(stocks))

@st.cache_data(ttl=3600)
def load_prices(ticker):
    data = yf.download(ticker, period="5y", interval="1wk",
                       auto_adjust=True, progress=False)
    if data.empty:
        return None
    close = data["Close"]
    if close.ndim == 2:
        close = close.iloc[:, 0]
    return close.dropna()

try:
    prices = load_prices(stocks[choice])
    if prices is None or len(prices) < 2:
        st.warning("Historical data is not available. Please try again.")
        st.stop()
except Exception:
    st.error("Could not download prices. Please try again later.")
    st.stop()

# Invest 10,000 units on the first date, then hold.
portfolio = 10000 * prices / prices.iloc[0]
total_return = (portfolio.iloc[-1] / 10000 - 1) * 100
max_drawdown = (portfolio / portfolio.cummax() - 1).min() * 100

st.subheader("Buy and Hold Results")
st.write(f"Period: {prices.index[0].date()} to {prices.index[-1].date()}")
st.write(f"Final value: {portfolio.iloc[-1]:,.0f} units")
st.write(f"Total return: {total_return:.2f}%")
st.write(f"Maximum drawdown: {max_drawdown:.2f}%")
st.line_chart(portfolio.rename("Portfolio value"))
st.caption("Yahoo Finance weekly prices (approx. 5 years). No fees, taxes or FX. "
           "S&P 500 and SOX are non-tradable index price simulations. "
           "00631L targets 2x daily returns, not 2x long-term returns. "
           "Historical results do not predict future performance.")
