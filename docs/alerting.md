# Alerting
An automatic alerting via Telegram can be performed by the bot. All stocks that is in your portfolio (PF in admin panel) or in your IB portfolio, will be checked periodically during stock exchange opening time.

1. You need a bot in telegram (search on internet, bot_father...). And save its token in trading_bot/etc/TELEGRAM_TOKEN. Think about starting it.
2. Time interval for checking is set in trading_bot/settings.py in TIME_INTERVAL_CHECK, the number is in minutes. Please take into account, that the checking itself takes some time.
3. By default, the algorithm check the change compared to closing price from the day before, like on any portal. Threshold for alerting and alarming are defined in trading_bot/settings.py. ALERT_THRESHOLD and ALARM_THRESHOLD. They are set in percents.
4. The alerts will recover if the change comes below the threshold-ALERT_HYST. It is an hysteresis to avoid alerting and recovering at high frequency if the price oscillates around the threshold.

The whole alerting mechanism is coded in reporting/telegram.py. The telegram bot is combined with the scheduler and run asynchronous from Django in a Redis server, thanks to Celery.

The script test/telegram_minimal.ipynb can help you testing your telegram bot.


