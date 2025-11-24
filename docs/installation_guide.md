# Pre-requisites
For this installation, it is assumed that python with version 3.12, git and pip are already installed.

* [Python >= 3.12.x](http://docs.python-guide.org/en/latest/starting/installation/)
* [pip](https://pip.pypa.io/en/stable/installing/)
* [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)

# Set up your venv (optional)
Set up your virtual environment with the tool of your choice.

Adapt the first line of start_bot.sh depending on your venv settings:

```
#start your venv
source <your path>/Anaconda/bin/activate
conda activate <venv name>
```

# Vectorbt
The bot requires [vectorbt](https://vectorbt.dev/) in its [pro version](https://vectorbt.pro/) (requires fee). Install it with:

- Vectorbtpro

```
pip install -U "vectorbtpro"
```

Note: it is clearly imaginable to use the bot with the basic version of vbt, but it would need some adaptions.

It will install some other dependencies needed for the bot, for instance: pandas, numpy, python-telegram-bot and TA-Lib. 

# Clone from git
Pull the project from git:

    git clone https://github.com/psemdel/py-trading-bot.git

# Django
Afterwards, you need to install [Django](https://www.djangoproject.com/) on one side and [Redis](https://redis.io/) (or equivalent) with [Celery](https://docs.celeryq.dev/en/stable/getting-started/introduction.html) for the worker. ib_insync is a library to communicate with interactive brokers. They are defined in requirements.txt. Note that you can comment out the keras installation, if you don't want to use the machine learning functions.

    pip install -r requirements.txt

# Database
You can perfectly use SQlite as Database, then go in trading_bot/settings.py and replace DATABASES through this snippet. Then there is no preliminary steps.

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

By default however, privilege a more production oriented database. By default, PostgresQL is used. [To install PostgresQL](https://www.postgresql.org/download/). In this case, you have to create a database in PostgresQL, an user and grant priviledges for the database to this user. 

Corresponding code in trading_bot/settings.py is the one used by default:

    DATABASES = {
    'default': {
         'ENGINE': 'django.db.backends.postgresql',
         'NAME': 'pgtradingbotdb',
         'USER': DB_USER,
         'PASSWORD': DB_SECRET_KEY,
         'HOST': 'localhost',
         'PORT': '',
     }
    }
    
pgtradingbotdb is the name of the database in postgres (but you can use whatever you want), DB_USER is the user you use in postgres, DB_SECRET_KEY the corresponding password. 

# Telegram
If you want to use Telegram to receive alert, you first need to create a bot in Telegram with BotFather. Internet is full of explanation on the topic. Note your token.

Note: think of starting it with the command /start in Telegram.

# Jupyter (optional)
It is optional, but you Jupyter to read the Jupyter notebooks. Vectorbt is very good to visualize strategies in Jupyter, it would be too bad not to use this possibility.

# Configuration
The configuration of the bot is done principally in:
    
    The file trading_bot/settings.py
    The admin panel of Django
    
However, you may need to modify file like core/constants.py, core/stratL.py... to have exactly the desired behavior. I am still working to centralize everything.

Go in trading_bot/settings.py, set IB settings relative to port (don't forget to open your Api in this software and to uncheck the "read-only" setting). Note that TWS and IB Gateway have different ports.

    "IB_LOCALHOST":'127.0.0.1',
    "IB_PORT": os.environ.get("IB_PORT",7496), #IB Gateway 4001, TWS 7496
    
Set the settings you want for Telegram

    ## Configuration of Telegram ##
    "PF_CHECK":True,
    "INDEX_CHECK":True,
    "REPORT":True, #for Paris and XETRA
    "INTRADAY":False,
    "HEARTBEAT":False, # to test telegram
    "HEARTBEAT_IB":False, # to test telegram
    "UPDATE_SLOW_STRAT":True, 

    "ALERT_THRESHOLD":3, #in %
    "ALARM_THRESHOLD":5, #in %
    "ALERT_HYST":1, #margin in % to avoid alert/recovery at high frequency, so if ALERT_THRESHOLD=3 and ALERT_HYST=1
                #then the alert will be deactivated when the price variation is 2% (3-1)

    "TIME_INTERVAL_CHECK":10, #in minutes, interval between two checks of pf values
    "TIME_INTERVAL_UPDATE":60,
    "TIME_INTERVAL_INTRADAY":15,

    "OPENING_CHECK_MINUTE_SHIFT":5,
    "DAILY_REPORT_MINUTE_SHIFT":15,    

Set USED_API_DEFAULT to the correct value depending if you use Interactive brokers or not. Three parameters are defined: 

- Orders: which API should perform your orders
- Alerting: from which API should the data be retrieved within the day to generate alert
- Reporting: from which API should the data be retrieved for report generation

If you use IB for the data, a list of stocks where you have no access can be defined in IB_STOCK_NO_PERMISSION. The permission in IB for the stock exchanges is set with the parameter ib_auth which can be accessed in the admin panel. 

    "USED_API_DEFAULT":{
        "orders": os.environ.get("USED_API_FOR_ORDER_PERF","IB"), #"IB", "MT5", "TS" or "CCXT" (YF does not allow performing orders)
        "alerting":os.environ.get("USED_API_FOR_DATA_ALERTING","IB"), #"IB", "YF", "MT5", "TS" or "CCXT"
        "reporting":os.environ.get("USED_API_FOR_DATA_REPORTING","YF"), #"IB", "YF", "MT5", "TS" or "CCXT"
        },
    "IB_STOCK_NO_PERMISSION":["^NDX","^DJI","^IXIC"],    

In trading_bot/etc/ adapt the values in files (never commit those files!! Uncomment **/trading_bot/etc/ in .gitignore to avoid this drama):

    - DB_USER contains your database user
    - DB_SECRET contains your database password
    - DJANGO_SECRET contains your Django secret
    - TELEGRAM_TOKEN contains your Telegram bot token
    
I would recommend to leave TIME_ZONE = 'UTC' except if you know what you are doing. 

# Import the dump (optional)
Reimport the dump file using "python manage.py loaddata dump.json" to fill your database with some financial products: CAC40, DAX, Nasdaq100 and S&P 500.

# Start IB (if applicable)
Start interactive broker, if you want to trade with it. This step is optional.

# Start the bot



Click on start_bot.sh

I recommend to open it in a terminal, so you can see the console messages and can close it more easily. Don't open several instances of the bot at the same times, it does not work!
When starting the bot, the message appearing will relate to Django, Redis, Telegram (see [example of starting message](https://github.com/psemdel/py-trading-bot/blob/main/docs/appendix/start_messages.txt). Afterwards a message from the scheduler defining which job will run at which time will appear. Later the alerting check will run every few minutes depending on the setting. It shows:

     0%|          | 0/1 [00:00<?, ?it/s]kPoolWorker-2] 
     AAPL:   0%|          | 0/1 [00:00<?, ?it/s]ker-2] 
     AAPL: 100%|##########| 1/1 [00:00<00:00,  8.02it/s]
     AAPL: 100%|##########| 1/1 [00:00<00:00,  8.01it/s]
     
If everything goes well, your Telegram should display a message "I'm back online". If not, type "/start" in Telegram, it will add your chat_id to the list.

Note: the admin panel from Django that allows creating finance products.












