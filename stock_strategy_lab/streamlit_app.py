"""Stock Strategy Backtesting Lab — course submission, public Streamlit app."""
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from backtest import compare_strategies, oos_metrics

st.set_page_config(page_title="Stock Strategy Backtesting Lab",page_icon="📈",layout="wide")
st.markdown("""<style>.block-container{padding-top:1.7rem}div[data-testid='stMetric']{background:#101c30;border:1px solid #2b4565;border-radius:12px;padding:14px}.hero{background:linear-gradient(110deg,#142b43,#172d52);border-radius:16px;padding:22px 28px;margin-bottom:14px}.eyebrow{letter-spacing:3px;color:#72ded4;font-size:12px}.hero h1{color:white;margin:4px 0 6px}.hero p{color:#c0d2e5;margin:0}</style>""",unsafe_allow_html=True)
st.markdown('<div class="hero"><div class="eyebrow">INTERACTIVE FINANCIAL ANALYTICS</div><h1>📈 Stock Strategy Backtesting Lab</h1><p>Do technical strategies beat buy-and-hold after trading costs?</p></div>',unsafe_allow_html=True)

@st.cache_data(ttl=3600,show_spinner=False)
def live_data(ticker,start,end):
    import yfinance as yf
    df=yf.download(ticker,start=start,end=(pd.Timestamp(end)+pd.Timedelta(days=1)).strftime('%Y-%m-%d'),
                   auto_adjust=True,progress=False,threads=False)
    if df.empty: raise ValueError('Yahoo returned no market data for that symbol/date range.')
    if isinstance(df.columns,pd.MultiIndex):
        # yfinance versions can return (Price,Ticker)
        p=df['Close'].iloc[:,0]
    else:p=df['Close']
    p=pd.Series(p.values,index=pd.to_datetime(p.index).tz_localize(None),name=ticker)
    return p.dropna()

@st.cache_data(show_spinner=False)
def offline_data(ticker):
    df=pd.read_csv(Path(__file__).parent/'data'/'plotly_weekly_stocks_2018_2019.csv',parse_dates=['date'])
    return pd.Series(df[ticker].to_numpy(float),index=df['date'],name=ticker)

with st.sidebar:
    st.header('⚙️ Research controls')
    source=st.radio('Price data',['Offline verified historical sample','Yahoo Finance (live download)'],help='Offline sample = real weekly normalized historical stock series, 2018–2019. Yahoo Finance may rate-limit.')
    if source.startswith('Offline'):
        ticker=st.selectbox('Stock',['AAPL','MSFT','AMZN','GOOG','NFLX','FB'])
        st.caption('Weekly normalized prices; 2018–2019. Not current quotes.')
        freq='Weekly';fast_default=4;slow_default=16
    else:
        ticker=st.text_input('Symbol','SPY').strip().upper()
        date_range=st.date_input('Date range',(pd.Timestamp('2018-01-01').date(),pd.Timestamp.today().date()))
        freq='Daily';fast_default=20;slow_default=60
    fee=st.slider('One-way total cost (bps)',0,100,10,5,help='Fee + assumed slippage; 10 bps = 0.10% each time position changes.')
    st.subheader('MA crossover')
    fast=st.slider('Fast MA periods',2,60,fast_default)
    slow=st.slider('Slow MA periods',fast+1,210,max(slow_default,fast+1))
    st.subheader('RSI mean reversion')
    rsi_period=st.slider('RSI lookback',2,30,14)
    low=st.slider('Buy when RSI below',5,49,35)
    high=st.slider('Exit when RSI above',max(low+1,51),95,65)
    split=st.slider('Train/test time split (%)',50,85,70,5)/100

try:
    if source.startswith('Offline'):
        price=offline_data(ticker)
    else:
        if not ticker: st.stop()
        if not isinstance(date_range,tuple) or len(date_range)!=2:
            st.info('Choose a start and end date.');st.stop()
        price=live_data(ticker,*date_range)
    if slow>=len(price): st.error(f'Slow MA must be under {len(price)} observations.');st.stop()
    params=dict(periods_per_year=52 if freq=='Weekly' else 252,
                cost_bps=fee,fast=fast,slow=slow,rsi_window=rsi_period,low=low,high=high)
    results=compare_strategies(price,**params)
except Exception as exc:
    st.error(f'Could not run this configuration: {exc}')
    st.info('For a guaranteed demo, select Offline verified historical sample.');st.stop()

st.caption(f'**Dataset:** {ticker} | {freq} | {price.index[0]:%Y-%m-%d} to {price.index[-1]:%Y-%m-%d} | {len(price)} observations | '+('Plotly built-in historical weekly stock series (normalized to 1)' if source.startswith('Offline') else 'Yahoo Finance adjusted closing prices (auto_adjust=True)'))
# All summaries are computed by engine, never hard-coded.
summary=pd.DataFrame({k:v['stats'] for k,v in results.items()}).T
best=summary['Total return'].idxmax()
c1,c2,c3,c4=st.columns(4)
c1.metric('Best strategy by total return',best)
c2.metric('Best total return',f"{summary.loc[best,'Total return']:.1%}")
c3.metric('Buy & hold return',f"{summary.loc['Buy & hold','Total return']:.1%}")
c4.metric('MA max drawdown',f"{summary.loc['Moving-average crossover','Max drawdown']:.1%}")

tab1,tab2,tab3,tab4=st.tabs(['📊 Strategy comparison','📉 Signals & executions','🧪 Out-of-sample test','📘 Research notes'])
with tab1:
    st.subheader('Portfolio growth (same initial capital = $10,000)')
    fig=go.Figure()
    for name,res in results.items():
        f=res['frame'];fig.add_trace(go.Scatter(x=f.index,y=f['Equity'],name=name,mode='lines'))
    fig.update_layout(template='plotly_dark',height=430,yaxis_title='Portfolio value ($)',xaxis_title='Date',legend=dict(orientation='h',y=1.1),margin=dict(t=30,b=20))
    st.plotly_chart(fig,use_container_width=True)
    display=summary.copy()
    for key in ['Total return','CAGR','Volatility','Max drawdown','Total cost / initial equity']:
        display[key]=display[key].map(lambda x:f'{x:.2%}')
    display['Sharpe (rf=0)']=display['Sharpe (rf=0)'].map(lambda x:'N/A' if pd.isna(x) else f'{x:.2f}')
    st.dataframe(display,use_container_width=True)
    st.download_button('Download strategy summary CSV',summary.to_csv().encode(),f'{ticker}_summary.csv','text/csv')
with tab2:
    selected=st.selectbox('Inspect strategy',['Moving-average crossover','RSI mean reversion','Buy & hold'])
    res=results[selected];frame=res['frame'];trades=res['trades']
    fig=go.Figure()
    fig.add_trace(go.Scatter(x=frame.index,y=frame['Price'],name='Adjusted/normalized close',line=dict(color='#9eb9df')))
    if selected=='Moving-average crossover':
        for key,color in [('Fast MA','#34d5a2'),('Slow MA','#f5be6c')]:
            fig.add_trace(go.Scatter(x=frame.index,y=frame[key],name=key,line=dict(color=color)))
    for side,shape,color in [('BUY','triangle-up','#32d5a0'),('SELL','triangle-down','#ff8b8b')]:
        t=trades.loc[trades['Side']==side]
        fig.add_trace(go.Scatter(x=t.index,y=t['Price'],mode='markers',name=side,marker=dict(size=12,symbol=shape,color=color)))
    fig.update_layout(template='plotly_dark',height=430,yaxis_title='Price (normalized for offline dataset)',margin=dict(t=20,b=20))
    st.plotly_chart(fig,use_container_width=True)
    st.caption('Markers show the assumed NEXT-BAR CLOSE execution, not the day when the signal was first observed.')
    st.dataframe(trades, use_container_width=True)
    st.download_button('Download executions CSV',trades.to_csv().encode(),f'{ticker}_executions.csv','text/csv')
with tab3:
    st.subheader('Chronological 70/30-style split')
    st.write('Fixed parameters are evaluated on the first portion and the later portion separately. Past data remain available for indicator warm-up; this is **not** automatic parameter optimization.')
    oos={k:oos_metrics(price,k,split=split,**params) for k in results}
    split_date=next(iter(oos.values()))['split_date']
    st.info(f'Out-of-sample starts: **{split_date:%Y-%m-%d}**. Do not tune parameters on the test results.')
    chart=[]
    for k,v in oos.items():
        chart.extend([{'Strategy':k,'Period':'In-sample','Return':v['in_sample']['Total return']},
                      {'Strategy':k,'Period':'Out-of-sample','Return':v['out_sample']['Total return']}])
    tmp=pd.DataFrame(chart)
    fig=go.Figure()
    for period in ['In-sample','Out-of-sample']:
        d=tmp[tmp['Period']==period]
        fig.add_trace(go.Bar(x=d['Strategy'],y=d['Return']*100,name=period))
    fig.update_layout(barmode='group',template='plotly_dark',height=370,yaxis_title='Segment return (%)')
    st.plotly_chart(fig,use_container_width=True)
    st.dataframe(tmp.pivot(index='Strategy',columns='Period',values='Return').style.format('{:.2%}'),use_container_width=True)
with tab4:
    st.markdown('''#### Hypothesis
A rule-based strategy may reduce drawdowns but can underperform buy-and-hold after costs. The purpose is to test rather than assume this claim.

#### Model choices
- **MA crossover:** long when fast average is greater than slow average; otherwise cash.
- **RSI mean reversion:** enter long below the lower threshold; sell above the upper threshold.
- **Benchmark:** invested continuously after the first available execution.
- **No look-ahead:** signals use complete bars; orders execute at the **following bar's close**, and earn price returns only from the next bar onward.
- **Trading frictions:** 0–100 basis points, charged on every allocation change. No leverage, short positions, taxes, interest on cash, or partial fills.
- **Equity:** cumulative compounded net daily/weekly returns. Sharpe uses zero risk-free return, annualization uses 252 daily or 52 weekly periods.
- **Out-of-sample:** chronological split with *fixed* parameters, not a simulated learning algorithm. No claim of forecasting power.

#### Data provenance and limitations
Offline fallback: historical **weekly normalized equity prices** from Plotly's published `px.data.stocks()` dataset, 2018–2019. They are not executable historical share prices and can omit cash dividend returns; they are provided as reproducible educational evidence rather than investment-grade total returns. Live mode requests Yahoo Finance **auto-adjusted daily close** using `yfinance`, subject to rate limits, revisions, and usage terms. Close-to-close fill model is simplified and can differ from executable orders. Survivorship bias, execution constraints, regime changes, and data errors can affect conclusions.

**Not financial advice.** No profitability or investment recommendation is implied.''')
