# VIX index
The VIX index, short for CBOE Volatility Index, is an index that can be found in Yahoo finance (ticker ^VIX). It summarizes the volatility of the market in general.

Two functionality are related to this index:

##Alerting
The value of the VIX is continuously checked, if it exceeded the value defined in settings "VIX_ALERT_THRESHOLD", then an alert is sent.

    "CHECK_VIX":True,
    "VIX_ALERT_THRESHOLD":40,
    
##Selling all
If the value of the VIX exceeds "VIX_SELL_ALL_THRESHOLD" all stocks are immediately sold. To deactivate this function, set it to a high value (1000).

    "VIX_SELL_ALL_THRESHOLD":45,
    
##Backtesting
To backtest the influence of the "VIX_SELL_ALL_THRESHOLD" value, you can introduce the parameter vix_threshold in the calculation of strat and presel:

    ust=strat.StratG(period,symbol_index=symbol_index,vix_threshold=45
