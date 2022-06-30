# Introduction
This trader bot automatizes orders on all kind of financial products, and is not targetting crypto. Objective is that it can run in autonomy. It is primarily a personal project, it must be seen as an example, not as a general framework.

Features implemented:

- Backstaging of complex strategies (including 101 Formulaic Alphas) using vectorbtpro
- Performing live automatically orders using the tested strategies and interactive brockers, thanks to ib_insync
- Send Telegram messages when performing an order
- Send Telegram alerts when the action price variation exceeds a certain threshold
- Writting at regular interval reports on the market, using Django and Celery with Redis
 
# Structure
- core contains the strategies and all backstaging logic supported by vectorbt. Its indicator factory is extensively used (for more information read https://vectorbt.pro/tutorials/superfast-supertrend/). 
- saved_cours contains some pre-saved data to perform backtesting. The jupyter notebooks in the root are there to perform this backtesting
- orders contains the Django models relative to orders and financial products. IB communication is handled also there
- reporting contains the Django models relative to reports
- trading_bot contains Django configuration

# Get started
Configuration:

- Go in trading_bot/settings.py, set IB settings relative to port (don't forget to open your Api in this software), useIB_for_data to the correct value depending if you use Interactive brokers or not. Look at the settings, for instance for Telegram.
- In trading_bot/etc/ put your Django key (whatever you want), your telegram token and your database credentials. I used postgresQL but it does not matter (read https://docs.djangoproject.com/en/4.0/ref/databases/)
- (optional) reimport the dump file using "python manage.py loaddata dump.rdb" to fill your database with some financial products: CAC40, DAX and Nasdaq100

When you are done:
- Click on start_bot.sh

# Deployment
Deployment of the bot on external machine has not been achieved yet for several reasons:

- If you use Interactive brokers, your trader workstation needs to be open on a machine which can communicate with the bot. As the login requires MFA, you need to be able to display the desktop of this machine. It requires a minimum of 4Gb ram, which exclude use of Raspberry pi. It is a challenge also for the security.
- Talib library, which is coded in C, need to be installed. In proved to be challenging on heroku for instance
- Pandas is very heavy. It excludes a deployment on Amazon lambda for instance
- In its present version, you need to start a Redis server, Celery, Django and Interactive Brokers at the same time. So it is a bit complex.

# Open points
- Tests

# Disclaimer
Do not risk money which you are afraid to lose. USE THE SOFTWARE AT YOUR OWN RISK. THE AUTHORS AND ALL AFFILIATES ASSUME NO RESPONSIBILITY FOR YOUR TRADING RESULTS.
