import numbers
from django.db import models
from django.db.models import Q

from trading_bot.settings import _settings

import datetime
import logging
logger = logging.getLogger(__name__)

import sys
if sys.version_info.minor>=9:
    import zoneinfo
    from zoneinfo import ZoneInfo
else:
    import backports.zoneinfo as zoneinfo
    from backports.zoneinfo import ZoneInfo
    
tz_Paris=ZoneInfo('Europe/Paris')

all_tz=[]
for tz in zoneinfo.available_timezones():
    all_tz.append((tz,tz))
all_tz=sorted(all_tz)  

'''
This file contains the models for the orders

The logic to perform them in the different platforms is in ib.py
'''
def check_if_index(action):
    """
    Check if a product is an index
    
    Arguments
    ----------
    action: stock to be checked
    """   
    if action.category==ActionCategory.objects.get(short="IND"):
        return True
    else:
        return False

def check_ib_permission(symbols: list, verbose: bool=True):
    '''
    Populate USED_API from USED_API_DEFAULT
    Check if IB can be used, otherwise YF is the fallback. For CCXT, MT5 and TS there is nothing to check.
    
    Needs to be performed for each set of symbols reported

    Arguments
    ----------
       symbols: list of YF tickers
    '''
    for k, v in _settings["USED_API_DEFAULT"].items():
        if v in ["CCXT","MT5","TS"]:
            _settings["USED_API"][k]=v
        elif v=="IB":
            if symbols is None:
                #then populate only if it is empty
                if _settings["USED_API"][k]=="": 
                    _settings["USED_API"][k]="IB"
            else:
                for symbol in symbols:
                    if symbol in _settings["IB_STOCK_NO_PERMISSION"]:
                        if verbose:
                            logger.info("symbol " + symbol + " has no permission for IB")
                        _settings["USED_API"][k]="YF"
                        break
                    
                    a=Action.objects.get(symbol=symbol)      
                    if a.stock_ex.ib_auth==False:
                        if verbose:
                            logger.info("stock ex " + a.stock_ex.ib_ticker + " has no permission for IB for "+k + " impacting: "+symbol)
                        _settings["USED_API"][k]="YF"
                        break
        elif v=="YF":
            _settings["USED_API"][k]=v
    
def get_exchange_actions(exchange:str,sec: str=None):
    '''
    Get lists of actions for the reporting

    Arguments
    ----------
        exchange: name of the stock exchange
        sec: name of the sector
    '''
    cat=ActionCategory.objects.get(short="ACT")
    
    try:
        stock_ex=StockEx.objects.get(name=exchange)
    except:
        raise ValueError("Stock exchange: "+str(exchange)+" not found, create it in the admin panel")
    
    c1 = Q(category=cat)
    c2 = Q(stock_ex=stock_ex)
    c3 = Q(delisted=False) #to be removed
    
    if stock_ex.presel_at_sector_level and sec is not None:
        action_sector, _=ActionSector.objects.get_or_create(name=sec)
        c4 = Q(sector=action_sector)
        actions=Action.objects.filter(c1 & c3 & c4) #c2 & no actual reason, but I use mix of Nasdaq and NYSE for sector
    else:
        actions=Action.objects.filter(c1 & c2 & c3)
        
    if len(actions)==0: #fallback for EUREX for instance
        cat=ActionCategory.objects.get(short="IND")
        c1 = Q(category=cat)
        actions=Action.objects.filter(c1 & c2 & c3)

    if _settings["USED_API"]["reporting"]=="":
        check_ib_permission([a.symbol for a in actions])

    return actions

def period_YF_to_ib(period: str): #see also split_freq_str in vbt
    '''
    Conversion between input from YF and IB for the period
    For instance transform "10 d" in "10 D"
    
    Arguments
    ----------
        period: time period for which data should be downloaded
    '''
    period_ib=None
    if period is not None:
        fig= ''.join(x for x in period if x.isdigit())
        if period.find("d")!=-1:
            period_ib=fig +" D"
        elif period.find("mo")!=-1:
            period_ib=fig +" M"
        elif period.find("y")!=-1:
            period_ib=fig +" Y"  
    
    return period_ib


def interval_YF_to_ib(interval: str):
    '''
    Conversion between input from YF and IB for the interval
    Time period of one bar. Must be one of: ‘1 secs’, ‘5 secs’, ‘10 secs’ 15 secs’, ‘30 secs’, ‘1 min’, ‘2 mins’, ‘3 mins’, ‘5 mins’, ‘10 mins’, ‘15 mins’, ‘20 mins’, ‘30 mins’, ‘1 hour’, ‘2 hours’, ‘3 hours’, ‘4 hours’, ‘8 hours’, ‘1 day’, ‘1 week’, ‘1 month’.

    Arguments
    ----------
        interval: time interval for which data should be downloaded
    '''
    if interval is None:
        res='1 day'
    else:
        fig= ''.join(x for x in interval if x.isdigit())
        if interval.find("m")!=-1:
            res=fig +" mins"
        elif interval.find("h")!=-1:
            res=fig +" hours"
        elif interval.find("d")!=-1:
            res=fig +" day"
        else:
            res='1 day'
            
    return res
                 
class Action(models.Model): 
    '''
    Action means stock in French
    Index is like stock (but it had to be separated, as an index cannot be bought directly)
    
    Attributes
   	----------
    symbol: YF ticker, used as primary key
    ib_ticker_explicit: IB ticker, if it is necessary to give it explicitely. For instance for symbol AAPL or MC.PA
                        it will be deduced from the symbol, however for indexes it needs to be defined separately
    name: name of the product
    stock_ex: at which stock exchange is the product listed
    currency: currency in which the product is listed by this exchange
    category: is it a stock, an index, an etf...
    sector: sector according to GICS classification of the product. Important for NYSE stocks, as otherwise they are too many
    delisted: is the stock delisted?
    etf_long: what is the ETF in the long direction associated with the product. Normally only for index
    etf_short: what is the ETF in the short direction associated with the product. Normally only for index     
    intro_date: when was the product introduced on the stock exchange
    delisting_date: when was the product delisted from the stock exchange
    ''' 
    symbol=models.CharField(max_length=15, blank=False, primary_key=True)
    ib_ticker_explicit=models.CharField(max_length=15, blank=True,default="AAA")
    name=models.CharField(max_length=100, blank=False)
    stock_ex=models.ForeignKey('StockEx',on_delete=models.CASCADE)
    currency=models.ForeignKey('Currency',on_delete=models.CASCADE)
    category=models.ForeignKey('ActionCategory',on_delete=models.CASCADE,blank=True, null=True)
    sector=models.ForeignKey('ActionSector',on_delete=models.CASCADE,blank=True,null=True)
    delisted=models.BooleanField(blank=False,default=False)
    etf_long=models.ForeignKey('self',on_delete=models.CASCADE,related_name='etf_long2',blank=True,null=True)
    etf_short=models.ForeignKey('self',on_delete=models.CASCADE,related_name='etf_short2',blank=True,null=True)
    
    intro_date=models.DateTimeField(null=True, blank=True, default=None)
    delisting_date=models.DateTimeField(null=True, blank=True, default=None)
    
    class Meta:
        ordering = ["name"]
        
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  
        StockStatus.objects.get_or_create(action=self) 
        
    def ib_ticker(self):
        if self.ib_ticker_explicit!="AAA" and self.ib_ticker_explicit is not None:
            return self.ib_ticker_explicit
        else:
            t=self.symbol.split(".")
            return t[0]      
        
    def __str__(self):
        return self.name
   
def filter_intro_sub(
        a: Action,
        y_period: numbers.Number
        )-> bool:
    '''
    Filter not introduced or delisted products from a list

    Arguments
    ----------
           a: Action to be tested
           y_period: period of time in year where we need to check backward from now
    '''  
    td=datetime.datetime.today()
    if y_period is None:
        limit_date_intro=td
    else:
        if td.month==2 and td.day==29: #29th feb
            tdday=28
        else:
            tdday=td.day
        limit_date_intro=datetime.datetime(td.year-y_period,td.month,tdday,tzinfo=tz_Paris) #time zone not important here but otherwise bug
        limit_date_delisted=datetime.datetime(td.year,td.month,td.day,tzinfo=tz_Paris) #today tz aware

    if a.intro_date is not None: #should come from database
        if a.intro_date>limit_date_intro :
           return False
    if a.delisting_date is not None:
        if a.delisting_date<limit_date_delisted :
           return False
    return True

class StockStatus(models.Model):
    '''
    Complement action, separated from action as Action contains the essence of the action, here it is some that the user can change
    
    Attributes
   	----------
    action: product associated with this status
    quantity: quantity of this stock that we own. Can be positive or negative
    order_in_ib: is the order manual (then we have no change to retrieve it using IB) or in IB?
    '''
    action = models.OneToOneField(
        Action,
        on_delete=models.CASCADE,
        primary_key=True,
    )
    quantity=models.FloatField(blank=True,null=True,default=0) 
    strategy=models.ForeignKey('Strategy',on_delete=models.CASCADE,blank=True,null=True)
    order_in_ib=models.BooleanField(blank=False,default=True)

    class Meta:
        ordering = ["action__name"]
        
    def __str__(self):
        return self.action.name    
    
def action_to_short(action):
    ss = StockStatus.objects.get(action=action)
    return ss.quantity<0  

def filter_intro_action(
        input_actions: list,
        y_period: numbers.Number
        )-> list:
    '''
    Filter not introduced or delisted products from a list

    Arguments
    ----------
    input_actions: list of products to be tested
    y_period: period of time in year where we need to check backward from now
    '''
    actions=[]
    for a in input_actions:
        if filter_intro_sub(a,y_period):
            actions.append(a)   
    return actions

### Data retrieval ###
def exchange_to_index_symbol(exchange):
    '''
    Determine which main index corresponds to a stock exchange

    Arguments
    ----------
    exchange: name of the stock exchange
    '''
    if type(exchange)==str:
        stock_ex=StockEx.objects.get(name=exchange)
    elif type(exchange)==StockEx:
        stock_ex=exchange
    else:
        raise ValueError("exchange has the wrong type")
    
    if stock_ex.main_index is None:
        return ["COMP","^IXIC"]
    else:
        return [stock_ex.main_index.ib_ticker(),stock_ex.main_index.symbol]

def action_to_etf(
        action: Action,
        short: bool
        ) -> Action:
    '''
    If the provided product is an index, will return the corresponding ETF

    Arguments
    ----------
    action: product
    short: if the products are presently in a short direction
    ''' 
    if action.category==ActionCategory.objects.get(short="IND"):
        if short:
            return action.etf_short
        else:
            return action.etf_long
    return action

def symbol_to_action(symbol)-> Action:
    '''
    Return action corresponding to a YF ticker

    Arguments
    ----------
    symbol: YF ticker of the product for which the order was performed
    '''  
    if type(symbol)==str:
        return Action.objects.get(symbol=symbol)
    else:
        return symbol #action in this case

class Currency(models.Model):
    '''
    Currency in which the stock is traded
    '''
    name=models.CharField(max_length=100, blank=False)
    symbol=models.CharField(max_length=100, blank=False,default="A")
    
    class Meta:
        ordering = ["name"]
        
    def __str__(self):
        return self.name
    
class Fees(models.Model):
    '''
    Fees for the trades
    
    Attributes
   	----------
    name: name used to describe this fee
    fixed: fixed fee to pay at each trade
    percent: percent fee to pay at each trade
    '''
    name=models.CharField(max_length=100, blank=False, default="fee")
    fixed=models.FloatField()
    percent=models.FloatField()
    
    def __str__(self):
        return self.name  

class Strategy(models.Model):
    '''
    Strategy to be used for product to perform the orders
    
    Attributes
   	----------
    name: name of this strategy
    class: name of the Class in strat.py or presel.py used to determine when to perform orders using this strategy
    perform_order: boolean that determines if automatic orders in IB should be performed. If False, only manual trade is possible
    priority: figure to rank the strategies by priority. Lower figure has higher priority
    target_order_size: which order size in the base currency should be performed. For instance 1000, with base currency EUR, will perform
                  order of 1000 euros
    minimum_order_size: if the target_order_size cannot be reached (not enough money), what is minimum size of the trade which should
                        lead to a trade execution
    maximum_money_engaged: maximum total money that can be engaged in this strategy / stock exchange. To avoid having all the money invested in one strategy.
    sl_threshold: stop loss threshold for orders performed with this strategy
    daily_sl_threshold: daily stop loss threshold for orders performed with this strategy
    option_share_per: percentage of the order that should be performed with options instead of stocks
    option_min_days_distance: minimum time in day between now and option expiration
    option_max_strike_distance_per: maximum difference between present stock price and option strike price
    '''
    name=models.CharField(max_length=100, blank=False)
    class_name=models.CharField(max_length=100, blank=False, null=True)
    perform_order=models.BooleanField(blank=False,default=False)
    priority=models.IntegerField(null=False, blank=False, default=1000)
    target_order_size=models.FloatField(blank=True,null=True)
    minimum_order_size=models.FloatField(blank=True,null=True)
    maximum_money_engaged=models.FloatField(blank=True,null=True)
    sl_threshold=models.FloatField(blank=True,null=True) #as price
    daily_sl_threshold=models.FloatField(blank=True,null=True) #as pu
    option_share_per=models.FloatField(blank=True,null=True, default=0)
    option_min_days_distance=models.IntegerField(null=False, blank=False, default=30)
    option_max_strike_distance_per=models.FloatField(blank=True,null=True, default=10)
    
    class Meta:
        ordering = ["name"]
        
    def __str__(self):
        return self.name
    
class StockEx(models.Model):
    '''
    Stock exchange
    
    Attributes
   	----------
    name: name of this stock exchange
    fees: fees associated with this stock exchange
    ib_ticker: ticker in IB
    opening_time: opening time of this stock exchange in the timezone defined afterwards
    closing_time: closing time of this stock exchange in the timezone defined afterwards
    timezone: timezone of this stock exchange
    perform_order: boolean that determines if automatic orders in IB should be performed. If False, only manual trade is possible
    ib_auth: do you have enough permission in IB to perform trades in this stock exchange?
    strategies_in_use: select the strategies you want to use for this stock exchange, before closing. 
                       Overriden by those at sector level if presel_at_sector_level is true!
    strategies_in_use_intraday: select the strategies you want to use for this stock exchange, during the day
                                Overriden by those at sector level if presel_at_sector_level is true!
    presel_at_sector_level: if true, the strategy will be performed at sector level. Is true only for NYSE, as there are too many stocks
                            in the S&P 500. You may want to use the same strategy on 5 bundles of 100 stocks instead of 1 strategy for 
                            500 stocks.
    main_index: select the index related to this stock exchange  
    calc_report: should the report be calculated, useful to deactivate report about ETF stock exchanges
    '''
    name=models.CharField(max_length=100, blank=False)
    fees=models.ForeignKey('Fees',on_delete=models.CASCADE)
    ib_ticker=models.CharField(max_length=15, blank=True,default="AAA")
    opening_time=models.TimeField(default=datetime.time(9, 00))
    closing_time=models.TimeField(default=datetime.time(17, 00))
    timezone=models.CharField(max_length=60,choices=all_tz, blank=False,default='Europe/Paris')
    perform_order=models.BooleanField(blank=False,default=False)
    ib_auth=models.BooleanField(blank=False,default=False)
    strategies_in_use=models.ManyToManyField(Strategy,blank=True, related_name='strategies_in_use')   # Presel strategies in use, normal/sl/tsl depends on the selected candidates
    strategies_in_use_intraday=models.ManyToManyField(Strategy,blank=True, related_name='strategies_in_use_intraday')  
    presel_at_sector_level=models.BooleanField(blank=False,default=False)
    main_index=models.ForeignKey('Action',on_delete=models.CASCADE,blank=True,null=True,default=None)
    calc_report=models.BooleanField(blank=False,default=True)
    
    class Meta:
        ordering = ["name"]
    
    def __str__(self):
        return self.name 

class Order(models.Model):
    '''
    Order/trade
    
    Attributes
   	----------
    action: product associated that was traded
    strategy: strategy that lead to this order
    active: is this order still open?
    short: is it an order with short direction?
    entering_date: date when this order was opened
    exiting_date: date when this order was closed
    entering_price: price of this product at order opening
    exiting_price: price of this product at order closing
    sl_threshold: stop loss threshold 
    daily_sl_threshold: daily stop loss threshold
    profit: absolute profit realized with this order
    profit_percent: relative profit realized with this order
    quantity: quantity of the product involved in the order    
    '''
    action=models.ForeignKey('Action',on_delete=models.CASCADE)
    strategy=models.ForeignKey('Strategy',on_delete=models.CASCADE,blank=True, null=True)
    active=models.BooleanField(blank=False,default=True)
    short=models.BooleanField(blank=False,default=False)
    entering_date=models.DateTimeField(null=False, blank=False, auto_now_add=True)#default=timezone.now())
    exiting_date=models.DateTimeField(null=True, blank=True)
    entering_price=models.FloatField(blank=True,null=True)
    exiting_price=models.FloatField(blank=True,null=True)
    sl_threshold=models.FloatField(blank=True,null=True) #as price
    daily_sl_threshold=models.FloatField(blank=True,null=True) #as pu
    profit=models.FloatField(blank=True,null=True)
    profit_percent=models.FloatField(blank=True,null=True)
    quantity=models.FloatField(blank=True,null=True)
    
    def __str__(self):
        return self.action.name + " "+ str(self.entering_date)

def pf_retrieve_all(
        opening: bool=False,
        s_ex: StockEx=None,
        it_is_index:bool=False,
        only_in_ib:bool=False
        )-> list:
    """
    Retrieve all stocks owned in long or short direction from the action status
    
    Arguments
   	----------
    opening: test at stock exchange opening (need to compare with the day before then)
    s_ex: stock exchange from which the stocks need to be returned
    it_is_indexes: dict containing if the symbol is an index or not
    only_in_ib: filter only actions in ib
    """
    c0=~Q(stockstatus__quantity=0)
    if it_is_index:
        cat=ActionCategory.objects.get(short="IND")
        c2=Q(category=cat)
    else:
        c2=~Q(pk__in=[]) #True
        
    if only_in_ib:
        c3=Q(stockstatus__order_in_ib=True)
    else:
        c3=~Q(pk__in=[]) #True
    
    if opening and s_ex is not None:
        c1 = Q(stock_ex=s_ex)
        actions=Action.objects.filter(c0&c1&c2&c3)
    else:
        actions=Action.objects.filter(c0&c2&c3) #filter(c1)

    return list(set(actions)) #unique

def pf_retrieve_all_symbols(
        opening: str=None
        )-> list:
    """
    Retrieve all stocks symbols owned in long or short direction from the action status
    
    Arguments
    ----------
    opening: test at stock exchange opening (need to compare with the day before then)
    """
    p=pf_retrieve_all(opening=opening)
    return [action.symbol for action in p]
  
def get_pf(
        strategy: str,
        exchange:str,
        short:bool,
        ):
    '''
    To get a list of the stocks presently using a strategy for an exchange
    
    Arguments
    ----------
    strategy: name of the strategy
    exchange: name of the stock exchange
    short: if the products are presently in a short direction
    '''
    try:
        stockEx1=StockEx.objects.get(name=exchange)
        c1=Q(stock_ex=stockEx1)
        st1=Strategy.objects.get(name=strategy)
        c2=Q(stockstatus__strategy=st1)
        
        if short:
            c0=Q(stockstatus__quantity__lt=0)
        else:
            c0=Q(stockstatus__quantity__gt=0)

        actions=Action.objects.filter(c0&c1&c2)
        return [action.symbol for action in actions] 

    except Exception as e:
        import sys
        _, e_, exc_tb = sys.exc_info()
        print(e)
        print("line " + str(exc_tb.tb_lineno))  
        logger.error(strategy)
        logger.error(e, stack_info=True, exc_info=True)

class ActionCategory(models.Model):
    '''
    To distinguish between ETF, actions, indexes...
    
    Attributes
   	----------
    short: short key, to identify this category clearly
    name: name of this category
    '''
    short=models.CharField(max_length=15, blank=False, default="AAA", primary_key=True)
    name=models.CharField(max_length=100, blank=False)
        
    def __str__(self):
        return self.name 

class ActionSector(models.Model):
    '''
    GICS sectors    
    
    Attributes
   	----------
    name: name of this sector
    strategies_in_use: select the strategies you want to use for this stock exchange, before closing. 
    strategies_in_use_intraday: select the strategies you want to use for this stock exchange, during the day
    '''
    name=models.CharField(max_length=100, blank=False)
    strategies_in_use=models.ManyToManyField(Strategy,blank=True,related_name="as_strategies_in_use")  
    strategies_in_use_intraday=models.ManyToManyField(Strategy,blank=True,related_name="as_strategies_in_use_intraday") 
    
    class Meta:
        ordering = ["name"]
        
    def __str__(self):
        return self.name     

class Candidates(models.Model):
    '''
    For strategy using two time frame, in the slow one (10 days) candidates are defined
    And on daily basis the other strategy decides which of the candidate is really bought or sold
    
    Attributes
   	----------
    actions: list of the products considered as candidate
    strategy: strategy associated with this list of candidates
    stock_ex: stock exchange where the candidates are listed (there can be only one)
    '''
    actions=models.ManyToManyField(Action,blank=True)    
    strategy=models.ForeignKey('Strategy',on_delete=models.CASCADE,blank=True,null=True)
    stock_ex=models.ForeignKey('StockEx',on_delete=models.CASCADE,blank=True,null=True)
    
    def reset(self):
        for a in self.actions.all():
            self.actions.remove(a)
            self.save()
    
    def append(self,symbol): #so we can name as for list
        a=symbol_to_action(symbol)
        self.actions.add(a)
        self.save()
        
    def retrieve(self):
        return [action.symbol for action in self.actions.all()]
    
    def __str__(self):
        return self.strategy.name + "_" + self.stock_ex.name

def get_candidates(strategy:str, exchange:str):
    '''
    Return the Candidates object corresponding to a strategy and a stock exchange
    
    Attributes
   	----------
    strategy: strategy name
    exchange: stock exchange name
    '''
    res, _ = Candidates.objects.get_or_create(
        stock_ex=StockEx.objects.get(name=exchange),
        strategy=Strategy.objects.get(name=strategy),
        )
    return res
 
class Excluded(models.Model):
    '''
    List of actions provisory excluded for a strategy as it risks to perform bad
    
    Attributes
   	----------
    name: name of this list. Normally same as the strategy, but there is a list "all" defined
    actions: list of the products excluded
    strategy: strategy for which those products are excluded
    ''' 
    name=models.CharField(max_length=100, blank=False)
    actions=models.ManyToManyField(Action,blank=True)   
    strategy=models.ForeignKey('Strategy',on_delete=models.CASCADE,blank=True,null=True)
    
    def reset(self):
        for a in self.actions.all():
            self.actions.remove(a)
            self.save()
    
    def append(self,symbol):
        a=symbol_to_action(symbol)
        self.actions.add(a)
        self.save()
        
    def remove(self,symbol):
        try:
            a=symbol_to_action(symbol)
            self.actions.remove(a)
            self.save()
        except Exception as e:
            logger.error(e + " symbol: "+symbol, stack_info=True, exc_info=True)    
            pass
        
    def retrieve(self):
        return [action.symbol for action in self.actions.all()]
    
    def __str__(self):
        return self.name 

class StratCandidates(models.Model):
    '''
    Define a list of actions and indexes that can be traded using the defined strategy
    
    Attributes
   	----------
    actions: list of the products that can be traded
    strategy: associated strategy
    '''
    actions=models.ManyToManyField(Action,blank=True)    
    strategy=models.ForeignKey('Strategy',on_delete=models.CASCADE,blank=True,null=True)
    
    def retrieve(self):
        return [action.symbol for action in self.actions.all()]
    
    def __str__(self):
        return self.strategy.name   
    
class Job(models.Model):
    '''
    Job, typically actualization job
    
    Attributes
   	----------
    strategy: associated strategy
    stock_ex: associated stock exchange 
    last_execution: date when the job was last executed
    frequency_days: how often must the job be executed? In days
    period_year: how far in the past should the script download prices.
    '''
    strategy=models.ForeignKey('Strategy',on_delete=models.CASCADE,blank=True,null=True)
    stock_ex=models.ForeignKey('StockEx',on_delete=models.CASCADE,blank=True,null=True)
    
    last_execution=models.DateTimeField(null=False, blank=False, auto_now_add=True)
    frequency_days=models.IntegerField(null=False, blank=False, default=14)
    period_year=models.IntegerField(null=False, blank=False, default=1)
    
    def __str__(self):
        return self.strategy.name + "_" + self.stock_ex.name