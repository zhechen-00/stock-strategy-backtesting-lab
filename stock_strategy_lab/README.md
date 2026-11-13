# Stock Strategy Backtesting Lab

A deployable Streamlit research dashboard comparing moving-average crossover, RSI mean reversion, and buy-and-hold with visible execution markers and realistic one-way transaction cost assumptions.

## Quick start

Use Python 3.11 or 3.12 (avoid managed / blocked Python executables):

```bash
python -m pip install -r requirements.txt
python -m streamlit run streamlit_app.py
python -m pytest -q tests
```

On Windows if `python` is blocked, select a permitted installation with `py -3.12 -m ...` or use GitHub Codespaces to avoid local installation.

## Live & reliable demo data

- **Offline (default)**: reproducible Plotly historical weekly normalized stock series covering 2018–2019; AAPL, MSFT, AMZN, GOOG, NFLX, FB. Included in `data/`, so the public app works even if data APIs are unavailable.
- **Yahoo Finance**: real historical DAILY adjusted closing prices, downloaded on demand by yfinance. Subject to Yahoo access, rate limits and terms; do not claim the live source is always available.

Both are historical observations, not randomly generated stock prices. Offline sample is only a demonstration (normalized values and limited period), not a real-time quotation or investment-grade total-return study.

## Execution methodology

- At completed close t, compute the signal.
- At close t+1, execute full long/cash allocation according to signal t; charge one-way cost (fee+slippage proxy).
- Earn close-to-close price return from t+1 to t+2 while held. This avoids same-bar signal execution/look-ahead.
- Cash earns 0%, no shorting, tax, spread model, borrowing or fractional risk sizing.
- RSI uses Wilder-style exponentially smoothed changes (EWMA initialization approximation).
- Out-of-sample uses chronological split with no future price data in signals, though parameters are selected by user and are not auto-optimized.

## Deployment in Streamlit Community Cloud

1. Create a **public** GitHub repo, e.g. `stock-strategy-backtesting-lab`.
2. Upload `streamlit_app.py`, `backtest.py`, `requirements.txt`, `.streamlit/config.toml`, `data/plotly_weekly_stocks_2018_2019.csv`; optionally upload `README.md`, `tests/`.
3. Visit https://share.streamlit.io, sign in via GitHub and choose **Create app**.
4. Select your repository, branch `main`, and main file `streamlit_app.py`; click **Deploy**.
5. Test the assigned `https://...streamlit.app` link in a private browser window, showing sample, interactions, chart, downloads and the test tab.
6. Add that **actual assigned URL** to the PDF's placeholder or README, then present it in class. The publicly deployed URL cannot be assigned merely by bundling these files.

Official docs: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy

## Research extension ideas

Implement walk-forward validation and a market/sector regime comparison; contrast Taiwan 0050.TW vs USA SPY and test whether lower turnover explains net outcomes. Avoid choosing parameters solely based on final test return.

## Attribution

Demo stock observations: Plotly `plotly.express.data.stocks()` (`2018–2019` historical normalized weekly price series). Historical data: Yahoo Finance via yfinance when selected. Data should be used subject to provider licensing and service conditions.

**Educational analytics only; not investment advice.**
