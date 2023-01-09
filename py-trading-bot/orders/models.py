from django.db import models
from django.db.models import Q

import sys
from trading_bot.settings import ( USE_IB_FOR_DATA, IB_STOCKEX_NO_PERMISSION, IB_STOCK_NO_PERMISSION)
import datetime
#from orders.ib import 


### Check if IB can be used
def check_ib_permission(symbols):
    IBok=True
    for symbol in symbols:
        if symbol in IB_STOCK_NO_PERMISSION:
            print("symbol " + symbol + " has no permission for IB")
            IBok=False
            break
        
        a=Action.objects.get(symbol=symbol)        
        if a.stock_ex.ib_ticker in IB_STOCKEX_NO_PERMISSION:
            print("stock ex " + a.stock_ex.ib_ticker + " has no permission for IB")
            IBok=False
            break
    return IBok

def check_exchange_ib_permission(exchange):
    s_ex=StockEx.objects.get(name=exchange)
    if s_ex.ib_ticker in IB_STOCKEX_NO_PERMISSION:
        return False
    else:
        return True   
    
### Get lists of actions for the reporting
def get_exchange_actions(exchange,**kwargs):
    cat=ActionCategory.objects.get(short="ACT")
    stockEx=StockEx.objects.get(name=exchange)
    
    c1 = Q(category=cat)
    c2 = Q(stock_ex=stockEx)
    c3 = Q(delisted=False)
    
    if exchange=="NYSE" and kwargs.get("sector"):
        action_sector=ActionSector.objects.get(name=kwargs.get("sector"))
        c4 = Q(sector=action_sector)
        actions=Action.objects.filter(c1 & c2 & c3 & c4)
    else:
        actions=Action.objects.filter(c1 & c2 & c3)
        
    use_IB=False
    if USE_IB_FOR_DATA:
        use_IB=check_ib_permission([a.symbol for a in actions])
   
    return use_IB, actions


### Conversion between input from YF and IB
def period_YF_to_ib(period): #see also split_freq_str in vbt
    #transform "10 d" in "10 D"
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

def interval_YF_to_ib(interval):
    #Time period of one bar. Must be one of: ‘1 secs’, ‘5 secs’, ‘10 secs’ 15 secs’, ‘30 secs’, ‘1 min’, ‘2 mins’, ‘3 mins’, ‘5 mins’, ‘10 mins’, ‘15 mins’, ‘20 mins’, ‘30 mins’, ‘1 hour’, ‘2 hours’, ‘3 hours’, ‘4 hours’, ‘8 hours’, ‘1 day’, ‘1 week’, ‘1 month’.
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

### Data retrieval ###

def exchange_to_index_symbol(exchange):
    exchange_to_symbol_dic={
        "SBF":["CAC40","^FCHI"],
        "MONEP":["CAC40","^FCHI"],
        "IBIS":["DAX","^GDAXI"],
        "NASDAQ":["COMP","^IXIC"], #COMP
        "NYSE":["SPX","^DJI"],    #should be INDU actually, but no permission
        "default":["COMP","^IXIC"],
        }    
    
    if exchange in exchange_to_symbol_dic:
        return exchange_to_symbol_dic[exchange]
    else:
        return exchange_to_symbol_dic["default"]


    
def action_to_etf(action,short):
    if action.category==ActionCategory.objects.get(short="IND"):
        if short:
            action=action.etf_short
        else:
            action=action.etf_long
    return action

class Currency(models.Model):
    name=models.CharField(max_length=100, blank=False)
    symbol=models.CharField(max_length=100, blank=False,default="A")
    
    def __str__(self):
        return self.name
    
class Fees(models.Model):
    name=models.CharField(max_length=100, blank=False, default="fee")
    fixed=models.DecimalField(max_digits=100, decimal_places=5)
    percent=models.DecimalField(max_digits=100, decimal_places=5)
    
    def __str__(self):
        return self.name  
    
class StockEx(models.Model):
    name=models.CharField(max_length=100, blank=False)
    fees=models.ForeignKey('Fees',on_delete=models.CASCADE)
    ib_ticker=models.CharField(max_length=15, blank=True,default="AAA")
    opening_time=models.TimeField(default=datetime.time(9, 00))
    closing_time=models.TimeField(default=datetime.time(17, 00))
    
    def __str__(self):
        return self.name    

class Strategy(models.Model):
    name=models.CharField(max_length=100, blank=False)
    
    def __str__(self):
        return self.name  

### Index is like action, but it had to be separated, as an index cannot be bought directly
class Action(models.Model):
    symbol=models.CharField(max_length=15, blank=False, primary_key=True)
    ib_ticker_explicit=models.CharField(max_length=15, blank=True,default="AAA") #for index especially
    name=models.CharField(max_length=100, blank=False)
    stock_ex=models.ForeignKey('StockEx',on_delete=models.CASCADE)
    currency=models.ForeignKey('Currency',on_delete=models.CASCADE)
    category=models.ForeignKey('ActionCategory',on_delete=models.CASCADE,blank=True)
    sector=models.ForeignKey('ActionSector',on_delete=models.CASCADE,blank=True,default=0)
    #strategy=models.ForeignKey('Strategy',on_delete=models.CASCADE,blank=True,default=0)
    delisted=models.BooleanField(blank=False,default=False)
    etf_long=models.ForeignKey('self',on_delete=models.CASCADE,related_name='etf_long2',blank=True,null=True)
    etf_short=models.ForeignKey('self',on_delete=models.CASCADE,related_name='etf_short2',blank=True,null=True)
    
    #introduction_date=models.DateTimeField(null=True, blank=True, auto_now_add=True)
    
    class Meta:
        ordering = ["name"]
        
    def ib_ticker(self):
        if self.ib_ticker_explicit!="AAA" and self.ib_ticker_explicit is not None:
            return self.ib_ticker_explicit
        else:
            t=self.symbol.split(".")
            return t[0]      
        
    def __str__(self):
        return self.name

class Order(models.Model):
    action=models.ForeignKey('Action',on_delete=models.CASCADE)
    pf=models.ForeignKey('PF',on_delete=models.SET_NULL,blank=True,null=True)
    active=models.BooleanField(blank=False,default=True)
    entering_date=models.DateTimeField(null=False, blank=False, auto_now_add=True)#default=timezone.now())
    exiting_date=models.DateTimeField(null=True, blank=True)
    entering_price=models.DecimalField(max_digits=100, decimal_places=5,blank=True,null=True)
    exiting_price=models.DecimalField(max_digits=100, decimal_places=5,blank=True,null=True)
    sl_threshold=models.DecimalField(max_digits=100, decimal_places=5,blank=True,null=True)
    profit=models.DecimalField(max_digits=100, decimal_places=5,blank=True,null=True)
    profit_percent=models.DecimalField(max_digits=100, decimal_places=5,blank=True,null=True)
    quantity=models.DecimalField(max_digits=100, decimal_places=5,blank=True,null=True)

    def __str__(self):
        return self.action.name + " "+ str(self.entering_date)

def pf_retrieve_all(**kwargs):
    arr=[]
    
    for pf in PF.objects.filter(short=kwargs.get("short",False)):
        cat=ActionCategory.objects.get(short="ACT")
        c1 = Q(category=cat)
        if kwargs.get("opening")=="9h":
            stockEx1=StockEx.objects.filter(name="Paris")
            stockEx2=StockEx.objects.filter(name="XETRA")
            c2 = Q(stock_ex=stockEx1[0])
            c3 = Q(stock_ex=stockEx2[0])
            actions=pf.actions.filter(c1 & (c2|c3))
        elif kwargs.get("opening")=="15h":
            stockEx1=StockEx.objects.filter(name="Nasdaq")
            stockEx2=StockEx.objects.filter(name="NYSE")
            c2 = Q(stock_ex=stockEx1[0])
            c3 = Q(stock_ex=stockEx2[0])
            actions=pf.actions.filter(c1 & (c2|c3))
        else:
            actions=pf.actions.filter(c1)
        
        for action in actions:
            if not action in arr:
                arr.append(action)
    return arr

### Portfolio for a given strategy (used as name presently)
class PF(models.Model):
    # can be replaced with ib.positions() or ib.portfolio()
    name=models.CharField(max_length=100, blank=False)
    actions=models.ManyToManyField(Action,blank=True)
    sector=models.ForeignKey('ActionSector',on_delete=models.CASCADE,blank=True,default=0)
    short=models.BooleanField(blank=False,default=False)
    strategy=models.ForeignKey('Strategy',on_delete=models.CASCADE,blank=True)
    stock_ex=models.ForeignKey('StockEx',on_delete=models.CASCADE,blank=True,default=0)
    
    def __str__(self):
        return self.name
    
    def retrieve(self):
        arr=[]
        for action in self.actions.all():
            arr.append(action.symbol)
        return arr

    def remove(self,symbol):
        a = Action.objects.get(symbol=symbol)
        
        try:
            self.actions.remove(a)
            self.save()
        except Exception as msg:
            print("exception in remove_symbol")
            print(symbol)
            print(msg)
            _, e_, exc_tb = sys.exc_info()
            print("line " + str(exc_tb.tb_lineno))
            pass

    def append(self,symbol):
        try:
            a = Action.objects.get(symbol=symbol)
            self.actions.add(a)
            self.save()
        except Exception as msg:
            print("exception in " + __name__)
            print(msg)
            print("symbol: "+ symbol)
            _, e_, exc_tb = sys.exc_info()
            print("line " + str(exc_tb.tb_lineno))
            pass    

def get_sub(strategy, exchange,short,**kwargs):
    sector="undefined"
    name=strategy + "_" + exchange
    if short:
        name+="_short"
        
    if exchange=="NYSE":
        if kwargs.get("sector"):
            sector=kwargs.get("sector") 
            
    return name, sector

def get_pf(strategy, exchange,short,**kwargs):
    try:
        name, sector=get_sub(strategy, exchange,short,**kwargs)
        res, _ = PF.objects.get_or_create(
                stock_ex=StockEx.objects.get(name=exchange),
                strategy=Strategy.objects.get(name=strategy),
                short=short,
                sector=ActionSector.objects.get(name=sector),
                name=name)

        return res
    except Exception as msg:
        print(msg)

### To distinguish between ETF, actions, indexes...
class ActionCategory(models.Model):
    short=models.CharField(max_length=15, blank=False, default="AAA", primary_key=True)
    name=models.CharField(max_length=100, blank=False)

    def __str__(self):
        return self.name 

###GICS sectors    
class ActionSector(models.Model):
    name=models.CharField(max_length=100, blank=False)

    def __str__(self):
        return self.name     
    
###To define the capital assigned to one strategy.
###Not used presently  
class Capital(models.Model):
    #self.ib.accountSummary()
    capital=models.DecimalField(max_digits=100, decimal_places=5,blank=True,null=True)
    name=models.CharField(max_length=100, blank=False,default="")
    strategy=models.ForeignKey('Strategy',on_delete=models.CASCADE,blank=True)
    stock_ex=models.ForeignKey('StockEx',on_delete=models.CASCADE,blank=True,default=2)
    
    def __str__(self):
        return self.name 

def get_capital(strategy, exchange,short,**kwargs):
    name, sector=get_sub(strategy, exchange,short,**kwargs)
    res, _= Capital.objects.get_or_create(
        stock_ex=StockEx.objects.get(name=exchange),
        strategy=Strategy.objects.get(name=strategy),
        short=short,    
        sector=ActionSector.objects.get(name=sector),
        name=name)
    return res

###To define the number of orders assigned to one strategy
###1 means that only one action can be owned at a time using this strategy

class OrderCapital(models.Model):
    capital=models.DecimalField(max_digits=100, decimal_places=5,blank=True,null=True)
    name=models.CharField(max_length=100, blank=False,default="")
    strategy=models.ForeignKey('Strategy',on_delete=models.CASCADE,blank=True)
    stock_ex=models.ForeignKey('StockEx',on_delete=models.CASCADE,blank=True,default=2)
    sector=models.ForeignKey('ActionSector',on_delete=models.CASCADE,blank=True,default=0)
    
    def __str__(self):
        return self.name 

def get_order_capital(strategy, exchange,**kwargs):
    try:
        name, sector=get_sub(strategy, exchange,False,**kwargs)
        res, created = OrderCapital.objects.get_or_create(
            stock_ex=StockEx.objects.get(name=exchange),
            strategy=Strategy.objects.get(name=strategy),
            sector=ActionSector.objects.get(name=sector),
            name=name
            )
        if created:
            res.capital=0
        
        return res
    except Exception as msg:
        print(msg)        

###For strategy using two time frame, in the slow one (10 days) candidates are defined
###And on daily basis the other strategy decides which of the candidate is really bought or sold

class Candidates(models.Model):
    name=models.CharField(max_length=100, blank=False)
    actions=models.ManyToManyField(Action,blank=True)    
    strategy=models.ForeignKey('Strategy',on_delete=models.CASCADE,blank=True,default=1)
    stock_ex=models.ForeignKey('StockEx',on_delete=models.CASCADE,blank=True,default=2)
    
    def reset(self):
        for a in self.actions.all():
            self.actions.remove(a)
            self.save()
    
    def append(self,symbol): #so we can name as for list
        a = Action.objects.get(symbol=symbol)
        self.actions.add(a)
        self.save()
        
    def retrieve(self):
        arr=[]
        for action in self.actions.all():
            arr.append(action.symbol)
        return arr
    
    def __str__(self):
        return self.name     

def get_candidates(strategy, exchange):
    res, _ = Candidates.objects.get_or_create(
        stock_ex=StockEx.objects.get(name=exchange),
        strategy=Strategy.objects.get(name=strategy),
        name=strategy + "_" + exchange
        )
    return res
    
### List of actions provisory excluded for a strategy as it risks to perform bad
    
class Excluded(models.Model):
    name=models.CharField(max_length=100, blank=False)
    actions=models.ManyToManyField(Action,blank=True)   
    strategy=models.ForeignKey('Strategy',on_delete=models.CASCADE,blank=True)
    
    def reset(self):
        for a in self.actions.all():
            self.actions.remove(a)
            self.save()
    
    def append(self,symbol):
        a = Action.objects.get(symbol=symbol)
        self.actions.add(a)
        self.save()
        
    def remove(self,symbol):
        a = Action.objects.get(symbol=symbol)
        
        try:
            self.actions.remove(a)
            self.save()
        except Exception as msg:
            print("exception in " + __name__)
            print(symbol)
            print(msg)
            _, e_, exc_tb = sys.exc_info()
            print("line " + str(exc_tb.tb_lineno))
            pass
        
    def retrieve(self):
        arr=[]
        for action in self.actions.all():
            arr.append(action.symbol)
        return arr
    
    def __str__(self):
        return self.name 
 
### Define a list of actions and indexes that can be traded using the defined strategy
class StratCandidates(models.Model):
    name=models.CharField(max_length=100, blank=False)
    actions=models.ManyToManyField(Action,blank=True)    
    strategy=models.ForeignKey('Strategy',on_delete=models.CASCADE,blank=True,default=0)
    
    def retrieve(self):
        arr=[]
        for action in self.actions.all():
            arr.append(action.symbol)
        return arr  
    
    def __str__(self):
        return self.name     