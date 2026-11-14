# Stock Strategy Backtesting Lab

A beginner-friendly Python Streamlit website demonstrating Buy and Hold using historical prices.

## Assets
0050, 00631L, S&P 500, QQQ, and Philadelphia Semiconductor Index.

## What it does
Select one asset. The website retrieves approximately five years of weekly prices from Yahoo Finance, assumes 10,000 units invested at the beginning, and displays final portfolio value, total return, maximum drawdown, and a line chart.

## How to run
```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Public app: https://stock-strategy-backtesting-lab-m6l6dmbgcid7zizehezhz8.streamlit.app

Data source: Yahoo Finance. Price-based educational simulation, without fees, taxes, or exchange-rate effects. The two indices are not directly investable.
