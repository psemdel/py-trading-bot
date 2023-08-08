# Orders
## Automatic orders
### Introduction
One of the most important features of the bot is the possibility to perform orders automatically. To prevent the bot to run orders, when you don't want it, the permission is granted at diverse level: 

- bot level
- strategy level
- stock exchange level
- stock level

Most restrictive constraint is applied. So if any permission is set to False, the order won't be performed automatically.

### Pre-requisites
1. To do so, you need to open IB Trader Workstation and login when operating the bot. 

    The API must be enabled [documentation](https://interactivebrokers.github.io/tws-api/initial_setup.html).
    
2. You need the permission to receive the data from data for the product you want to order. See [IB Market Data](https://www.interactivebrokers.com/en/pricing/research-news-marketdata.php). 

    As you may want to use an automatic strategy for products where you don't have the right, the bot can still inform you via telegram to perform an order "manually". For this go in the admin pannel, and set in the stock exchanges the check "Ib auth" if you have the permission for it. 
   
### Bot level
In trading_bot/settings.py, the parameter `PERFORM_ORDER` must be set to True.

Additionally, in the settings, the broker to use to perform orders is defined:

    ```
    "USED_API_DEFAULT":{
        "orders": os.environ.get("USED_API_FOR_ORDER_PERF","IB"), #"IB", "MT5", "TS" or "CCXT" (YF does not allow performing orders)
        "alerting":os.environ.get("USED_API_FOR_DATA_ALERTING","IB"), #"IB", "YF", "MT5", "TS" or "CCXT"
        "reporting":os.environ.get("USED_API_FOR_DATA_REPORTING","YF"), #"IB", "YF", "MT5", "TS" or "CCXT"
        }
    ```

The `orders` must on be equal to `IB` to use IB for the trades. As written, you can also define an environment variable `USED_API_FOR_ORDER_PERF` that will overwrite the default setting.

### Strategy level
In the admin panel, the strategy field `Perform order` must be checked (=True).

### Stock exchange level
In the admin panel, the stock exchange field `Perform order` must be checked (=True).

### Stock level
Additionally, a black list of stocks can be configured in trading_bot/settings.py with IB_STOCK_NO_PERMISSION. It covers especially complex products, where permission is difficult to get.

### Order execution
The strategies are calculated during the creation of a report. Report is created once a day 15 minutes before stock exchange closing (see telegram.py). Alternatively, it can be generated during the day (Intraday) every x minutes. After calculation of the strategies, orders will be performed. 

## Manual orders
When the condition to perform the order automatically are not fullfiled, the order is considered manual. A telegram message is sent to you. You can then perform the order by another broker.

It is considered that you performed the order! (The bot has basically no mean to check)

If you didn't, you need to adapt your portfolio manually. Go to home page and click on `portfolio`, button on the bottom allows you to correct the state.
    
## Order (object)
An object `Order` is present in the database. One is created every time an order is performed, automatically or not. It is automatic an you don't need to interact manually with it in the database.










