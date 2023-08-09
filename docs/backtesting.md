# Backtesting
The bot heavily relies on vectorbt, which is designed to perform backtesting. 

To backtest your strategy with historical data (see [download data](https://github.com/psemdel/py-trading-bot/blob/main/docs/download_data.md)), use the Jupyter notebooks:

- strat.ipynb to backtest strategy for one stock
- presel.ipynb to backtest strategy for several stocks
- presel_classic.ipynb to backtest classical portfolio optimization strategy from libraries like PortfolioOptimizer and universal-portfolios which integrated in vbt

Advantage of backtesting from downloaded files:

1. You don't have to download the data again and again
2. They don't change. It makes comparison between strategies easier

Additionally, you can backtest with recent prices, for instance last 3 years, in the notebooks live.ipynb. It includes also the function scan_presel_all() that will calculate the return of each preselection strategies for each exchanges obtained during the past x days (90 by default). If you have the impression that a strategy does not perform so well right now, it will confirm your doubt or not. The list of strategies tested is defined in trading_bot/settings.py in:

    "STRATEGIES_TO_SCAN":["PreselVol","PreselRealMadrid","PreselRetard","PreselRetardMacro","PreselDivergence",
          "PreselDivergenceBlocked","PreselWQ7","PreselWQ31","PreselWQ53","PreselWQ54"],    
    
Note: for strategy on one stock, testing all stocks in the exchange would not make much sense, that's why it is not included in this scan.
