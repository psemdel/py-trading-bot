# Reporting
By default, reports are written once a day, 15 minutes before market closing (in trading_bot/settings.py and see `"DAILY_REPORT_MINUTE_SHIFT":15, `). At the same time, order decisions are performed. Reports can also be written within the day, strategies "Intraday" must be selected for a stock exchange in the admin panel.

The whole logic for the writting of the report is in reporting/models.py The function populate_report() is responsible for filling the statistics. perform() will trigger the calculation of the strategies if they are selected for a given stock exchange in the admin panel.

Here, no report will be generated:

![Extrema confirmed, trend bear](https://github.com/psemdel/py-trading-bot/blob/main/docs/appendix/no_strat_selected.png)

Here, a daily report will be generated, but no intraday:

![Extrema confirmed, trend bear](https://github.com/psemdel/py-trading-bot/blob/main/docs/appendix/strats_selected.png)

The reports writting can be also triggered from the main page. The code used is however slightly different, are in this case the report writting script is synchronous with django, whereas the scheduled one is asynchronous.
