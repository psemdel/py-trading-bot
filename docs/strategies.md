# Strategies
To decide when to perform orders and which stocks to trade, strategies need to defined. The bot offers different possibilities for their implementation. For their backtesting, refer to the [corresponding documentation](https://github.com/psemdel/py-trading-bot/blob/main/docs/backtesting.md).

## Object
The bot is delivered with a dump containing some predefined strategies, but you surely wants to add more.

fter having started the bot click on "Admin panel" (http://localhost:8000/admin/). 

- Click on "add" close to "Strategys"

Following inputs can be defined:

- name: name of this strategy
- class: name of the Class in strat.py or presel.py used to determine when to perform orders using this strategy, the algorithm.
- perform_order: boolean that determines if automatic orders in IB should be performed. If False, only manual trade is possible.
- priority: figure to rank the strategies by priority. Lower figure has higher priority. Concretely, if the report calculated lead to the performance of 2 orders but you have money for only one, it will define which one to execute.
- target_order_size: which order size in the base currency should be performed. For instance 1000, with base currency EUR, will perform order of 1000 euros.
- minimum_order_size: if the target_order_size cannot be reached (not enough money), what is minimum size of the trade which should lead to a trade execution.
- maximum_money_engaged: maximum total money that can be engaged in this strategy / stock exchange. To avoid having all the money invested in one strategy.
- sl_threshold: stop loss threshold for orders performed with this strategy.
- daily_sl_threshold: daily stop loss threshold for orders performed with this strategy.
- option_share_per: percentage of the order that should be performed with options instead of stocks.
- option_min_days_distance: minimum time in day between now and option expiration.
- option_max_strike_distance_per: maximum difference between present stock price and option strike price.

## Algorithm introduction
Fundamentally the bot differentiate two types of strategies:
- Strategies on one stock, called in the code "underlying strategy". Let's say you apply this strategy on Apple. It will decide when to buy and sell this stock depending on predefined signals, for instance the value of RSI. The stock involved will always be the same, here Apple. By default, you will always own this stock, in long or short direction.
- Strategies on several stocks. Before deciding to buy or to sell, this kind of strategy will first determine which stocks to trade from a predefined group, stock exchange related. This selected stocks are called candidates. This step is later called preselection. Afterwards an underlying strategy can determine when to buy or sell those candidate stocks.

## Strategy on one stock
Strategies on one stock are provided in core/strat.py and core/strat_legacy.py. Each underlying strategy is defined by a class.

The stocks that you want to trade with this kind of strategy must be selected in a "Strat candidates" object associated with the strategy, which can be create in the admin panel.

### Indicators from vbt
The easiest kind of strategies use predefined indicator from vbt. For instance:

```
class StratRSI(UnderlyingStrat):  
    '''
    Very basic RSI strategy
    '''
    def run(self):      
        t=vbt.RSI.run(self.close,wtype='simple')
        self.entries=t.rsi_crossed_below(20)
        self.exits=t.rsi_crossed_above(80)
        t2=ic.VBTFALSE.run(self.close)
        self.entries_short=t2.entries
        self.exits_short=t2.entries
```

Here an entry order will be performed when the RSI crosses below 20 and an exit when it crosses above 80. No short orders will be performed.

### Self-made indicators
You can create your own indicator in core/indicator.py. This function comes directly from vbt, documentation can be found there. As example:

```
def ma(close: np.array)-> (np.array, np.array):    
    fast_ma = vbt.MA.run(close, 5)
    slow_ma = vbt.MA.run(close, 15)
        
    entries =  fast_ma.ma_crossed_above(slow_ma)
    exits = fast_ma.ma_crossed_below(slow_ma)
    
    return entries, exits
 
VBTMA = vbt.IF( #just to keep everything the same shape... but useless here
     class_name='MA',
     short_name='ma',
     input_names=['close'],
     output_names=['entries', 'exits']
).with_apply_func(
     ma, 
     takes_1d=True,  
     )
```

This indicator will create an entry when fast_ma crosses above slow_ma, and an exit when fast_ma crosses below slow_ma. 

### Strategy array
Simple strategies are easy to understand, but they can be quite limited. Combination of different indicators can provide better results, without much more complexity. The bot provides the possibility to optimise combination of signals for certain stocks (see the [documentation about optimization](https://github.com/psemdel/py-trading-bot/blob/main/docs/optimization.md). The combination is always using OR, so signal1 or signal2 or ... A combination is represented by an array, as following:
    
For instance:

    class StratRSIeq(UnderlyingStrat):   
        '''
        Same a stratRSI but realized with a strategy array
        '''
        def __init__(self,
                     period: numbers.Number,
                     **kwargs):
            
            a={"simple":
               {"ent":['RSI20'],
                "ex": ['RSI20']
               }
              }

            super().__init__(period,strat_arr=a,**kwargs )

Uses RSI with threshold 20/80 for the entries and exits. It is perfectly equivalent to StratRSI presented above.

Possible key words are (for explanation about the different indicators refer to vbt and [talib documentation](https://github.com/TA-Lib/ta-lib-python/tree/master/docs/func_groups):
- MA (period 5/15)
- MFI (threshold 20/80)
- STOCH (threshold 20/80)
- WILLR (threshold -90/-10)
- SUPERTREND 
- BBANDS (crossing between the price and the bands)
- RSI20 (threshold 20/80)
- RSI30 (threshold 30/70)
- ULTOSC20 (threshold 20/80)
- ULTOSC25 (threshold 25/75)
Note: this is defined in strat.py

And all following patterns. They are defined in constants.py for explanation refer to [talib documentation](https://github.com/TA-Lib/ta-lib-python/tree/master/docs/func_groups). Bear can be used only for exits, bull for entries:            
             
BEAR_PATTERNS:
- CDLLONGLINE
- CDLENGULFING
- CDLCLOSINGMARUBOZU
- CDLBELTHOLD
- CDLHIKKAKE
- CDLRISEFALL3METHODS
- CDL3LINESTRIKE
- CDLBREAKAWAY
- CDLABANDONEDBABY
- CDLEVENINGSTAR
- CDLSEPARATINGLINES
- CDLEVENINGDOJISTAR
- CDL3BLACKCROWS
- CDLDARKCLOUDCOVER
- CDLMARUBOZU
- CDLHIKKAKEMOD
- CDLMORNINGSTAR
- CDLUNIQUE3RIVER
- CDLXSIDEGAP3METHODS
- CDLCOUNTERATTACK
- CDL3INSIDE
- CDLMORNINGDOJISTAR
- CDLBREAKAWAY

BULL_PATTERNS:
- CDLKICKINGBYLENGTH
- CDLKICKING
- CDLMARUBOZU
- CDLCLOSINGMARUBOZU
- CDL3WHITESOLDIERS
- CDLLONGLINE
- CDLENGULFING
- CDLDRAGONFLYDOJI
- CDLTAKURI
- CDLMORNINGDOJISTAR
- CDLMORNINGSTAR
- CDLHANGINGMAN
- CDL3INSIDE
- CDLKICKINGBYLENGTH_INV
- CDLKICKING_INV
- CDLINVERTEDHAMMER
- CDLPIERCING
- CDLHIKKAKEMOD
- CDLSTICKSANDWICH
- CDLTRISTAR
- CDL3LINESTRIKE
- CDLDARKCLOUDCOVER
- CDLINNECK
- CDL3BLACKCROWS          

### Trend dependent strategies
In addition to various combination of signal, it may be interesting to variate on one side the strategy depending on the trend of the market, on the other side a variation of the direction depending on the trend may also be useful. So when the market is bear, you will want to short, whereas it can be risky when the market is bull.

The trend calculation is explained in the corresponding documentation. It sorts the trend in bull, bear and uncertain. One strategy can be assigned for each trend:

    class StratG(UnderlyingStrat):    
        '''
        Strategy optimized to have the best yield used alone on stocks
        
        In long/both/both, Optimized on 2007-2023, CAC40 7.58 (3.13 bench), DAX 2.31 (1.68), NASDAQ 19.88 (12.1), IT 15.69 (8.44)
        '''
        def __init__(self,
                     period: numbers.Number,
                     **kwargs):

            a={'bull': {'ent': ['KAMA','RSI20','RSI30','CDLMARUBOZU',"CDL3WHITESOLDIERS","CDLENGULFING","CDLTAKURI","CDLMORNINGDOJISTAR","CDLMORNINGSTAR","CDLKICKING_INV"],
                        'ex': ["CDLRISEFALL3METHODS","CDLABANDONEDBABY"]},
               'bear': {'ent': ['STOCH','RSI20','RSI30',"CDLMARUBOZU","CDL3WHITESOLDIERS","CDLLONGLINE","CDLENGULFING","CDLTAKURI",
                                "CDLMORNINGDOJISTAR","CDLHANGINGMAN","CDLKICKINGBYLENGTH_INV"],
                        'ex': ['SUPERTREND','BBANDS',"CDLBELTHOLD"]},
               'uncertain': {'ent': ['STOCH','KAMA','RSI20','RSI30',"CDLMARUBOZU","CDLCLOSINGMARUBOZU","CDL3WHITESOLDIERS","CDLLONGLINE","CDLENGULFING",
                                     "CDLMORNINGDOJISTAR","CDLHANGINGMAN","CDLKICKINGBYLENGTH_INV","CDLKICKING_INV"],
                             'ex': ["CDLHIKKAKE","CDL3LINESTRIKE","CDLBREAKAWAY"]}} 
            
            super().__init__(
                period,
                strat_arr=a,
                **kwargs )     

Concerning the direction, by default the following is configured:

    dir_bull="long",
    dir_bear="both",
    dir_uncertain="both"
    

Note: Theoretically, short would be better for bear, but:

1. Bear tends to be more difficult to detect than bull, 
2. The rebound is badly exploited if you are in short.

To change this, just change the super().__init__ function presented above:


    super().__init__(
                period,
                strat_arr=a,
                dir_bull="long",
                dir_bear="short",
                dir_uncertain="long",
                **kwargs ) 

## Strategies on several stocks
Strategies on several stocks, later preselection strategies, are provided in core/presel.py. Each preselection strategy is defined by a class. 

Those strategies have two steps:

1. Select the stock(s) to buy/sell
2. Determine when to buy/sell them

Many strategies on several stocks can be imagined. To cover all those possibilities, the algorithm requires a certain complexity. 

### Underlying strategy
The second step "Determine when to buy/sell them" use underlying strategy, as presented before. For instance: 

    def underlying(self):
        self.underlying_creator("StratF")     

This preselection strategy will use the StratF as underlying strategy.

Additionnaly, the way the underlying strategy acts can be defined by:

    self.only_exit_ust=False
    self.no_ust=False
    
If no_ust is True, then the underlying strategy is completely ignored. If a stock is candidate, it is bought immediately. When it is not anymore in the candidates, it is sold.

If only_exit_ust is True. If a stock is candidate, it is bought immediately. However, it is sold only when the underlying strategy decides so. It means that the entry definition of the underlying strategy plays no role at all.

### Sorting
To determine which stock(s) to buy/sell, a sorting function is often required. The first stock(s) of the output list are then the candidates. For instance:

    def sorting(self,ii: int,**kwargs):
        v={}
        for symbol in self.close.columns.values:
            v[symbol]=self.vol[symbol].values[ii]
        self.sorted=sorted(v.items(), key=lambda tup: tup[1], reverse=True)
    
For the volatility preselection, the volatility (self.vol) serves to sort the stocks. 
If the sorting function can be calculated once and for all, it is done with the function sorting_g.

### Supplementary criterium
For certain strategy, the condition to become candidate is not only about the sorting. This supplementary condition can be defined in supplementary_criterium which used variable "condition". For instance:

    self.condition["long"]=remove_multi(self.macd_tot.macd>0)
    self.condition["short"]=remove_multi(self.macd_tot.macd<0)
    
The candidates here need to have a macd_tot.hist >0, if the direction is long.

### Strategy name
If you use pre-defined preselection strategies, note for some, the name of the strategy in your bot should be the same as the one defined in self.strategy in presel.py. 

### Maximum number of candidates
The maximum number of candidates at the same time is defined by `self.max_candidates_nb`. When it is higher than 1, the underlying strategy will be decisive about which one of the candidates will be actually bought.

### Influence of the trend
The behavior of the strategy can variate depending on the market trend. For the calculation of trend, see [here](https://github.com/psemdel/py-trading-bot/blob/main/docs/trend_calculation.md).

In the init function, the trend must then be calculated:

    PreselMacro.preliminary(self)

Two settings cover a different behavior:

    self.blocked=False     
    self.blocked_im=False  

If self.blocked is True, when the trend becomes short, no more candidate is added, but the stocks presently owned are sold by exit signal.

If self.blocked_im is True, when the trend becomes short, no more candidate is added, but the stocks presently owned are sold immediately.

There are also preselection strategy, that revert completely their behavior when the trend becomes short, like PreselRetardMacro. Then the run method must be changed:

    def run(self,**kwargs):
        self.last_short=PreselMacro.run(self,**kwargs)
    
### Slow preselection
Eventually, slow preselection strategies can be defined. The idea is that several candidates are selected at regular interval, let's say 14 days. The underlyng strategy will then determine which one to buy and sell. Methods like max_sharpe (defined in presel_classic.py) could be ranked in this categories. However, it does seem useful to schedule a job to run every year. For this case, you can run manually the portfolio optimization algorithm and put the candidates in "Strat candidates".

To calculate portfolio optimization algorithm like max sharpe, OLMAR and similar, you can use the Jupyter notebook presel_classic.

### Machine learning
For machine learning, see the dedicated documentation. 









