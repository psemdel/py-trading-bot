# Introduction
This trader bot automatizes orders on all kind of financial products, and is not targetting crypto. Objective is that it can run in autonomy. It is primarily a personal project, it must be seen as an example, not as a general framework or a bot ready to go.

Features implemented:

- Backstaging of complex strategies (including [101 Formulaic Alphas](https://arxiv.org/pdf/1601.00991.pdf)) using [vectorbtpro](https://vectorbt.pro/), on historical data but also on recent data.
- Performing live automatically orders using the tested strategies and interactive brockers, thanks to ib_insync
- Send Telegram messages when performing an order
- Send Telegram alerts when the action price variation exceeds a certain threshold. Note: last version from IB mobile app has also this function.
- Writting at regular interval reports on the market, using Django and Celery with Redis
- Perform strategy optimization on data set
 
# Vision and comparison with other tools
I want to trade without having to spend hours every day watching at curves or read tweets to find out which product to trade and when to trade it. I want to be able trading American and European stocks. I want to receive alerts on my phone in case anything abnormal happens on my assets. I want to be able to use complex trading strategies, that can rely on machine learning for their design.

There are many similar tools out there, that have similar purposes that are certainly more complete and mature. Freqtrade for instance only trades crypto. If you need only American stocks, you can also use QuantConnect. MetaTrader can also be used, if your broker supports it. TradingView offers also similar services against quite high fees. In the end, it's up to you. 

# Structure
The bot run with Django, however backtesting works without Django running. It explains why there are methods for both. Especially the Stocks are defined in Django admin panel, for when Django runs, and once in core/constants.py, when not. Same applies for general configuration which is in Django admin panel and settings.py.

The file structure is as following:
- core contains the strategies and all backstaging logic supported by vectorbt. Its indicator factory is extensively used (for more information read https://vectorbt.pro/tutorials/superfast-supertrend/)
- saved_cours contains some pre-saved data to perform backtesting. The jupyter notebooks are there to perform this backtesting
- orders contains the Django models relative to orders and financial products. IB communication is handled also there
- reporting contains the Django models relative to reports
- trading_bot contains Django configuration

# Get started
For installation see [installation guide](https://github.com/psemdel/py-trading-bot/blob/main/docs/installation_guide.md).

# Deployment
Deployment of the bot on external machine has not been achieved yet for several reasons:

- If you use Interactive brokers, your trader workstation (TWS) or IB Gateway needs to be open on a machine which can communicate with the bot. As the login requires MFA, you need to be able to display the desktop of this machine. You can consider setting up on a powerful Raspberry with IB Gateway. However, it stays challenging as the docker image of the bot is very heavy.
- Talib library, which is coded in C, need to be installed. In proved to be challenging on PaaS, like heroku for instance.
- Vertorbt is very heavy (docker image > 4 Gb). It excludes a deployment on Amazon lambda for instance.

# Disclaimer
Do not risk money which you are afraid to lose. USE THE SOFTWARE AT YOUR OWN RISK. THE AUTHORS AND ALL AFFILIATES ASSUME NO RESPONSIBILITY FOR YOUR TRADING RESULTS, EVEN IF CAUSED BY A BUG OF THE SOFTWARE.
