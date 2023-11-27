# Machine learning
The bot is perfectly able to use a machine learning algorithm to generate entries and exits signals. An examplary algorithm is provided in ml.py and the corresponding jupyter notebook ml.ipynb. 

In a similar way to strat.py first the algorithm is able to preprocess the price, with RSI, STOCH... for example. If preprocessing is set to false, the price alone is used as an input. After this signal is scaled and used for the training of model or the prediction. Presently, MLP and LSTM are implemented.

The preprocessing functions used are defined with features_name. The list is provided in the section below.

Keras and SKlearn are used, but it could be replaced by any other library. Only condition for the model to work with the bot is to generate entries and exits signals.

## Preselection
The model provided select the stock with the highest expected maximum in the next 10 days in the provided data set. Additionnaly, a mechanism is implemented to limit the number of orders by defining a threshold: if the estimation for the stock with the present maximum is not sufficiently above the previous candidate stock estimation, then we keep the old one.

# List of features
When a "_ent" is in the name, it means it is an entry signal, "_ex" means exit signal, without those suffix, the value is taken directly. This kind of values seem to work better than entry/exit signals with machine learning. The suffix "_RANK" means the rank of the stock compared to the other stock of the dataset for this parameter.

- MA_ent, MA_ex (period 5/15)
- KAMA_ent, KAMA_ex (on extrema of KAMA function)
- MFI (threshold 20/80)
- STOCH, STOCH_ent, STOCH_ex (threshold 20/80)
- WILLR
- SUPERTREND_ent, SUPERTREND_ex 
- BBANDS_BANDWIDTH, BBANDS_ent, BBANDS_ex
- RSI, RSI20_ent, RSI20_ex (threshold 20/80), RSI30_ent, RSI30_ex (threshold 30/70)
- ULTOSC
- GROW30 (increasing in value during past 30 days), GROW30_RANK
- GROW30_MA (same but on the moving average signal), GROW30_MA_RANK
- GROW30_DEMA (same but on the DEMA signal), GROW30_DEMA_RANK
- GROW50 (increasing in value during past 30 days), GROW50_RANK
- GROW50_MA (same but on the moving average signal), GROW50_MA_RANK
- GROW50_DEMA (same but on the DEMA signal), GROW50_DEMA_RANK
- GROW200 (increasing in value during past 30 days), GROW200_RANK
- GROW200_MA (same but on the moving average signal), GROW200_MA_RANK
- GROW200_DEMA (same but on the DEMA signal), GROW200_DEMA_RANK
- OBV
- AD
- MACD
- HIST (from MACD)
- DIVERGENCE (see predefined strategy documentation, compare the stock price variation to the index price variation)
- NATR
- HT_TRENDMODE
- MACRO_TREND (see trend_calculation documentation)
- PU_RESISTANCE (try to evaluate the distance from last resistance)
- PU_SUPPORT (try to evaluate the distance from last support)

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
