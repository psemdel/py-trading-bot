#Functions
The file start_bot.sh starts the bot. It contains some fundamental commands, which is helpful to understand. Some other basic commands are explained.

##Django
The basic command to start a Django server, which is in our case a web and application server, is:

    python3 manage.py runserver
    
Other commands, that are important, are:

    python3 manage.py makemigrations
     
Which define the migration to be performed, if the models files (in reporting and orders) are changed.

    python3 manage.py migrate
   
Which applies the migration defined before.

##Redis and Celery
Redis is a no-sql database which is used here as a queue. It is started with:

    redis-server
      
Celery is the library which is used to manage the asynchronous tasks which put in the queue. Celery settings are put in trading_bot/settings.py. The trading_bot/celery.py is perfectly standard. The Celery server is started with:

    celery -A trading_bot worker -l info


Functions are declared asynchronous with the decorator @shared_task(bind=True) in the code.

##Opening the bot in the browser
To start the telegram part of the bot, the command is:

    xdg-open http://localhost:8000/start_bot

It must be performed after the Celery server is launched, which itself requires the Redis server.

Note: Don't start several times the bot! Telegram does not support it. If it happens, close all instances of py-trading-bot before starting it again.

##Kubernetes folder
The Kubernetes manifests, in the folder with the same name, create the DB, Redis and Django servers and start them. The commands are the same as those described above.

##Closing the bot
To stop the bot, close the terminal where you opened it. If you started it in the background (not recommended), close the process.

