from django.db import models
from django.utils import timezone
from django.db.models import Q

import asyncio
from ib_insync import IB, Stock, MarketOrder, util, Contract
from core.indicators import rel_dif

import vectorbtpro as vbt
from vectorbtpro.data.custom import RemoteData
from vectorbtpro import _typing as tp

import sys
import math
import traceback

import numpy as np

from trading_bot.settings import (PERFORM_ORDER, USE_IB_FOR_DATA,DIC_PERFORM_ORDER,
                                  IB_LOCALHOST, IB_PORT, IB_STOCKEX_NO_PERMISSION, 
                                  IB_STOCK_NO_PERMISSION)

### Interactive brockers and data retrieval ###
def stk(action):
    if action.ib_ticker()=="AAA":
        return None
    else:
        s_ex=action.stock_ex.ib_ticker 
        if s_ex not in IB_STOCKEX_NO_PERMISSION:
            if action.stock_ex.ib_ticker=='NASDAQ':
                s_ex='SMART'
                return Stock(action.ib_ticker(),s_ex, action.currency.symbol,primaryExchange='NASDAQ')
            else:
                return Stock(action.ib_ticker(),s_ex, action.currency.symbol)
        else:
            print("stock "+action.ib_ticker() + " not in authorized stock exchange")
            return None

def symbol_to_exchangeticker(symbol):
    actions=Action.objects.filter(symbol=symbol)
    if len(actions)==0:
        action=Index.objects.get(symbol=symbol)
    else:
        action=actions[0]  
    return action.stock_ex.ib_ticker

def symbol_to_IBcontract(myIB,symbol):
    try:
        contract=None
        actions=Action.objects.filter(symbol=symbol)
        if len(actions)==0:
            action=Index.objects.get(symbol=symbol)
            t_contract = Contract(symbol=action.ib_ticker(),secType="IND") 
            cds=myIB.ib.reqContractDetails(t_contract)
            contracts = [cd.contract for cd in cds]
            for c in contracts:
                if (c.exchange not in IB_STOCKEX_NO_PERMISSION and 
                action.ib_ticker() not in IB_STOCK_NO_PERMISSION):
                    contract=c
                    break
            if contract is None: #fallback ETF
                contract = stk(action.etf_long)
        else:
            action=actions[0]
            contract = stk(action)
        return contract
    except:
        print("error in symbol_to_IBcontract")
        return None, None

class IBData(RemoteData):
    @classmethod
    def fetch_symbol(
        cls,
        symbol: str,
        period: tp.Optional[str] = None,
        start: tp.Optional[tp.DatetimeLike] = None,
        end: tp.Optional[tp.DatetimeLike] = None,
        timeframe: tp.Optional[str] = None,
        **kwargs,
        ) -> tp.Frame:

        try:
            myIB=kwargs.get("myIB")
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
                            
            contract=symbol_to_IBcontract(myIB,symbol)
            
            if contract is None:
                return None
            else:
                bars = myIB.ib.reqHistoricalData(
                        contract,
                        endDateTime='',
                        durationStr=period_ib, #"10 D","1 M"
                        barSizeSetting=interval, #"1 day", "1 min"
                        whatToShow='TRADES',
                        useRTH=True,
                        formatDate=1)
                t=util.df(bars)
                
                if t is not None:
                    t.columns = ['Date', 'Open', 'High', 'Low','Close','Volume','Average','BarCount']
                    t=t.set_index('Date')
                
                return t
            
        except Exception as msg:
            print(msg)
            print("exception in " + __name__)
            _, e_, exc_tb = sys.exc_info()
            print("line " + str(exc_tb.tb_lineno))
            print(msg)

## All symbols must be from same stock exchange
def retrieve_data(symbols,period,**kwargs):
    try:
        IBok=True
        myIB=None
        symbol=None
        
        if USE_IB_FOR_DATA:
            try:
                myIB=MyIB()
                clientID=1
                while clientID<=10:
                    try:
                        myIB.ib.connect(host=IB_LOCALHOST, port=IB_PORT, clientId=clientID)
                        break
                    except:                    
                        clientID+=1
                        pass
            except:
                IBok=False
                print("connection to IB failed")
                pass
        
        for symbol in symbols:
            if symbol in IB_STOCK_NO_PERMISSION:
                print("symbol " + symbol + " has no permission for IB")
                IBok=False
                break
            
            if kwargs.get("index",False):
                action=Index.objects.get(symbol=symbol)
            else:
                action=Action.objects.get(symbol=symbol)
            
            if action.stock_ex.ib_ticker in IB_STOCKEX_NO_PERMISSION:
                print("stock ex " + action.stock_ex.ib_ticker + " has no permission for IB")
                IBok=False
                break
        
        if kwargs.get("index",False):
            index_symbol=symbols[0]
            all_symbols=symbols
        else:
            index_symbol=exchange_to_symbol(action)
            all_symbols=symbols+[index_symbol]
        
        if (USE_IB_FOR_DATA and IBok) or kwargs.get("useIB",False): 
            try:
                cours=IBData.fetch(all_symbols, period=period,missing_index='drop',myIB=myIB,**kwargs)
            except:
                print("Error with IB for data retrieval, fallback with YF")
                cours=vbt.YFData.fetch(all_symbols, period=period,missing_index='drop',**kwargs)
        else:
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
                if (USE_IB_FOR_DATA and IBok) or kwargs.get("useIB",False):    
                    data=IBData.fetch([symbol], period=period,**kwargs)
                else:
                    data=vbt.YFData.fetch(symbol, period=period,**kwargs)
            
                #knowing what we drop
                close_debug=data.get("Close")
                for ii in range(len(close_debug)):
                    if math.isnan(close_debug.values[ii]):
                        print(symbol)
                        print("dropping at least " + str(close_debug.index[ii]))
        
        if myIB is not None:
            myIB.ib.disconnect()
        
        return cours_high, cours_low, cours_close, cours_open, cours_volume,  \
               cours_high_ind, cours_low_ind,  cours_close_ind, cours_open_ind,\
               cours_volume_ind
                   
    except Exception as msg:
        print(msg)
        print("symbol faulty " +(symbol or ""))
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
    elif action.stock_ex.ib_ticker=="NYSE":
        return "^DJI"
    elif action.stock_ex.ib_ticker=="BVME.ETF":
        return "^IXIC"

def get_exchange_actions(exchange,**kwargs):
    cat=ActionCategory.objects.get(short="ACT")
    stockEx=StockEx.objects.get(name=exchange)
    
    c1 = Q(category=cat)
    c2 = Q(stock_ex=stockEx)
    c3 = Q(delisted=False)
    
    if exchange=="NYSE":
        sector=kwargs.get("sector")
        if sector:
            action_sector=ActionSector.objects.get(name=sector)
            c4 = Q(sector=action_sector)
            actions=Action.objects.filter(c1 & c2 & c3 & c4)
        else:
            actions=Action.objects.filter(c1 & c2 & c3)
    else:
        actions=Action.objects.filter(c1 & c2 & c3)
    
    return [ob.symbol for ob in actions]
        
def retrieve_ib_pf():
    print("myIB retrieve")
    action=None
    
    with MyIB() as myIB:
        pf=[]
        pf_short=[]
        
        for pos in myIB.ib.positions():
            contract=pos.contract
            actions=Action.objects.filter(symbol__contains=contract.localSymbol)
            if len(actions)==1:
                action=actions[0]
            else:
                for a in actions:
                    if a.ib_ticker()==contract.localSymbol:
                        action=a

            if action is not None:            
                if pos.position>0:
                    pf.append(action.symbol)
                else:
                    pf_short.append(action.symbol)

    return pf, pf_short

#for SL check
def get_last_price(symbol,**kwargs):
    try:
        #if symbol not in ["BZ=F"]: #buggy
        s_ex=symbol_to_exchangeticker(symbol)

        if (USE_IB_FOR_DATA and s_ex not in IB_STOCKEX_NO_PERMISSION):
            with MyIB() as myIB:
                contract =symbol_to_IBcontract(myIB,symbol)
                if contract is not None:
                    cours_pres=myIB.get_last_price(contract)
        else: #YF
            cours=vbt.YFData.fetch([symbol], period="2d")
            cours_close=cours.get("Close")
            cours_pres=cours_close[symbol].iloc[-1]
    
        return cours_pres
        #else:
        #    return 0
    except Exception as msg:
        print(symbol)
        print("exception in " + __name__)
        print(msg)

def get_ratio(symbol,**kwargs):
    try:
        #if symbol not in ["BZ=F"]: #buggy
        cours_pres=0
        cours_ref=0
        s_ex=symbol_to_exchangeticker(symbol)
            
        if (USE_IB_FOR_DATA and s_ex not in IB_STOCKEX_NO_PERMISSION):
            with MyIB() as myIB:
                contract =symbol_to_IBcontract(myIB,symbol)
                if contract is not None:
                    cours_ref, cours_open=myIB.get_past_closing_price(contract) #dif between closing yesterday and opening today
                    if kwargs.get("opening",False):
                        cours_pres=cours_open
                    else:
                        cours_pres=myIB.get_last_price(contract)
   
        else: #YF
            cours=vbt.YFData.fetch([symbol], period="2d")
            cours_close=cours.get("Close")
            cours_ref=cours_close[symbol].iloc[0]
                    
            if kwargs.get("opening",False):
                cours_open=cours.get("Open")
                cours_pres=cours_open[symbol].iloc[-1]
            else:
                cours_pres=cours_close[symbol].iloc[-1]
                
        if cours_pres!=0 and cours_ref!=0:
            return rel_dif(cours_pres,cours_ref)*100
        else:
            return 0
        #else:
        #    return 0
    except Exception as msg:
        print(symbol)
        print("exception in " + __name__)
        print(msg)

class MyIB():
    def __init__(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        self.ib = IB()
    
    def __enter__(self):
        try:
            self.ib.connect(host=IB_LOCALHOST, port=IB_PORT, clientId=1)
            return self
        except:
            return self
        
    def __exit__(self, exc_type, exc_value, tb):
        #print("disconnecting myIB")
        if exc_type is not None:
            traceback.print_exception(exc_type, exc_value, tb)
        self.ib.disconnect()

    def cash_balance(self):
        try:
            for v in self.ib.accountSummary():
                if v.tag == 'CashBalance':
                    return float(v.value)
        except:
            return 0
        
    def test(self,symbol):
        action=Action.objects.get(symbol=symbol)
        contract = stk(action)
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
        timeout=2
        t=0
        m_data = self.ib.reqMktData(contract)
        while m_data.last != m_data.last and t<timeout:  #Wait until data is in. 
            t+=0.01
            self.ib.sleep(0.01)
        if t==timeout:
            m_data.last=0
        self.ib.cancelMktData(contract)
        return m_data.last
    
    def get_past_closing_price(self,contract):
        period="2 D"
        try:
            bars = self.ib.reqHistoricalData(
                    contract,
                    endDateTime='',
                    durationStr=period, #"10 D","1 M"
                    barSizeSetting='1 day', #"1 day", "1 min"
                    whatToShow='TRADES',
                    useRTH=True,
                    formatDate=1)
            if len(bars)!=0:
                df=util.df(bars)
                return df.iloc[0]["close"], df.iloc[-1]["open"]
            else:
                return 0, 0
        except:
            return 0, 0
    
    def place(self,buy,action,short,**kwargs): #quantity in euros
        contract =stk(action)
        
        if contract is None:
            return "", 0, 0
        else:
            self.ib.qualifyContracts(contract)
            
            if buy:
                order_size=kwargs.get("order_size",0)
                last_price=self.get_last_price(contract)
                quantity=math.floor(order_size/last_price)
                
                if short:
                    order = MarketOrder('SELL', quantity)
                else:
                    order = MarketOrder('BUY', quantity)
            else:
                quantity=kwargs.get("quantity",0)
                
                if short:
                    order = MarketOrder('BUY', quantity)
                else:
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
            pf= get_pf(strategy, exchange,short,**kwargs)
            ocap=get_order_capital(strategy, exchange,**kwargs)
            
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
                                           action,
                                           short,
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
            pf= get_pf(strategy, exchange,short,**kwargs)
            order_size=10000
            balance=self.cash_balance()
            if balance<order_size and balance>0.9*order_size: #tolerance on order side
                order_size=balance
            
            ocap=get_order_capital(strategy, exchange,**kwargs)
            
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
                order_size<=balance):
                    
                order=Order(action=action, pf=pf)

                txt, order.entering_price, order.quantity= self.place(True,
                                        action,
                                        short,
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
        pf= get_pf(strategy, exchange,short,**kwargs)
        
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

def entry_order(symbol,strategy, exchange,short,auto,**kwargs):
    if (PERFORM_ORDER and DIC_PERFORM_ORDER[strategy] and not kwargs.get("index",False)
        and not exchange=="XETRA" and not auto==False): #ETF trading requires too high permissions on IB, XETRA data too expansive
        print("myIB")
        with MyIB() as myIB:
            print("automatic order execution")
            return myIB.entry_order(symbol,strategy, exchange,short,**kwargs), True
    else:   
        return entry_order_test(symbol,strategy, exchange,short,**kwargs), False
    
def exit_order(symbol,strategy, exchange,short,auto,**kwargs): 
    if (PERFORM_ORDER and DIC_PERFORM_ORDER[strategy] and not kwargs.get("index",False)
        and not exchange=="XETRA" and not auto==False): #ETF trading requires too high permissions on IB, XETRA data too expansive
        with MyIB() as myIB:
            return myIB.exit_order(symbol,strategy, exchange,short,**kwargs), True
    else:   
        return exit_order_test(symbol,strategy, exchange,short,**kwargs), False

def entry_order_test(symbol,strategy, exchange,short,**kwargs): 
    try:
        #type check necessary for indexes
        pf= get_pf(strategy, exchange,short,**kwargs)
        ocap=get_order_capital(strategy, exchange,**kwargs)
        
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
        pf= get_pf(strategy, exchange,short,**kwargs)
        ocap=get_order_capital(strategy, exchange,**kwargs)
        
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
    ibticker=models.CharField(max_length=15, blank=True,default="AAA")
    name=models.CharField(max_length=100, blank=False)
    stock_ex=models.ForeignKey('StockEx',on_delete=models.CASCADE)
    currency=models.ForeignKey('Currency',on_delete=models.CASCADE)
    etf_long=models.ForeignKey('Action',on_delete=models.PROTECT,default=0,related_name='etf_long')
    etf_short=models.ForeignKey('Action',on_delete=models.PROTECT, default=0,related_name='etf_short')
    
    class Meta:
        ordering = ["name"]

    def ib_ticker(self):
        return self.ibticker
        
    def __str__(self):
        return self.name  

class Action(models.Model):
    symbol=models.CharField(max_length=15, blank=False, primary_key=True)
    #ib_ticker=models.CharField(max_length=15, blank=True,default="AAA")
    name=models.CharField(max_length=100, blank=False)
    stock_ex=models.ForeignKey('StockEx',on_delete=models.CASCADE)
    currency=models.ForeignKey('Currency',on_delete=models.CASCADE)
    category=models.ForeignKey('ActionCategory',on_delete=models.CASCADE,blank=True)
    sector=models.ForeignKey('ActionSector',on_delete=models.CASCADE,blank=True,default=10)
    strategy=models.ForeignKey('Strategy',on_delete=models.CASCADE,blank=True,default=0)
    delisted=models.BooleanField(blank=False,default=False)
    #introduction_date=models.DateTimeField(null=True, blank=True, auto_now_add=True)
    
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
            stockEx2=StockEx.objects.filter(name="NYSE")
            c2 = Q(stock_ex=stockEx1[0])
            c3 = Q(stock_ex=stockEx2[0])
            actions=pf.actions.filter(c1 & (c2|c3))
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
    sector=models.ForeignKey('ActionSector',on_delete=models.CASCADE,blank=True,default=10)
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

def get_pf(strategy, exchange,short,**kwargs):
    
    s=Strategy.objects.get(name=strategy)
    e=StockEx.objects.get(name=exchange)

    c1 = Q(stock_ex=e)
    c2 = Q(strategy=s) 
    c3 = Q(short=short)
    
    try:
        if exchange=="NYSE":
            sector=kwargs.get("sector")
            if sector:
                action_sector=ActionSector.objects.get(name=sector)
                c4 = Q(sector=action_sector)
                return PF.objects.get(c1 & c2 & c3 & c4)
        return PF.objects.get(c1 & c2 & c3)
    except:
        print("get_pf failed")
        print("strategy: " + strategy)
        print("exchange: " +exchange)
        print("short: " + short)       

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
    s=Strategy.objects.get(name=strategy)
    e=StockEx.objects.get(name=exchange)

    c1 = Q(stock_ex=e)
    c2 = Q(strategy=s) 
    c3 = Q(short=short)

    if exchange=="NYSE":
        sector=kwargs.get("sector")
        if sector:
            action_sector=ActionSector.objects.get(name=sector)
            c4 = Q(sector=action_sector)
            return Capital.objects.get(c1 & c2 & c3 & c4)

    return Capital.objects.get(c1 & c2 & c3)

###To define the number of orders assigned to one strategy
###1 means that only one action can be owned at a time using this strategy

class OrderCapital(models.Model):
    capital=models.DecimalField(max_digits=100, decimal_places=5,blank=True,null=True)
    name=models.CharField(max_length=100, blank=False,default="")
    strategy=models.ForeignKey('Strategy',on_delete=models.CASCADE,blank=True)
    stock_ex=models.ForeignKey('StockEx',on_delete=models.CASCADE,blank=True,default=2)
    sector=models.ForeignKey('ActionSector',on_delete=models.CASCADE,blank=True,default=10)
    
    def __str__(self):
        return self.name 

def get_order_capital(strategy, exchange,**kwargs):
    try:
        s=Strategy.objects.get(name=strategy)
        e=StockEx.objects.get(name=exchange)
    
        c1 = Q(stock_ex=e)
        c2 = Q(strategy=s) 
        
        if exchange=="NYSE":
            sector=kwargs.get("sector")
            if sector:
                action_sector=ActionSector.objects.get(name=sector)
                c3 = Q(sector=action_sector)
                return OrderCapital.objects.get(c1 & c2 & c3)
        return OrderCapital.objects.get(c1 & c2)
    except:
        print("get_order_capital failed for")
        print("strategy: "+ strategy)
        print("exchange: "+ exchange)

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
    
    def retrieve_index(self):
        arr=[]
        for action in self.indexes.all():
            arr.append(action.symbol)
        return arr      
    def __str__(self):
        return self.name     