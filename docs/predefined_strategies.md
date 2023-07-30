# Pre-defined strategies
For information about strategy implementation in the bot, look at the strategy document. This document provides some explanation about the strategies pre-defined in the bot. I am not a professional trader. The strategies included in the bot are more example, to show you how you could implement your own one. For their backtesting, refer to the corresponding documentation.

# Strategy on one stock
## Indicators from vbt
* MA: Compare a smoothed price over a short time window (fast signal) with a smoothed signal over a longer time window (slow signal). If the fast signal cross the slow one and becomes higher, a buy signal is created. At the opposite, if they cross and the fast becomes lower than the slow one, a sell signal is created. [See also](https://www.investopedia.com/ask/answers/071414/whats-difference-between-moving-average-and-weighted-moving-average.asp)
* RSI: It buys if the stock is "oversold", so when the price decreases quickly, and sell when it is overbought. The threshold can be defined, typically 80 and 20 or 70 and 30.
* Stochastic RSI: variation of RSI. Same idea
* KAMA: Kama is just an exponential smoothing of the price (PT1-filter for the German ;) ). Compare to the moving average smoothing, it has the advantage to give more weight to recent prices. My algorithm looks for the extrema of this function. It buys when a minimum is detected and sell when a maximum is detected. It indicates big changes, however it is not especially fast as the filter brings with it a delay.
* Supertrend: [See](https://medium.datadriveninvestor.com/superfast-supertrend-6269a3af0c2a)
* Bollinger band: [See](https://www.investopedia.com/trading/using-bollinger-bands-to-gauge-trends/). When the price reaches the bottom band, a buy signal is sent.
* Patterns: there are many candlelight patterns. The ones selected, see core/constants, have higher prediction potential according to my statistics, but you can basically use any defined in Talib.

## Strategy array
The combination defined in the bot results from optimisation algorithms without any a priori. It is StratF, StratG... As the index tends to behave differently, a strategy has been optimized for them also. It is StratIndex, StratIndexB...

# Strategy on several stocks
## Volatility
The candidates are the stocks with the highest volatility.

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
