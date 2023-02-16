# Pre-requisites
For this installation, it is assumed that python with a version >3.8, git and pip are already installed.

* [Python >= 3.8.x](http://docs.python-guide.org/en/latest/starting/installation/)
* [pip](https://pip.pypa.io/en/stable/installing/)
* [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)

# Vectorbt
I recommend using [vectorbt](https://vectorbt.dev/) in its [pro version](https://vectorbt.pro/) (requires fee), but basically vectorbt "dev" is the same with less features (I will create a branch for the bot using vectorbt normal). Install it with:

- Vectorbt "normal"

```sh
pip install -U "vectorbt[full]"
```

- Vectorbtpro

```sh
pip install -U "vectorbtpro"
```

It will install some other dependencies needed for the bot, for instance: pandas, numpy, python-telegram-bot and TA-Lib. 
Note: you have to choose between the pro and the dev versions. You can have both installed at the same time.

# Django
Afterwards, you need to install [Django](https://www.djangoproject.com/) on one side and [Redis](https://redis.io/) (or equivalent) with [Celery](https://docs.celeryq.dev/en/stable/getting-started/introduction.html) for the worker. asyncio is used for asynchronous tasks. ib_insync is a library to communicate with interactive brokers.

```sh
pip install django celery[redis] asyncio ib_insync whitenoise
```

# Clone from git
Pull the project from git:

```
git clone https://github.com/psemdel/py-trading-bot.git
```

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
Go in trading_bot/settings.py, set IB settings relative to port (don't forget to open your Api in this software and to uncheck the "read-only" setting). Note that TWS and IB Gateway have different ports.


    ## IB configuration
    IB_LOCALHOST='127.0.0.1'
    IB_PORT=7496


Set the settings you want for Telegram


    ## Configuration of Telegram ##
    PF_CHECK=True
    INDEX_CHECK=True
    REPORT_17h=True #for Paris and XETRA
    REPORT_22h=True
    HEARTBEAT=False # to test telegram

    ALERT_THRESHOLD=3 #in %
    ALARM_THRESHOLD=5 #in %
    ALERT_HYST=1 #margin to avoid alert/recovery at high frequency

    TIME_INTERVAL_CHECK=10 #in minutes, interval between two checks of pf values


Set USE_IB_FOR_DATA to the correct value depending if you use Interactive brokers or not. If you use IB for the data, also adapt the list of stock exchanges where you have access, respectively no access to avoid bugs.


    ## Order settings ##
    USE_IB_FOR_DATA=True #use IB for Data or YF
    IB_STOCKEX_NO_PERMISSION=["IBIS","EUREX","NASDAQ IND"]
    IB_STOCKEX_PERMISSION=["SMART","SBF","NYSE","BVME"]
    IB_STOCK_NO_PERMISSION=["NDX"]



In trading_bot/etc/ adapt the values in files (never commit those files!! Uncomment **/trading_bot/etc/ in .gitignore to avoid this drama):

    - DB_USER contains your database user
    - DB_SECRET contains your database password
    - DJANGO_SECRET contains your Django secret
    - TELEGRAM_TOKEN contains your Telegram bot token

# Import the dump (optional)
Reimport the dump file using "python manage.py loaddata dump.rdb" to fill your database with some financial products: CAC40, DAX, Nasdaq100 and S&P 500.

# Start the bot
Click on start_bot.sh
Note the admin panel from Django that allows creating finance products.












