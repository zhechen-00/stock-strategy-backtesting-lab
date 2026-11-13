# Three-Minute Classroom Demo — English Script

**Title:** Stock Strategy Backtesting Lab

### 0:00–0:25 | Open with a question

“Can a simple trading strategy really beat buying and holding a stock? Many investors use moving averages or the RSI indicator, but backtests often look profitable only because they ignore fees or accidentally use future information. I built this interactive lab to make those trade-offs visible.”

**On screen:** Open the public Streamlit URL. Show the title and sidebar.

### 0:25–0:55 | Data and research design

“The dashboard compares three approaches on exactly the same price history: buy-and-hold, a moving-average crossover, and RSI mean reversion. The user can select a stock and adjust the rules. For the live source, the app downloads adjusted daily prices from Yahoo Finance. For a stable classroom demo, this offline mode includes genuine historical weekly observations, not randomly generated prices.”

**On screen:** Keep Offline AAPL selected. Point out 4/16 moving averages and 10-basis-point cost.

### 0:55–1:35 | Main finding

“Here are the results for Apple's weekly historical sample from 2018 to 2019. Buy-and-hold earned about 65.7%, compared with 59.6% for the moving-average strategy. However, the maximum drawdown was about 34.9% for buy-and-hold and only 17.3% for the crossover. So the crossover had a lower return, but much lower downside exposure. This is why I measure risk as well as profit.”

**On screen:** Point to the three strategy curves and performance table.

### 1:35–2:05 | Show the programming evidence

“Unlike a static dashboard, every result recalculates when I change a parameter. For example, I can raise the trading cost to 30 basis points and see how active strategies are penalized. Importantly, the code does not execute trades on the same closing price that created the signal. It delays the trade until the following bar's close.”

**On screen:** Move the cost slider from 10 to 30; open Signals & executions, point to buy/sell arrows and downloadable trade log.

### 2:05–2:35 | Evaluation, not prediction

“This tab divides history chronologically into earlier in-sample and later out-of-sample observations. It helps us ask whether a fixed trading rule is consistent over time. It is not a promise that the rule will work tomorrow. We also document limitations like slippage, short sample periods and parameter overfitting.”

**On screen:** Open Out-of-sample test. Explain the split date.

### 2:35–3:00 | Close

“My project combines financial curiosity with Python, data analysis and interactive software deployment. The main lesson is that the best strategy depends on what you care about: total return, drawdown, or risk-adjusted performance. The app is online, repeatable and available for anyone to explore. Thank you.”

**Before class:** Replace “the app is online” only after the public URL is actually working. Write that URL on the first slide, browser bookmark or the PDF handout. Verify the offline demo works in an incognito window.
