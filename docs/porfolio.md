# Stock status

The bot keeps track of the portfolio you own. For each stock, a stock status object is created automatically. It's attribute quantity saves how much stocks you have.



In the bot, the concept of portfolio is used. You can look at the content of the portfolio by clicking on the button "Portfolio" on the starting page.

One portfolio is created for each combination stock exchange / strategy / direction / sector. There is for instance a portfolio for Paris, normal, long, undefined. It allows keeping track of the stock presently owned for a specific strategy. For instance, for the divergence strategy, a strategy in core/strat.py will be used to determine the exit of the stocks.

There is no synchronisation between the portfolio you own in IB and the one in the bot for following reasons :

* If a stock is in IB and not in the bot, there is no mean to know because of which strategy it was bought
* If a stock is missing in IB, there could be unclarity about which strategy was concerned
* You may want to perform trading outside of IB with the bot

It is actually a difficulty, as you need to perform this synchronisation manually if you want to get the best of the bot. So if you sell manually a stock, you should update the portfolio. Inversely, if the bot tell you to sell/buy a stock, you should do it, otherwise the will be a discrepency between the portfolio in the bot and the reality.



