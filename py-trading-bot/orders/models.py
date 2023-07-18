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

def check_ib_permission(symbols: list):
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
            _settings["USED_API"][k]="IB"
            for symbol in symbols:
                if symbol in _settings["IB_STOCK_NO_PERMISSION"]:
                    logger.info("symbol " + symbol + " has no permission for IB")
                    _settings["USED_API"][k]="YF"
                    break
                
                a=Action.objects.get(symbol=symbol)      
                if a.stock_ex.ib_auth==False:
                    logger.info("stock ex " + a.stock_ex.ib_ticker + " has no permission for IB")
                    _settings["USED_API"][k]="YF"
                    break
        elif v=="YF":
            _settings["USED_API"][k]=v
    
def get_exchange_actions(exchange:str,**kwargs):
    '''
    Get lists of actions for the reporting

    Arguments
    ----------
        exchange: name of the stock exchange
    '''
    cat=ActionCategory.objects.get(short="ACT")
    
    try:
        stock_ex=StockEx.objects.get(name=exchange)
    except:
        raise ValueError("Stock exchange: "+str(exchange)+" not found, create it in the admin panel")
    
    c1 = Q(category=cat)
    c2 = Q(stock_ex=stock_ex)
    c3 = Q(delisted=False) #to be removed
    
    if stock_ex.presel_at_sector_level and kwargs.get("sec"):
        action_sector, _=ActionSector.objects.get_or_create(name=kwargs.get("sec"))
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
    ''' 
    symbol=models.CharField(max_length=15, blank=False, primary_key=True)
    ib_ticker_explicit=models.CharField(max_length=15, blank=True,default="AAA") #for index especially
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
        is_new=False
        if "id" not in self.__dir__():
            is_new = True
        super().save(*args, **kwargs)  
        if is_new:
            StockStatus.objects.create(action=self)        
        
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
        limit_date=td
    else:
        limit_date=datetime.datetime(td.year-y_period,td.month,td.day,tzinfo=tz_Paris) #time zone not important here but otherwise bug

    if a.intro_date is not None: #should come from database
        if a.intro_date>limit_date :
           return False
    if a.delisting_date is not None:
        if a.delisting_date<limit_date :
           return False
    return True

class StockStatus(models.Model):
    '''
    Complement action, separated from action as Action contains the essence of the action, here it is some that the user can change
    '''
    action = models.OneToOneField(
        Action,
        on_delete=models.CASCADE,
        primary_key=True,
    )
    quantity=models.DecimalField(max_digits=100, decimal_places=5,blank=True,null=True,default=0) #no need for short as quantity can be negative
    strategy=models.ForeignKey('Strategy',on_delete=models.CASCADE,blank=True,null=True)
    order_in_ib=models.BooleanField(blank=False,default=True)

    class Meta:
        ordering = ["action__name"]
        
    def __str__(self):
        return self.action.name    
    
def action_to_short(action):
    a=Action.objects.get(action=action)
    ss = StockStatus.objects.get(action=a)
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
    '''
    name=models.CharField(max_length=100, blank=False, default="fee")
    fixed=models.DecimalField(max_digits=100, decimal_places=5)
    percent=models.DecimalField(max_digits=100, decimal_places=5)
    
    def __str__(self):
        return self.name  

class Strategy(models.Model):
    '''
    Strategy to be used for product to perform the orders
    '''
    name=models.CharField(max_length=100, blank=False)
    class_name=models.CharField(max_length=100, blank=False, null=True)
    perform_order=models.BooleanField(blank=False,default=False)
    priority=models.IntegerField(null=False, blank=False, default=1000)
    order_size=models.DecimalField(max_digits=100, decimal_places=5,blank=True,null=True)
    maximum_money_engaged=models.DecimalField(max_digits=100, decimal_places=5,blank=True,null=True)
    sl_threshold=models.DecimalField(max_digits=100, decimal_places=5,blank=True,null=True) #as price
    daily_sl_threshold=models.DecimalField(max_digits=100, decimal_places=5,blank=True,null=True) #as pu
    
    class Meta:
        ordering = ["name"]
        
    def __str__(self):
        return self.name
    
class StockEx(models.Model):
    '''
    Stock exchange
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
    
    class Meta:
        ordering = ["name"]
    
    def __str__(self):
        return self.name 

class Order(models.Model):
    action=models.ForeignKey('Action',on_delete=models.CASCADE)
    strategy=models.ForeignKey('Strategy',on_delete=models.CASCADE,blank=True, null=True)
    active=models.BooleanField(blank=False,default=True)
    short=models.BooleanField(blank=False,default=False)
    entering_date=models.DateTimeField(null=False, blank=False, auto_now_add=True)#default=timezone.now())
    exiting_date=models.DateTimeField(null=True, blank=True)
    entering_price=models.DecimalField(max_digits=100, decimal_places=5,blank=True,null=True)
    exiting_price=models.DecimalField(max_digits=100, decimal_places=5,blank=True,null=True)
    sl_threshold=models.DecimalField(max_digits=100, decimal_places=5,blank=True,null=True) #as price
    daily_sl_threshold=models.DecimalField(max_digits=100, decimal_places=5,blank=True,null=True) #as pu
    profit=models.DecimalField(max_digits=100, decimal_places=5,blank=True,null=True)
    profit_percent=models.DecimalField(max_digits=100, decimal_places=5,blank=True,null=True)
    quantity=models.DecimalField(max_digits=100, decimal_places=5,blank=True,null=True)
    
    def __str__(self):
        return self.action.name + " "+ str(self.entering_date)

def pf_retrieve_all(
        opening: str=None,
        )-> list:
    """
    Retrieve all stocks owned in long or short direction from the action status
    
    Arguments
   	----------
       opening: test at stock exchange opening (need to compare with the day before then)
    """
    c0=~Q(stockstatus__quantity=0)

    if opening=="9h":
        stockEx1=StockEx.objects.filter(name="Paris")
        stockEx2=StockEx.objects.filter(name="XETRA")
        c2 = Q(stock_ex=stockEx1[0])
        c3 = Q(stock_ex=stockEx2[0])
        actions=Action.objects.filter(c0&(c2|c3))#c1 &
    elif opening=="15h":
        stockEx1=StockEx.objects.filter(name="Nasdaq")
        stockEx2=StockEx.objects.filter(name="NYSE")
        c2 = Q(stock_ex=stockEx1[0])
        c3 = Q(stock_ex=stockEx2[0])
        actions=Action.objects.filter(c0&(c2|c3)) #c1 &
    else:
        actions=Action.objects.filter(c0) #filter(c1)

    return list(set(actions)) #unique

def pf_retrieve_all_symbols(opening: str=None,
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
    '''
    short=models.CharField(max_length=15, blank=False, default="AAA", primary_key=True)
    name=models.CharField(max_length=100, blank=False)
        
    def __str__(self):
        return self.name 

class ActionSector(models.Model):
    '''
    GICS sectors    
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

def get_candidates(strategy, exchange):
    res, _ = Candidates.objects.get_or_create(
        stock_ex=StockEx.objects.get(name=exchange),
        strategy=Strategy.objects.get(name=strategy),
        )
    return res
 
class Excluded(models.Model):
    '''
    List of actions provisory excluded for a strategy as it risks to perform bad
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
    '''
    actions=models.ManyToManyField(Action,blank=True)    
    strategy=models.ForeignKey('Strategy',on_delete=models.CASCADE,blank=True,null=True)
    
    def retrieve(self):
        return [action.symbol for action in self.actions.all()]
    
    def __str__(self):
        return self.strategy.name   
    
class Job(models.Model):
    strategy=models.ForeignKey('Strategy',on_delete=models.CASCADE,blank=True,null=True)
    stock_ex=models.ForeignKey('StockEx',on_delete=models.CASCADE,blank=True,null=True)
    
    last_execution=models.DateTimeField(null=False, blank=False, auto_now_add=True)
    frequency_days=models.IntegerField(null=False, blank=False, default=14)
    period_year=models.IntegerField(null=False, blank=False, default=1)
    
    def __str__(self):
        return self.strategy.name + "_" + self.stock_ex.name