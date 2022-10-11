# Introduction
This trader bot automatizes orders on all kind of financial products, and is not targetting crypto. Objective is that it can run in autonomy. It is primarily a personal project, it must be seen as an example, not as a general framework or a bot ready to go.

Features implemented:

- Backstaging of complex strategies (including 101 Formulaic Alphas) using [vectorbtpro](https://vectorbt.pro/)
- Performing live automatically orders using the tested strategies and interactive brockers, thanks to ib_insync
- Send Telegram messages when performing an order
- Send Telegram alerts when the action price variation exceeds a certain threshold
- Writting at regular interval reports on the market, using Django and Celery with Redis
 
# Vision and comparison with other tools
I want to trade without having to spend hours every day watching at curves or read tweets to find out which product to trade and when to trade it. I want to be able trading American and European stocks. I want to receive alerts on my phone in case anything abnormal happens on my assets. I want to be able to use complex trading strategies, that can rely on machine learning for their design.

There are many similar tools out there, that have similar purposes that are certainly more complete and mature. Freqtrade for instance only trades crypto. If you need only American stocks, you can also use QuantConnect. MetaTrader can also be used, if your broker supports it. TradingView offers also similar services against quite high fees. In the end, it's up to you. 

# Structure
- core contains the strategies and all backstaging logic supported by vectorbt. Its indicator factory is extensively used (for more information read https://vectorbt.pro/tutorials/superfast-supertrend/)
- saved_cours contains some pre-saved data to perform backtesting. The jupyter notebooks in the root are there to perform this backtesting
- orders contains the Django models relative to orders and financial products. IB communication is handled also there
- reporting contains the Django models relative to reports
- trading_bot contains Django configuration

# Get started
For details, especially relative to pre-requisites, see [installation guide](https://github.com/psemdel/py-trading-bot/blob/main/installation_guide.md)
In short:

- Go in trading_bot/settings.py, set IB settings relative to port (don't forget to open your Api in this software), useIB_for_data to the correct value depending if you use Interactive brokers or not. Look at the settings, for instance for Telegram.
- In trading_bot/etc/ adapt the values in files (never commit those files!! Uncomment **/trading_bot/etc/ in .gitignore to avoid this drama):

    - DB_USER contains your database user
    - DB_SECRET contains your database password
    - DJANGO_SECRET contains your Django secret
    - TELEGRAM_TOKEN contains your Telegram bot token
    
- (optional) reimport the dump file using "python manage.py loaddata dump.rdb" to fill your database with some financial products: CAC40, DAX, Nasdaq100 and S&P 500.

When you are done:
- Click on start_bot.sh

# To do
Using USE_IB_FOR_DATA and PERFORM_ORDER on True is still in beta phase. For USE_IB_FOR_DATA, please note that you need the permission for all actions that you need to retrieve. One missing permission lead to the failure of the process.

# Deployment
Deployment of the bot on external machine has not been achieved yet for several reasons:

- If you use Interactive brokers, your trader workstation needs to be open on a machine which can communicate with the bot. As the login requires MFA, you need to be able to display the desktop of this machine. It requires a minimum of 4Gb ram, which exclude use of Raspberry pi. It is a challenge also for the security.
- Talib library, which is coded in C, need to be installed. In proved to be challenging on PaaS, like heroku for instance.
- Vertorbt is very heavy (docker image > 4 Gb). It excludes a deployment on Amazon lambda for instance.

# Disclaimer
Do not risk money which you are afraid to lose. USE THE SOFTWARE AT YOUR OWN RISK. THE AUTHORS AND ALL AFFILIATES ASSUME NO RESPONSIBILITY FOR YOUR TRADING RESULTS.
