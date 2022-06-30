from django.db import models
from django.utils import timezone
from django.db.models import Q

import asyncio
from ib_insync import IB, Stock, MarketOrder, util
from core.common import  empty_append
from core.indicators import rel_dif

import vectorbtpro as vbt
import sys
import math

import pandas as pd
import numpy as np

from trading_bot.settings import (PERFORM_ORDER, USE_IB_FOR_DATA,DIC_PERFORM_ORDER,
                                  IB_LOCALHOST, IB_PORT)

### Interactive brockers and data retrieval ###
'''
Contains:
- Communication with Interactive brokers
- Retrieval of live data (Interactive brokers or YFinance)
- Performing order
- Models for financial products, stock exchanges...

Note: for some reasons, it does not work if myIB class is not in models
'''

## All symbols must be from same stock exchange
def retrieve_data(symbols,period,**kwargs):
    try:
        IBok=True
        for symbol in symbols:
            if kwargs.get("index",False):
                action=Index.objects.get(symbol=symbol)
            else:
                action=Action.objects.get(symbol=symbol)
            
            if action.stock_ex.ib_ticker in ["BVME.ETF"]:
                IBok=False
                break
        
        index_symbol=exchange_to_symbol(action)
        
        if (USE_IB_FOR_DATA and IBok) or kwargs.get("useIB",False):         
            fig= ''.join(x for x in period if x.isdigit())
            if period.find("d")!=-1:
                period_ib=fig +" D"
            elif period.find("mo")!=-1:
                period_ib=fig +" M"
            elif period.find("y")!=-1:
                period_ib=fig +" Y"  
            
            #Time period of one bar. Must be one of: ‘1 secs’, ‘5 secs’, ‘10 secs’ 15 secs’, ‘30 secs’, ‘1 min’, ‘2 mins’, ‘3 mins’, ‘5 mins’, ‘10 mins’, ‘15 mins’, ‘20 mins’, ‘30 mins’, ‘1 hour’, ‘2 hours’, ‘3 hours’, ‘4 hours’, ‘8 hours’, ‘1 day’, ‘1 week’, ‘1 month’.
            if kwargs.get("interval",False):
                fig= ''.join(x for x in  kwargs.get("interval") if x.isdigit())
                if period.find("m")!=-1:
                    interval=fig +" mins"
                elif period.find("h")!=-1:
                    interval=fig +" hours"
                elif period.find("d")!=-1:
                    interval=fig +" day"
            else:
                interval='1 day'
            
            open_=[]
            close=[]
            low=[]
            high=[]
                    
            myIB=MyIB()
            for symbol in symbols:
                action=Action.objects.get(symbol=symbol)
                contract = Stock(action.ib_ticker(),action.stock_ex.ib_ticker, action.currency.symbol)
                bars = myIB.ib.reqHistoricalData(
                        contract,
                        endDateTime='',
                        durationStr=period_ib, #"10 D","1 M"
                        barSizeSetting=interval, #"1 day", "1 min"
                        whatToShow='TRADES',
                        useRTH=True,
                        formatDate=1)
        
                df=util.df(bars)
                open_=empty_append(open_,df["open"].values,axis=1)
                close=empty_append(close,df["close"].values,axis=1)
                high=empty_append(high,df["high"].values,axis=1)
                low=empty_append(low,df["low"].values,axis=1)
                volume=empty_append(low,df["volume"].values,axis=1)
            
            cours_open=pd.DataFrame(data=open_,index=df["date"],columns=symbols)
            cours_close=pd.DataFrame(data=close,index=df["date"],columns=symbols)
            cours_low=pd.DataFrame(data=low,index=df["date"],columns=symbols)
            cours_high=pd.DataFrame(data=high,index=df["date"],columns=symbols)
            cours_volume=pd.DataFrame(data=volume,index=df["date"],columns=symbols)
    
            action=Action.objects.get(symbol=index_symbol)
            contract = Stock(action.ib_ticker(),action.stock_ex.ib_ticker, action.currency.symbol)
            bars = myIB.ib.reqHistoricalData(
                    contract,
                    endDateTime='',
                    durationStr=period_ib, #"10 D","1 M"
                    barSizeSetting=interval, #"1 day", "1 min"
                    whatToShow='TRADES',
                    useRTH=True,
                    formatDate=1)
            
            df=util.df(bars)
            cours_open_ind=df["open"]
            cours_close_ind=df["close"]
            cours_high_ind=df["high"]
            cours_low_ind=df["low"]
            cours_volume_ind=df["volume"]
            #Volume
            
            if len(cours_close_ind)!=len(cours_close):
                print("cours index is different from cours length")
            
            myIB.disconnect()
        else:
            all_symbols=symbols+[index_symbol]
            cours=vbt.YFData.fetch(all_symbols, period=period,missing_index='drop',**kwargs)
            cours_action=cours.select(symbols)
            cours_open =cours_action.get('Open')
            cours_high=cours_action.get('High')
            cours_low=cours_action.get('Low')
            cours_close=cours_action.get('Close')
            cours_volume=cours_action.get('Volume')
            print("number of days retrieved: " + str(np.shape(cours_close)[0]))
            
            cours_index=cours.select(index_symbol)
            cours_open_ind =cours_index.get('Open')
            cours_high_ind=cours_index.get('High')
            cours_low_ind=cours_index.get('Low')
            cours_close_ind=cours_index.get('Close')
            cours_volume_ind=cours_index.get('Volume')

            debug=False
            if debug:
                for symbol in all_symbols:
                    data=vbt.YFData.fetch(symbol, period=period,**kwargs)
                
                    #knowing what we drop
                    close_debug=data.get("Close")
                    for ii in range(len(close_debug)):
                        if math.isnan(close_debug.values[ii]):
                            print(symbol)
                            print("dropping at least " + str(close_debug.index[ii]))
          
        return cours_high, cours_low, cours_close, cours_open, cours_volume,  \
               cours_high_ind, cours_low_ind,  cours_close_ind, cours_open_ind,\
               cours_volume_ind
                   
    except Exception as msg:
        print(msg)
        print("exception in " + __name__)
        _, e_, exc_tb = sys.exc_info()
        print("line " + str(exc_tb.tb_lineno))
        print(msg)         

def exchange_to_symbol(action):
    if action.stock_ex.ib_ticker=="SBF":
        return "^FCHI"
    elif action.stock_ex.ib_ticker=="IBIS":
        return "^GDAXI"
    elif action.stock_ex.ib_ticker=="NASDAQ":
        return "^IXIC"
    elif action.stock_ex.ib_ticker=="BVME.ETF":
        return "^IXIC" #it is only ETF anyhow

def get_exchange_actions(exchange):
    cat=ActionCategory.objects.get(short="ACT")
    stockEx=StockEx.objects.get(name=exchange)
    
    c1 = Q(category=cat)
    c2 = Q(stock_ex=stockEx)
    
    actions=Action.objects.filter(c1 & c2)
    return [ob.symbol for ob in actions]
        
def retrieve_ib_pf():
    myIB=MyIB()
    pf=[]
    pf_short=[]
    
    for pos in myIB.ib.positions():
        contract=pos.contract
        action=Action.objects.get(ib_ticker=contract.localSymbol)
        
        if pos.position>0:
            pf.append(action.symbol)
        else:
            pf_short.append(action.symbol)

    myIB.disconnect()
    return pf, pf_short

#for SL check
def get_last_price(symbol,**kwargs):
    try:
        if kwargs.get("index",False):
            action=Index.objects.get(symbol=symbol)
        else:
            action=Action.objects.get(symbol=symbol)   

        if USE_IB_FOR_DATA and action.stock_ex.ib_ticker not in ["BVME.ETF"]:
            myIB=MyIB()
            contract = Stock(action.ib_ticker(),action.stock_ex.ib_ticker, action.currency.symbol)
            cours_pres=myIB.get_last_price(contract)
            myIB.disconnect()
        else: #YF
            cours=vbt.YFData.fetch([symbol], period="2d")
            cours_close=cours.get("Close")
            cours_pres=cours_close[symbol].iloc[-1]
    
        return cours_pres
    except Exception as msg:
        print(symbol)
        print("exception in " + __name__)
        print(msg)

def get_ratio(symbol,**kwargs):
    try:
        if kwargs.get("index",False):
            action=Index.objects.get(symbol=symbol)
        else:
            action=Action.objects.get(symbol=symbol)
        
        if USE_IB_FOR_DATA and action.stock_ex.ib_ticker not in ["BVME.ETF"]:
            myIB=MyIB()
            contract = Stock(action.ib_ticker(),action.stock_ex.ib_ticker, action.currency.symbol)
            cours_pres=myIB.get_last_price(contract)
            cours_ref, cours_open=myIB.get_past_closing_price(contract)
            
            if kwargs.get("opening",False):
                cours_pres=cours_open
            
            myIB.disconnect()
        else: #YF
            cours=vbt.YFData.fetch([symbol], period="2d")
            cours_close=cours.get("Close")

            cours_ref=cours_close[symbol].iloc[0]
                    
            if kwargs.get("opening",False):
                cours_open=cours.get("Open")
                cours_pres=cours_open[symbol].iloc[-1]
            else:
                cours_pres=cours_close[symbol].iloc[-1]

        return rel_dif(cours_pres,
                           cours_ref
                           )*100
    except Exception as msg:
        print(symbol)
        print("exception in " + __name__)
        print(msg)

class MyIB():
    def __init__(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        self.ib = IB()
        self.ib.connect(host=IB_LOCALHOST, port=IB_PORT, clientId=1)
    
    def cash_balance(self):
        try:
            for v in self.ib.accountSummary():
                if v.tag == 'CashBalance':
                    return float(v.value)
        except:
            return 0
        
    def test(self,symbol):
        action=Action.objects.get(symbol=symbol)
        contract = Stock(action.ib_ticker(),action.stock_ex.ib_ticker, action.currency.symbol)
        print(self.ib.qualifyContracts(contract))  
        
    def retrieve(self,contract,period):
        
        bars = self.ib.reqHistoricalData(
                contract,
                endDateTime='',
                durationStr=period, #"10 D","1 M"
                barSizeSetting='1 hour', #"1 day", "1 min"
                whatToShow='TRADES',
                useRTH=True,
                formatDate=1)

        return util.df(bars)
    
    def get_last_price(self,contract):
        m_data = self.ib.reqMktData(contract)
        while m_data.last != m_data.last:  #Wait until data is in. 
            self.ib.sleep(0.01)
        self.ib.cancelMktData(contract)
        return m_data.last
    
    def get_past_closing_price(self,contract):
        period="2 D"
        bars = self.ib.reqHistoricalData(
                contract,
                endDateTime='',
                durationStr=period, #"10 D","1 M"
                barSizeSetting='1 day', #"1 day", "1 min"
                whatToShow='TRADES',
                useRTH=True,
                formatDate=1)
        df=util.df(bars)
        return df.iloc[0]["close"], df.iloc[-1]["open"]
    
    def place(self,buy,ticker,currency,exchange,**kwargs): #quantity in euros
        if ticker=="AAA":
            print("ticker not found")
            return "", 0
        else:
            contract = Stock(ticker, exchange, currency)
            self.ib.qualifyContracts(contract)
            
            if buy:
                order_size=kwargs.get("order_size",0)
                last_price=self.get_last_price(contract)
                quantity=math.floor(order_size/last_price)
                order = MarketOrder('BUY', quantity)
            else:
                quantity=kwargs.get("quantity",0)
                order = MarketOrder('SELL', quantity)
            trade = self.ib.placeOrder(contract, order)
            
            self.ib.sleep(1.0)
            if trade.orderStatus.status == 'Filled':
                fill = trade.fills[-1]
                txt=f'{fill.time} - {fill.execution.side} {fill.contract.symbol} {fill.execution.shares} @ {fill.execution.avgPrice}'
                price=fill.execution.avgPrice     
                return txt, price, quantity
        
    def exit_order(self,symbol,strategy, exchange,short,**kwargs):   
        #type check necessary for indexes
        try:
            pf= get_pf(strategy, exchange,short)
            ocap=get_order_capital(strategy, exchange)
            
            if kwargs.get("index",False):
                index=Index.objects.get(symbol=symbol) #actually should be more complex
                if short:
                    action=index.etf_short
                else:
                    action=index.etf_long
            else:
                action=Action.objects.get(symbol=symbol)
            
            if symbol in pf.retrieve():
                c1 = Q(action=action)
                c2 = Q(active=True)
                
                order=Order.objects.filter(c1 & c2)

                #profit
                if len(order)>0:
                    txt, order[0].exiting_price, quantity= self.place(False,
                                           action.ib_ticker(),
                                           action.currency.symbol, 
                                           action.stock_ex.ib_ticker,
                                           quantity=order[0].quantity)
                    order[0].exiting_date=timezone.now()
                    
                    if order[0].entering_price is not None: 
                        order[0].profit=order[0].exiting_price-order[0].entering_price
                        order[0].profit_percent=(order[0].exiting_price/order[0].entering_price-1)*100
                    
                    order[0].active=False
                    order[0].save()
    
                    ocap.capital+=1
                    ocap.save()
                    pf.remove(symbol)
                    pf.save()
    
                    return True
                else:
                    print("order not found " + symbol)
                    return False
            return False
        
        except Exception as msg:
            print("exception in exit")
            print(msg)
            _, e_, exc_tb = sys.exc_info()
            print("line " + str(exc_tb.tb_lineno))
            pass

    def entry_order(self,symbol,strategy, exchange,short,**kwargs): 
        try:
            #type check necessary for indexes
            pf= get_pf(strategy, exchange,short)
            order_size=5000
            ocap=get_order_capital(strategy, exchange)
            #accountSummary
            
            if kwargs.get("index",False):
                index=Index.objects.get(symbol=symbol)
                if short:
                    action=index.etf_short
                else:
                    action=index.etf_long
            else:
                action=Action.objects.get(symbol=symbol)
                
            excluded=Excluded.objects.get(name="all") #list of actions completely excluded from entries

            if (symbol not in pf.retrieve() and 
                symbol not in excluded.retrieve() and  
                ocap.capital>0 and
                order_size<=self.cash_balance()):
                    
                order=Order(action=action, pf=pf)
                txt, order.entering_price, order.quantity=  self.place(True,
                                        action.ib_ticker(),
                                        action.currency.symbol,
                                        action.stock_ex.ib_ticker,
                                        order_size=order_size)
                
                if kwargs.get("sl",False):
                    sl=kwargs.get("sl")
                    order.sl_threshold=order.entering_price*(1-sl)
                
                order.save()
                pf.append(symbol)
                pf.save()
                ocap.capital-=1
                ocap.save()
                
                return True
            return False
        except Exception as msg:
            print("exception in " + __name__)
            print(msg)
            _, e_, exc_tb = sys.exc_info()
            print("line " + str(exc_tb.tb_lineno))
            pass

    def disconnect(self):
        self.ib.disconnect()

def check_hold_duration(symbol,strategy, exchange,short,**kwargs): 
        #type check necessary for indexes
    try:
        pf= get_pf(strategy, exchange,short)
        
        #accountSummary
        if kwargs.get("index",False):
            index=Index.objects.get(symbol=symbol)
            if short:
                action=index.etf_short
            else:
                action=index.etf_long
        else:
            action=Action.objects.get(symbol=symbol)

        if symbol in pf.retrieve():
            c1 = Q(action=action)
            c2 = Q(active=True)
            order=Order.objects.filter(c1 & c2)
            if len(order)>0:
                delta=timezone.now()-order[0].entering_date
                return delta.days
        
        return 0
    except Exception as msg:
         print("exception in " + __name__)
         print(msg)
         return 0

def entry_order(symbol,strategy, exchange,short,**kwargs): 
    if PERFORM_ORDER and DIC_PERFORM_ORDER[strategy]:
        myIB=MyIB()
        return myIB.entry_order(symbol,strategy, exchange,short,**kwargs), True
    else:   
        return entry_order_test(symbol,strategy, exchange,short,**kwargs), False
    
def exit_order(symbol,strategy, exchange,short,**kwargs): 
    if PERFORM_ORDER and DIC_PERFORM_ORDER[strategy]:
        myIB=MyIB()
        return myIB.exit_order(symbol,strategy, exchange,short,**kwargs), True
    else:   
        return exit_order_test(symbol,strategy, exchange,short,**kwargs), False

def entry_order_test(symbol,strategy, exchange,short,**kwargs): 
    try:
        #type check necessary for indexes
        pf= get_pf(strategy, exchange,short)
        ocap=get_order_capital(strategy, exchange)
        
        if kwargs.get("index",False):
            index=Index.objects.get(symbol=symbol)
            if short:
                action=index.etf_short
            else:
                action=index.etf_long
        else:
            action=Action.objects.get(symbol=symbol)
        symbol2=action.symbol
        
        excluded=Excluded.objects.get(name="all") #list of actions completely excluded from entries
        
        if (symbol2 not in pf.retrieve() and 
            symbol2 not in excluded.retrieve() and
            ocap.capital>0):
            order=Order(action=action, pf=pf)
            order.entering_price=1.0
            
            order.save()
            #post telegram
            pf.append(symbol2)
            
            pf.save()
            ocap.capital-=1 #also for short
            ocap.save()
            
            return True
        return False
    except Exception as msg:
        print("exception in " + __name__)
        print(msg)
        _, e_, exc_tb = sys.exc_info()
        print("line " + str(exc_tb.tb_lineno))
        pass
    
def exit_order_test(symbol,strategy, exchange,short,**kwargs):   
    try:
        pf= get_pf(strategy, exchange,short)
        ocap=get_order_capital(strategy, exchange)
        
        if kwargs.get("index",False):
            index=Index.objects.get(symbol=symbol) #actually should be more complex
            if short:
                action=index.etf_short
            else:
                action=index.etf_long
        else:
            action=Action.objects.get(symbol=symbol)
        symbol2=action.symbol
        
        if symbol2 in pf.retrieve():
            c1 = Q(action=action)
            c2 = Q(active=True)
            
            order=Order.objects.filter(c1 & c2)
            #post telegram
            #price
            #profit
            if len(order)>0:
                order[0].exiting_date=timezone.now()
                order[0].active=False
                order[0].save()

            ocap.capital+=1 #also for short
            ocap.save()
            pf.remove(symbol2)
            pf.save()

            return True
        return False
    
    except Exception as msg:
        print("exception in " + __name__)
        print(msg)
        _, e_, exc_tb = sys.exc_info()
        print("line " + str(exc_tb.tb_lineno))
        pass

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
    opening_time=models.TimeField(default="09:00:00")
    closing_time=models.TimeField(default="17:00:00")
    
    def __str__(self):
        return self.name    


class Strategy(models.Model):
    name=models.CharField(max_length=100, blank=False)
    
    def __str__(self):
        return self.name

### Index is like action, but it had to be separated, as an index cannot be bought directly
class Index(models.Model):
    symbol=models.CharField(max_length=15, blank=False, primary_key=True)
    ib_ticker=models.CharField(max_length=15, blank=True,default="AAA")
    name=models.CharField(max_length=100, blank=False)
    stock_ex=models.ForeignKey('StockEx',on_delete=models.CASCADE)
    currency=models.ForeignKey('Currency',on_delete=models.CASCADE)
    etf_long=models.ForeignKey('Action',on_delete=models.PROTECT,default=0,related_name='etf_long')
    etf_short=models.ForeignKey('Action',on_delete=models.PROTECT, default=0,related_name='etf_short')
    
    class Meta:
        ordering = ["name"]

    def ib_ticker(self):
        return self.ib_ticker
        
    def __str__(self):
        return self.name  

class Action(models.Model):
    symbol=models.CharField(max_length=15, blank=False, primary_key=True)
    ib_ticker=models.CharField(max_length=15, blank=True,default="AAA")
    name=models.CharField(max_length=100, blank=False)
    stock_ex=models.ForeignKey('StockEx',on_delete=models.CASCADE)
    currency=models.ForeignKey('Currency',on_delete=models.CASCADE)
    category=models.ForeignKey('ActionCategory',on_delete=models.CASCADE,blank=True)
    strategy=models.ForeignKey('Strategy',on_delete=models.CASCADE,blank=True,default=0)
    
    class Meta:
        ordering = ["name"]
        
    def ib_ticker(self):
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
            c2 = Q(stock_ex=stockEx1[0])
            actions=pf.actions.filter(c1 & c2)
        else:
            actions=pf.actions.filter(c1)
        
        for action in actions:
            if not action.symbol in arr:
                arr.append(action.symbol)
    return arr

### Portfolio for a given strategy (used as name presently)
class PF(models.Model):
    # can be replaced with ib.positions() or ib.portfolio()
    name=models.CharField(max_length=100, blank=False)
    actions=models.ManyToManyField(Action,blank=True)
    short=models.BooleanField(blank=False,default=False)
    strategy=models.ForeignKey('Strategy',on_delete=models.CASCADE,blank=True)
    stock_ex=models.ForeignKey('StockEx',on_delete=models.CASCADE,blank=True,default=2)
    
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
            print(symbol)
            print(msg)
            _, e_, exc_tb = sys.exc_info()
            print("line " + str(exc_tb.tb_lineno))
            pass    

def get_pf(strategy, exchange,short):
    
    s=Strategy.objects.get(name=strategy)
    e=StockEx.objects.get(name=exchange)

    c1 = Q(stock_ex=e)
    c2 = Q(strategy=s) 
    c3 = Q(short=short)
    
    try:
        return PF.objects.get(c1 & c2 & c3)
    except:
        name=strategy+"_"+exchange
        if short:
            name+="_short"
        pf=PF(stock_ex=e,strategy=s,short=short,name=name)
        pf.save() #create the pf
        return pf

### To distinguish between ETF, actions, indexes...
class ActionCategory(models.Model):
    short=models.CharField(max_length=15, blank=False, default="AAA", primary_key=True)
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

def get_capital(strategy, exchange,short):
    s=Strategy.objects.get(name=strategy)
    e=StockEx.objects.get(name=exchange)

    c1 = Q(stock_ex=e)
    c2 = Q(strategy=s) 
    c3 = Q(short=short)

    return Capital.objects.get(c1 & c2 & c3)

###To define the number of orders assigned to one strategy
###1 means that only one action can be owned at a time using this strategy

class OrderCapital(models.Model):
    capital=models.DecimalField(max_digits=100, decimal_places=5,blank=True,null=True)
    name=models.CharField(max_length=100, blank=False,default="")
    strategy=models.ForeignKey('Strategy',on_delete=models.CASCADE,blank=True)
    stock_ex=models.ForeignKey('StockEx',on_delete=models.CASCADE,blank=True,default=2)
    
    def __str__(self):
        return self.name 

def get_order_capital(strategy, exchange):
    s=Strategy.objects.get(name=strategy)
    e=StockEx.objects.get(name=exchange)

    c1 = Q(stock_ex=e)
    c2 = Q(strategy=s) 

    return OrderCapital.objects.get(c1 & c2)

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
    s=Strategy.objects.get(name=strategy)
    e=StockEx.objects.get(name=exchange)

    c1 = Q(stock_ex=e)
    c2 = Q(strategy=s) 

    return Candidates.objects.get(c1 & c2)
    
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
    indexes=models.ManyToManyField(Index,blank=True)   
    strategy=models.ForeignKey('Strategy',on_delete=models.CASCADE,blank=True,default=0)
    
    def retrieve(self):
        arr=[]
        for action in self.actions.all():
            arr.append(action.symbol)
        return arr    
    
    def __str__(self):
        return self.name     