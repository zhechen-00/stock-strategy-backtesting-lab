from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
from backtest import compare_strategies, run_backtest, make_signal, oos_metrics

def test_no_look_ahead_and_lagged_fill():
    p=pd.Series(np.linspace(100,150,100), index=pd.date_range('2023-01-01',periods=100))
    res=run_backtest(p,'Moving-average crossover',fast=3,slow=10)
    frame=res['frame']
    assert frame['Target position'].equals(frame['Signal'].shift(1).fillna(0))
    assert frame['Held for return'].equals(frame['Target position'].shift(1).fillna(0))
    assert frame['Strategy return'].iloc[0]==0

def test_trade_cost_reduces_profit():
    p=pd.Series(np.linspace(100,150,100), index=pd.date_range('2023-01-01',periods=100))
    a=run_backtest(p,'Buy & hold',cost_bps=0)
    b=run_backtest(p,'Buy & hold',cost_bps=40)
    assert a['frame']['Equity'].iloc[-1]>b['frame']['Equity'].iloc[-1]

def test_offline_real_observations():
    df=pd.read_csv(Path(__file__).resolve().parents[1]/'data/plotly_weekly_stocks_2018_2019.csv')
    assert len(df)==105
    price=pd.Series(df['AAPL'].to_numpy(), index=pd.to_datetime(df['date']))
    res=compare_strategies(price)
    assert len(res)==3
    for r in res.values():
        assert np.isfinite(r['frame']['Equity']).all()
        assert r['stats']['Trades']>=0
    oos=oos_metrics(price,'Moving-average crossover')
    assert oos['out_sample']['Total return'] > -1
