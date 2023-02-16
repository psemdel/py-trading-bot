# Strategies

I am not a professional trader. The strategies included in the bot are more example, to show you how you could implement your own one. For transparency, some explications are brought here.

# Strategy on one stock

Strategies on one stock are provided in core/strat.py. They buy and send one stock, let's say Apple, depending on some signal. The combination of signals is provided in the form of an array, 1 means the signal is used, 0 means that it is not used. The signals are well known one, and most of them provided out-of-the-box by vectorbt but you can modify them:
* MA: Compare a smoothed price over a short time window (fast signal) with a smoothed signal over a longer time window (slow signal). If the fast signal cross the slow one and becomes higher, a buy signal is created. At the opposite, if they cross and the fast becomes lower than the slow one, a sell signal is created. [See also](https://www.investopedia.com/ask/answers/071414/whats-difference-between-moving-average-and-weighted-moving-average.asp)
* RSI: It buys if the stock is "oversold", so when the price decreases quickly, and sell when it is overbought. The threshold can be defined, typically 80 and 20 or 70 and 30.
* Stochastic RSI: variation of RSI. Same idea
* KAMA: Kama is just an exponential smoothing of the price (PT1-filter for the German ;) ). Compare to the moving average smoothing, it has the advantage to give more weight to recent prices. My algorithm looks for the extrema of this function. It buys when a minimum is detected and sell when a maximum is detected. It indicates big changes, however it is not especially fast as the filter brings with it a delay.
* Supertrend: [See](https://medium.datadriveninvestor.com/superfast-supertrend-6269a3af0c2a)
* Bollinger band: [See](https://www.investopedia.com/trading/using-bollinger-bands-to-gauge-trends/). When the price reaches the bottom band, a buy signal is sent.
* Patterns: there are many candlelight patterns. The ones selected, see core/constants, have higher prediction potential according to my statistics, but you can basically use any defined in Talib.

The combination defined in the bot results from optimisation algorithms without any a priori. The best combination for stocks is called "normal strategy" in the bot. As the index tends to behave differently, a strategy has been optimized for them also.

The strategies on one stock are useful, but obviously do not help to select the stock to bet on.

# "Macro" Trend
Additionally, you can choose if you want to perform only long, only short or only both orders. The "macro" function, determine the general trend of the index related to the stock. So the dow jones for the NYSE. You can variate the type of orders depending on this trend. By default, it is long if the trend is bull, both for undetermined or bear trend. Theoretically, short would be better for bear, but a) bear tends to be more difficult to detect than bull, b) the rebound is badly exploited if you are in short.

The detection of the general trend is not easy. The present algorithm was optimized, but it cannot detect immediately a reversal.

# Strategy on several stocks
This kind of strategy tries to:
a) Select the stock to buy/sell
b) Determine when to buy/sell them

They are saved in core/bt.py

The points a and b can be handled the same way, but an "underlying strategy" (see previous paragraph) can be used to handle b. The point a is defined as preselection. Let's take an example, you want to trade the stock with the highest volatility (function preselect_vol in core/bt.py). It filters the, let's say 4, stocks with the highest volatility (the candidates). When a buy signal, underlying strategy, is detected for one of those stock, it is bought. Then we wait for a sell signal from the underlying strategy, and determine again the candidates.

## Volatility
See example

## MACD + volatility
Same as volatility, but the candidates must have a positive MACD.

## HIST + volatility
Same as volatility, but the hysteresis parameter of the MACD must be positive for the candidates.

Note: the two last strategies turn to be highly chaotic. If you change your backtesting window from one day (let's say it begins the 05/01/2007 instead of the 4/01/2007), it will completely change the result.

## Realmadrid
I called this strategy so, as it bets on the winners. The candidates are the stocks which raised the most on a window of the past 400 trading days. 

## Retard
This strategy first perform a KAMA on all prices. Then it determines the extrema and calculate the number of days in which the stock has been in a trend. So a figure of 30 means that the smoothed price of the stock has been decreasing for the past 30 days. -30 means, it rises since 30 days. The stock whose price is decreasing since the longest time is candidate. As a kind of stop loss, the stock cannot be retained more than 15 days. If it happens, it is sold and "excluded" from the strategy until the trend inverts. I called this strategy "retard" (delay) as the candidate stock is somehow delayed compared to the general trend and will at some point tries to reduce the difference to it.

If the macro trend (see above) is bear, the mechanism is inverted. It does not work as good however.

## Retard keep
Variation of retard. Retard sells the stock, when it reverted it trends. So it means when the price is increasing, which is a bit too bad. Retard keep, keeps the stock until a signal of the underlying strategy comes (it is packed in the "normal strategy"). It requires however twice more capital than "retard", as the new candidate (price decreasing) is bought and the old candidate is kept. 

## Divergence
It compare the smoothed price variation of one stock to the smoothed price variation of the index. If the stock price variation is significantly worse, it becomes candidate. It is a kind of RSI for multiple stocks. The stock is sold depending on the underlying strategy.

## WQ
Implementation of the [101 Formulaic Alphas](https://arxiv.org/pdf/1601.00991.pdf). So professional alphas, some of them are very powerful. Check out also the number of trades they create, as you may pay more fee than a big trader bank ;). 



