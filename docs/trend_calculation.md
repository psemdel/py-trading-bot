# Trend calculation
To find the right strategy, it can be interesting to determine if a stock price or the market is bear or bull. The bot incorporate some method to determine the trend. It does not rely on literature though, don't hesitate to incorporate your own one.

## Fast trend
The "fast" trend tends to change quickly. They can be found in core/indicators.py. They are "Bbands trend", "Bbands MACD trend" and Supertrend. To be honest, they are not very reliable and useful, I don't provide more details here.

An issue is that fast changing trends tend to interfere with the signals for buy/sell. You can for instance perfectly use Supertrend to determine when to buy and sell a stock, so as signal. Using it for the direction at the same time can make things weird. 

## Slow trend
To avoid last issue, I considered that it is more useful to determine general, slow changing trends. They are called macro trend in the bot. They are defined in core/macro.py. Once again, it is home made, so don't hesitate to incorporate your own one.

Present algorithm uses a smoothed price as entry, typically the main index price (Dow Jones). The algorithm looks for extrema on this curve. The last extrema is compared with the present price. If the present price is close to the extrema, let's say the price is 99 and the maximum was 100, this extrema is not considered to have changed the trend and is ignored. For instance:

![Extrema ignored](https://github.com/psemdel/py-trading-bot/blob/main/docs/appendix/CAC40_feb2020_1.png)

If the price is a bit farer, 97, then the extrema is considered to have changed the trend. For instance:

![Extrema considered but trend uncertain](https://github.com/psemdel/py-trading-bot/blob/main/docs/appendix/CAC40_feb2020_2.png)

However, the trend is set to uncertain as the reversal is not important. If the price is farer, 90, the trend is not anymore uncertain, it reversed. So in our example, the trend is not anymore bull but bear.

![Extrema confirmed, trend bear](https://github.com/psemdel/py-trading-bot/blob/main/docs/appendix/CAC40_feb2020_3.png)

This trend can be used to chose which direction to used for the orders. It can also allow a strategy variation depending on the trend.

The detection of the general trend is not easy. The present algorithm was optimized, but it cannot detect immediately a reversal.


