# Adding financial products
The bot is delivered with a dump containing some stocks and indexes, but you surely wants to add more.
Important note: the stocks are, still, named action in the bot. It is the French name for stock, and it will be corrected at some point.

After having started the bot click on "Admin panel" (http://localhost:8000/admin/). 

To add a stock (called Action in the bot):

- Click on "add" close to "Actions"

Following inputs can be defined:

- symbol: YF ticker, used as primary key
- ib_ticker_explicit: IB ticker, if it is necessary to give it explicitely. For instance for symbol AAPL or MC.PA, it will be deduced from the symbol, however for indexes it needs to be defined separately
- name: name of the product
- stock_ex: at which stock exchange is the product listed
- currency: currency in which the product is listed by this exchange
- category: is it a stock, an index, an etf...
- sector: sector according to GICS classification of the product. Important for NYSE stocks, as otherwise they are too many
- delisted: is the stock delisted? Redundant with delisting_date, but can also be a convenient way to exclude this stock from all calculation.
- etf_long: what is the ETF in the long direction associated with the product. Normally only for index
- etf_short: what is the ETF in the short direction associated with the product. Normally only for index     
- intro_date: when was the product introduced on the stock exchange
- delisting_date: when was the product delisted from the stock exchange

# Adding the products to strategies
Strategies using a preselection will perform the preselection in all stocks for a stock exchange by default. So there is no need to do anything.
For stock exchange where the option presel_at_sector_level is True, the preselection will be performed for all stocks in a defined sector.

For underlying strategies, the stocks need to be added in the corresponding "strat candidates". Go in the admin panel and select the stock name in the strat candidate. Note: to select several press ctrl.

