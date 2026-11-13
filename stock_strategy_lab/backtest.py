"""Transparent long/cash close-to-close backtesting engine.

Execution convention: signal determined from completed bar t; order filled at
close of bar t+1; investment return first earned over t+1 -> t+2.
Transactions are charged at the assumed fill (close) with a fixed one-way rate.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

TRADING_PERIODS = {"Daily": 252, "Weekly": 52}


def validate_prices(prices: pd.Series) -> pd.Series:
    prices = pd.to_numeric(prices, errors="coerce").dropna().astype(float).sort_index()
    prices = prices[~prices.index.duplicated(keep="last")]
    if len(prices) < 25 or (prices <= 0).any():
        raise ValueError("At least 25 positive, non-missing adjusted close prices are required.")
    return prices


def rsi(prices: pd.Series, window: int = 14) -> pd.Series:
    """Wilder's smoothing with explicit seed using mean gain/loss."""
    delta = prices.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    g = gain.ewm(alpha=1/window, adjust=False, min_periods=window).mean()
    l = loss.ewm(alpha=1/window, adjust=False, min_periods=window).mean()
    ratio = g / l.replace(0, np.nan)
    out = 100 - 100/(1+ratio)
    out = out.mask((l == 0) & (g > 0), 100).mask((l == 0) & (g == 0), 50)
    return out


def make_signal(prices: pd.Series, kind: str, fast: int = 4, slow: int = 16,
                rsi_window: int = 14, low: float = 35, high: float = 65) -> tuple[pd.Series,pd.DataFrame]:
    """Signal is desired long/cash allocation calculated at bar CLOSE (0 or 1)."""
    p = validate_prices(prices)
    indic = pd.DataFrame(index=p.index)
    if kind == "Moving-average crossover":
        if fast < 2 or slow <= fast or slow >= len(p):
            raise ValueError("Require 2 <= fast < slow < observation count.")
        indic["Fast MA"] = p.rolling(fast, min_periods=fast).mean()
        indic["Slow MA"] = p.rolling(slow, min_periods=slow).mean()
        signal = (indic["Fast MA"] > indic["Slow MA"]).astype(float)
    elif kind == "RSI mean reversion":
        if not (2 <= rsi_window < len(p) and 0 < low < high < 100):
            raise ValueError("Require valid RSI period and 0 < buy threshold < sell threshold < 100.")
        indic["RSI"] = rsi(p, rsi_window)
        # Stateful: enter when RSI falls below low; exit when above high.
        active = 0.0
        choices = []
        for v in indic["RSI"]:
            if pd.notna(v):
                if v < low: active = 1.0
                elif v > high: active = 0.0
            choices.append(active)
        signal = pd.Series(choices, index=p.index, dtype=float)
    elif kind == "Buy & hold":
        signal = pd.Series(1., index=p.index)
    else:
        raise ValueError(f"Unsupported strategy: {kind}")
    return signal.rename("Signal"), indic


def run_backtest(prices: pd.Series, kind: str, *, periods_per_year: int=52,
                 cost_bps: float=10, fast: int=4, slow: int=16,
                 rsi_window: int=14, low: float=35, high: float=65,
                 start_cash: float=10000) -> dict:
    p = validate_prices(prices)
    signal, indic = make_signal(p,kind,fast,slow,rsi_window,low,high)
    # This bar's target is set by yesterday's signal, filled at THIS close.
    target = signal.shift(1).fillna(0).astype(float)
    # Price change in the bar happens prior to close-of-bar target execution.
    held = target.shift(1).fillna(0)
    raw_return = p.pct_change().fillna(0)
    turnover = target.diff().abs().fillna(target.abs())
    trading_cost = turnover * (cost_bps / 10000)
    net_return = held * raw_return - trading_cost
    equity = start_cash * (1+net_return).cumprod()
    out = pd.DataFrame({"Price":p,"Signal":signal,"Target position":target,
                       "Held for return":held,"Market return":raw_return,
                       "Turnover":turnover,"Trading cost":trading_cost,
                       "Strategy return":net_return,"Equity":equity})
    out = out.join(indic)
    changes=out.loc[out["Turnover"]>0,["Price","Target position","Turnover","Trading cost"]].copy()
    changes["Side"]=np.where(changes["Target position"]>0,"BUY","SELL")
    changes.index.name="Execution date"
    stats=performance(out["Strategy return"],equity,periods_per_year,
                      int(len(changes)),float(trading_cost.sum()))
    return {"frame":out,"trades":changes,"stats":stats}


def performance(ret: pd.Series, eq: pd.Series, periods_per_year: int,
                trades: int, total_cost_pct: float) -> dict:
    n=max(len(eq)-1,1)
    total=eq.iloc[-1]/eq.iloc[0]-1
    # Note: equity[0] may include initial fee; annualized uses initial principal
    total_from_principal=eq.iloc[-1]/10000 if False else None
    # Caller may choose a different initial capital; base from first daily return.
    initial=eq.iloc[0] / (1+ret.iloc[0]) if 1+ret.iloc[0] !=0 else eq.iloc[0]
    total=eq.iloc[-1]/initial-1
    cagr=(1+total)**(periods_per_year/n)-1 if total > -1 else -1
    vol=ret.std(ddof=1)*np.sqrt(periods_per_year)
    sharpe=(ret.mean()/ret.std(ddof=1))*np.sqrt(periods_per_year) if ret.std(ddof=1)>0 else np.nan
    dd=eq/eq.cummax()-1
    return {"Total return":float(total),"CAGR":float(cagr),
            "Volatility":float(vol),"Sharpe (rf=0)":float(sharpe),
            "Max drawdown":float(dd.min()),"Trades":int(trades),
            "Total cost / initial equity":float(total_cost_pct)}


def compare_strategies(p: pd.Series, *, periods_per_year: int=52,
                        cost_bps:float=10, fast:int=4,slow:int=16,
                        rsi_window:int=14,low:float=35,high:float=65,
                        start_cash:float=10000) -> dict:
    common=dict(periods_per_year=periods_per_year,cost_bps=cost_bps,
                fast=fast,slow=slow,rsi_window=rsi_window,low=low,high=high,
                start_cash=start_cash)
    return {name:run_backtest(p,name,**common) for name in
            ["Buy & hold","Moving-average crossover","RSI mean reversion"]}


def oos_metrics(prices:pd.Series, kind:str, split:float=.7, **kwargs) -> dict:
    """Fixed parameter evaluation, not parameter optimization. Uses warm-up history.
    OOS return is recomputed from daily returns in test segment, not equity subtraction.
    """
    res=run_backtest(prices,kind,**kwargs)
    frame=res['frame']; cut=int(len(frame)*split)
    if cut < 5 or len(frame)-cut < 5: raise ValueError("Too few observations.")
    py=kwargs.get("periods_per_year",52)
    def piece(part):
        ret=part["Strategy return"]
        eq=(1+ret).cumprod()*10000
        return performance(ret,eq,py,int((part["Turnover"]>0).sum()),float(part["Trading cost"].sum()))
    return {"in_sample":piece(frame.iloc[:cut]),
            "out_sample":piece(frame.iloc[cut:]),"split_date":frame.index[cut]}
