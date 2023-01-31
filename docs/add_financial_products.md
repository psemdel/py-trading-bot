# Adding financial products
The bot is delivered with a dump containing some stock exchanges and stocks, but you surely wants to add more.

After having started the bot click on "Admin panel" (http://localhost:8000/admin/). 

To add a stock exchange:

- Click on "add" close to "Stock exs"
- Give a name, a fee and the ib_ticker! For instance, Paris is SBF. If the ticker is wrong, the interface with Interactive broker won't work.

To add a stock (Action in the bot):

- Click on "add" close to "Actions"
- Symbol is the Yahoo Finance symbol. It is used as primary key. 
- IB Ticket is normally not needed, as normally it is the same or can be derived from the symbol. For instance, AAPL is both the symbol in YF and on IB. ENGI.PA is the symbol on YF, in IB it is only ENGI (the bot recognize the "."). It is required for the indexes though.
- Select the stock exchange, the currency and the category. Note that the category influence the behavior of the bot. Index cannot be traded directly. ETF are related to other products. 
- Etf long and Etf short are optional and intended for indexes mainly.
- Intro date is the date when the products was introduced at the stock exchange. If you want to calculate a strategy for the past x years and compare stocks in this range, it is important that they are available for the whole time range, the bot will filter the ones that were introduced too late.
- Delisting date, clear
- The delisted check can be used if the product is delisted, but also if you want to avoid trading it right now ;). 

# Report about another stock exchange
Let's suppose you want to produce a report about a stock exchange which is not included yet. For the example, let's take Hong Kong.

- Create the stock exchange and the related stocks
- Go in reporting/telegram.py create a new method:

    def daily_report_HK(self):
    
        print("writting daily report HK")
        report1=Report()
        report1.save()
        st=report1.daily_report_action("Hong Kong") #name you gave to your stock exchange
        
- Add it to the scheduler (still in telegram.py):

        tz_HK=ZoneInfo('Asia/Hong_Kong')
        self.do_weekday(time(16,00,tzinfo=tz_HK), self.daily_report_HK)
        
  A report will be create at 16h Hong Kong time. It will perform the "normal strategy" (see automatic orders help) on all stocks listed in the Hong Kong stock exchange in the database.
  
- If you want to use one of the strategy with preselection on the stock from Hong Kong, just add the following in the daily_report_HK method created before:

        report1.presel(st,"Hong Kong") #name you gave to your stock exchange
  
 

