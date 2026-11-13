from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.pdfmetrics import stringWidth
from backtest import compare_strategies,oos_metrics

BASE=Path(__file__).resolve().parent
raw=pd.read_csv(BASE/'data/plotly_weekly_stocks_2018_2019.csv',parse_dates=['date'])
p=pd.Series(raw['AAPL'].to_numpy(),index=raw['date'],name='AAPL')
results=compare_strategies(p,periods_per_year=52,cost_bps=10,fast=4,slow=16,rsi_window=14,low=35,high=65)
summary=pd.DataFrame({k:v['stats'] for k,v in results.items()}).T
summary.to_csv(BASE/'empirical_results_AAPL_2018_2019.csv',float_format='%.8f')

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9})
fig,ax=plt.subplots(figsize=(8.3,2.5),dpi=180)
for name,color in [('Buy & hold','#1860b9'),('Moving-average crossover','#008a78'),('RSI mean reversion','#e79f3b')]:
 f=results[name]['frame']
 ax.plot(f.index,f['Equity'],label=name,color=color,linewidth=1.8)
ax.set_ylabel('Portfolio value ($)');ax.grid(alpha=.16);ax.legend(loc='upper left',frameon=False,ncol=3,fontsize=7.5)
for s in ax.spines.values():s.set_visible(False)
fig.autofmt_xdate(rotation=0);fig.tight_layout(pad=.5)
fig.savefig(BASE/'equity_comparison.png',bbox_inches='tight',pad_inches=.1)
plt.close(fig)

OUT=BASE/'Executive_Summary_Stock_Strategy_Lab.pdf'
c=Canvas(str(OUT),pagesize=A4)
w,h=A4
NAVY=HexColor('#11243B');BLUE=HexColor('#177eac');MINT=HexColor('#008d82');GRAY=HexColor('#536273');LIGHT=HexColor('#e9f1f4')

def txt(x,y,s,size=9,color=NAVY,font='Helvetica'):
 c.setFillColor(color);c.setFont(font,size);c.drawString(x,y,s)
def right(x,y,s,size=9,color=NAVY,font='Helvetica'):
 c.setFillColor(color);c.setFont(font,size);c.drawRightString(x,y,s)
def line(y):
 c.setStrokeColor(HexColor('#dce5ec'));c.line(39,y,w-39,y)
def wrap(s,max_width,size=8.4,font='Helvetica'):
 words=s.split();rows=[];cur=''
 for word in words:
  proposed=(cur+' '+word).strip()
  if stringWidth(proposed,font,size)>max_width and cur:
   rows.append(cur);cur=word
  else:cur=proposed
 if cur:rows.append(cur)
 return rows
def paragraph(x,y,s,width,size=8.3,leading=12,color=NAVY):
 for line_text in wrap(s,width,size):
  txt(x,y,line_text,size,color);y-=leading
 return y

# Header stripe
c.setFillColor(NAVY);c.rect(0,h-119,w,119,stroke=0,fill=1)
txt(39,h-42,'STOCK STRATEGY',23,HexColor('#ffffff'),'Helvetica-Bold')
txt(39,h-67,'BACKTESTING LAB',23,HexColor('#ffffff'),'Helvetica-Bold')
txt(39,h-91,'A transparent, interactive experiment in systematic trading',10,HexColor('#c0e7e3'))
right(w-39,h-92,'PROGRAMMING & DATA ANALYSIS  |  FINAL BONUS',7.5,HexColor('#e8f3fa'))
y=h-146

txt(39,y,'THE QUESTION',9,MINT,'Helvetica-Bold');y-=17
y=paragraph(39,y,'Can simple technical rules improve investment outcomes after trading friction? The app tests three long-or-cash approaches on identical historical observations and reports both returns and risk.',w-78,9,13);y-=7

txt(39,y,'HOW IT WORKS',9,MINT,'Helvetica-Bold');y-=16
y=paragraph(39,y,'Built with Python, Streamlit, Pandas and Plotly. Compare buy-and-hold, a 4/16-period moving-average crossover, and RSI(14) mean reversion (buy <35; sell >65). Signals are calculated on closed bars; orders fill at the following close. Charge 10 basis points per side for transaction cost and estimated slippage.',w-78,8.4,12);y-=10

txt(39,y,'EMPIRICAL DEMONSTRATION',9,MINT,'Helvetica-Bold');y-=15
txt(39,y,'AAPL | 105 weekly historical normalized observations | 2018-2019 | $10,000 initial capital',8,GRAY);y-=22
cols=[39,270,345,427,513]
headers=['Strategy','Total return','Max DD','Sharpe','Trades']
for x,s in zip(cols,headers):txt(x,y,s,8,NAVY,'Helvetica-Bold')
y-=9;line(y);y-=16
for key,lab in [('Buy & hold','Buy & Hold'),('Moving-average crossover','MA Crossover (4/16)'),('RSI mean reversion','RSI Mean Reversion')]:
 st=results[key]['stats']
 values=[lab,f"{st['Total return']:+.2%}",f"{st['Max drawdown']:.2%}",f"{st['Sharpe (rf=0)']:.2f}",str(st['Trades'])]
 for x,s in zip(cols,values):txt(x,y,s,8.6,MINT if key=='Moving-average crossover' else NAVY,'Helvetica-Bold' if key=='Moving-average crossover' else 'Helvetica')
 y-=18
line(y+7)
y-=4
# figure scaled
chart_height=142
c.drawImage(str(BASE/'equity_comparison.png'),39,y-chart_height,width=w-78,height=chart_height,mask='auto')
y-=chart_height+11

txt(39,y,'KEY INSIGHT',9,MINT,'Helvetica-Bold');y-=16
y=paragraph(39,y,'Buy & Hold led in total return (+65.65%). MA Crossover earned less (+59.55%) but reduced the maximum drawdown from -34.87% to -17.32% and increased Sharpe from 1.07 to 1.40. Lower risk is not equivalent to superior profit; costs and market regimes matter.',w-78,8.5,12);y-=12

txt(39,y,'WHAT MAKES THE APP USEFUL',9,MINT,'Helvetica-Bold');y-=16
y=paragraph(39,y,'Interactive parameters, multi-strategy equity curves, annotated buy/sell executions, downloadable CSV outputs, and a chronological in-sample/out-of-sample comparison. Real daily adjusted-price download is available via Yahoo Finance; an included historical offline dataset keeps the classroom demonstration reproducible.',w-78,8.3,12);y-=11

txt(39,y,'LIMITATIONS & NEXT STEPS',9,MINT,'Helvetica-Bold');y-=15
y=paragraph(39,y,'The included Plotly demo series is normalized, short, and not verified for dividend-inclusive total return. The fill model ignores market impact and tax. Future work: longer market histories, walk-forward tests and sensitivity to trading cost. Results are educational, not investment advice.',w-78,8.1,11)
line(38)
txt(39,25,'DATA: Plotly historical weekly stock sample (2018-2019)  |  LIVE: Yahoo Finance via yfinance',7,GRAY)
right(w-39,25,'PUBLIC APP URL: add after deployment',7,GRAY)
if y < 44: raise ValueError('PDF content overflow: '+str(y))
c.showPage();c.save()
print('created',OUT,'end y',y)
