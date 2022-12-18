# Reporting
By default, reports are written once a day, just before market closing. At the same time, order decisions are performed.

1. To change the time of the report writting, go in reporting/telegram.py in the function MyScheduler. The times are defined UTC.
2. The whole logic for the writting of the report is in reporting/models.py The function populate_report() is responsible for filling the statistics. Most of the other functions are there to decide to perform or not orders.

The reports writting can be also triggered from the main page. The code used is however slightly different, are in this case the report writting script is synchronous with django, whereas the scheduled one is asynchronous.
