# Adding a stock exchange
The bot is delivered with a dump containing some stock exchanges, but you surely wants to add more.

After having started the bot click on "Admin panel" (http://localhost:8000/admin/). 

To add a stock exchange:

- Click on "add" close to "Stock exs"

Following inputs can be defined:

- name: name of this stock exchange. 
- fees: fees associated with this stock exchange
- ib_ticker: ticker in IB. For instance, Paris is SBF. If the ticker is wrong, the interface with Interactive broker won't work.
- opening_time: opening time of this stock exchange in the timezone defined afterwards
- closing_time: closing time of this stock exchange in the timezone defined afterwards
- timezone: timezone of this stock exchange
- perform_order: boolean that determines if automatic orders in IB should be performed. If False, only manual trade is possible
- ib_auth: do you have enough permission in IB to perform trades in this stock exchange?
- strategies_in_use: select the strategies you want to use for this stock exchange, before closing. Overriden by those at sector level if presel_at_sector_level is true!
- strategies_in_use_intraday: select the strategies you want to use for this stock exchange, during the day. Overriden by those at sector level if presel_at_sector_level is true!
- presel_at_sector_level: if true, the strategy will be performed at sector level. Is true only for NYSE, as there are too many stocks in the S&P 500. You may want to use the same strategy on 5 bundles of 100 stocks instead of 1 strategy for 500 stocks.
- main_index: select the index related to this stock exchange 
- calc_report: should the report be calculated, useful to deactivate report about ETF stock exchanges

# Writing a report for the new stock exchange
The scheduler will generate automatically a report for all stock exchanges where at least a strategy is in use, 15 min before its closing. There is nothing to do.

To add a link to generate a report for this stock exchange manually on the home page, go to /reporting/templates/reporting/reports.html

Add a row:

```
<td><a href="{% url 'reporting:report' '[name of the new stock exchange]' %}">Write report for [name of the new stock exchange]</a></td>
```

That's all!

