#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan  6 19:41:08 2023

@author: maxime
"""

from trading_bot.settings import (PERFORM_ORDER, USE_IB_FOR_DATA,DIC_PERFORM_ORDER,
                                  IB_STOCKEX_NO_PERMISSION, IB_STOCK_NO_PERMISSION,
                                  IB_LOCALHOST, IB_PORT)
from vectorbtpro.data.custom import RemoteData
from vectorbtpro import _typing as tp
import warnings
import math
import sys
from ib_insync import MarketOrder, util
from core.indicators import rel_dif
from django.db.models import Q
from django.utils import timezone

import vectorbtpro as vbt
import numpy as np

from orders.models import (Action, Order, ActionCategory, Excluded, Strategy,
                           check_exchange_ib_permission, action_to_etf,
                           get_pf, get_order_capital, period_YF_to_ib,
                           exchange_to_index_symbol
                           )

#Module to handle IB connection

##Part of the code that should be in _settings.py in vbt
'''        
#from vectorbtpro.utils.config import ChildDict, Config, FrozenConfig                   
data = ChildDict(
    custom=Config(
        # Synthetic
        ib=FrozenConfig(
            localhost=IB_LOCALHOST,
            port=IB_PORT,
            ),
    ),
)
'''
ib_cfg={"localhost":IB_LOCALHOST,"port":IB_PORT}
ib_global={"connected":False, "client":None}

###Part of the code that should be in data/custom.py in vbt

class IBData(RemoteData):
    #_setting_keys: tp.SettingsKeys = dict(custom="data.custom.ib")
    
    @classmethod
    def connect(cls):
        #ib_cfg = cls.get_settings(key_id="custom")
        
        if not cls.client.isConnected():
            clientID=1
            while clientID<=100:
                try:
                    cls.client.connect(host=ib_cfg['localhost'], port=ib_cfg['port'], clientId=clientID)
                    break
                except:                    
                    clientID+=1
                    pass
        if cls.client.isConnected():
            ib_global["connected"]=True
        else:
            warnings.warn("connection to IB failed, check that IB is started")   
            
    @classmethod
    def resolve_client(cls, client: tp.Optional[tp.Any] = None, **client_config) -> tp.Any:
        
        #from vectorbtpro.utils.opt_packages import assert_can_import
        #assert_can_import("ib_insync")
        from ib_insync import IB
        import asyncio

        if client is None and "cls.client" not in locals(): #create a new connection
            if ib_global["client"] is None:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                cls.client=IB()
                cls.connect()
                ib_global["client"]=cls.client
            else:
                cls.client=ib_global["client"]
        elif client is not None:
            cls.client=client

        return cls.client

    @classmethod 
    def get_contract_ib(cls, symbol,exchange,index):
        #resolve client???
        
        from ib_insync import Stock, Index
        if index:
            return Index(exchange=exchange,symbol=symbol)
        elif exchange=="NASDAQ":
            return Stock(symbol,"SMART", primaryExchange='NASDAQ')
        else:
            return Stock(symbol,exchange)
        return None

    @classmethod
    def fetch_symbol(
        cls,
        symbol: str, 
        client: tp.Optional[tp.Any] = None,
        client_config: tp.KwargsLike = None,
        period: tp.Optional[str] = None,
        start: tp.Optional[tp.DatetimeLike] = None,
        end: tp.Optional[tp.DatetimeLike] = None,
        timeframe: tp.Optional[str] = None,
        indexes: tp.Optional[dict] = None,
        exchanges: tp.Optional[dict] = None,
        ) -> tp.Any:

        #from vectorbtpro.utils.opt_packages import assert_can_import
        #assert_can_import("ib_insync")
        from ib_insync import util
        
        exchange="SMART" #default
        if exchanges is not None:
            if symbol in exchanges:
                exchange=exchanges[symbol]
                
        index=False
        if indexes is not None:
            if symbol in indexes:
                index=indexes[symbol]        
        
        if client_config is None:
            client_config = {}
        cls.resolve_client(client=client, **client_config)

        if ib_global["connected"]:
            contract=cls.get_contract_ib(symbol,exchange,index)
            #check period and timeframe
            bars = cls.client.reqHistoricalData(
                    contract,
                    endDateTime='',
                    durationStr=period, #"10 D","1 M"
                    barSizeSetting=timeframe, #"1 day", "1 min"
                    whatToShow='TRADES',
                    useRTH=True,
                    formatDate=1)
            df=util.df(bars)
            
            if df is not None:
                df.rename(
                    columns={
                        "date":"Date",
                        "open": "Open",
                        "high": "High",
                        "low": "Low",
                        "close": "Close",
                        "volume": "Volume",
                        "average":"Average",
                        "barCount": 'BarCount',
                    },
                    inplace=True,
                )
                df=df.set_index('Date')
            
            return df
        
    @classmethod
    def get_last_price(cls,contract):
        timeout=2
        t=0
        cls.resolve_client(client=None)
        m_data = cls.client.reqMktData(contract)
        while m_data.last != m_data.last and t<timeout:  #Wait until data is in. 
            t+=0.01
            cls.client.sleep(0.01)
        if t==timeout:
            m_data.last=0
        cls.client.cancelMktData(contract)
        return m_data.last
    
# Part customized for the bot
###IB management, moved to vbt principally

#decorator
def connect_ib(func):
    def wrapper(*args,**kwargs):
        kwargs['client'] = IBData.resolve_client(None)
        return func(*args,**kwargs)
    return wrapper

@connect_ib
def get_tradable_contract_ib(action,short,**kwargs):
    if action.ib_ticker()=="AAA":
        print("stock "+action.ib_ticker() + " not found")
        return None
    else:
        if action.stock_ex.ib_ticker not in IB_STOCKEX_NO_PERMISSION:
            action=action_to_etf(action,short) #if index replace the index through the corresponding ETF
            return IBData.get_contract_ib(action.ib_ticker(),action.stock_ex.ib_ticker,False)
        else:
            print("stock "+action.ib_ticker() + " not in authorized stock exchange")
            return None

@connect_ib
def retrieve_ib_pf(**kwargs):
    if kwargs['client']:
        print("myIB retrieve")
        action=None
        
        pf=[]
        pf_short=[]
        
        for pos in kwargs['client'].positions():
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
    else:
        return None, None

@connect_ib        
def cash_balance(self,**kwargs):
    if kwargs['client']:
        for v in kwargs['client'].accountSummary():
            if v.tag == 'CashBalance':
                return float(v.value)
    else:
        return 0

#for SL check
@connect_ib
def get_last_price(action,**kwargs):
    try:
        #if symbol not in ["BZ=F"]: #buggy
        if kwargs['client'] and (USE_IB_FOR_DATA and action.stock_ex.ib_ticker not in IB_STOCKEX_NO_PERMISSION):
            contract=IBData.get_contract_ib(action.ib_ticker(),action.stock_ex.ib_ticker,check_if_index(action))
            if contract is not None:
                cours_pres=IBData.get_last_price(contract)
        else: #YF
            cours=vbt.YFData.fetch([action.symbol], period="2d")
            cours_close=cours.get("Close")
            cours_pres=cours_close[action.symbol].iloc[-1]
    
        return cours_pres

    except Exception as msg:
        print(action.symbol)
        print("exception in " + __name__)
        print(msg)
        
@connect_ib  
def get_ratio(action,**kwargs):
    try:
        #if symbol not in ["BZ=F"]: #buggy
        cours_pres=0
        cours_ref=0
            
        if kwargs['client'] and (USE_IB_FOR_DATA and action.stock_ex.ib_ticker not in IB_STOCKEX_NO_PERMISSION):
            contract=IBData.get_contract_ib(action.ib_ticker(),action.stock_ex.ib_ticker,check_if_index(action))
            if contract is not None:
                bars = kwargs['client'].reqHistoricalData(
                        contract,
                        endDateTime='',
                        durationStr="2 D", #"10 D","1 M"
                        barSizeSetting='1 day', #"1 day", "1 min"
                        whatToShow='TRADES',
                        useRTH=True,
                        formatDate=1)
                if len(bars)!=0:
                    df=util.df(bars)
                    cours_ref=df.iloc[0]["close"] #closing price of the day before
                    cours_open=df.iloc[-1]["open"]

                if kwargs.get("opening",False):
                    cours_pres=cours_open
                else:
                    cours_pres=IBData.get_last_price(contract)
   
        else: #YF
            cours=vbt.YFData.fetch([action.symbol], period="2d")
            cours_close=cours.get("Close")
            cours_ref=cours_close[action.symbol].iloc[0]
                    
            if kwargs.get("opening",False):
                cours_open=cours.get("Open")
                cours_pres=cours_open[action.symbol].iloc[-1]
            else:
                cours_pres=cours_close[action.symbol].iloc[-1]
                
        if cours_pres!=0 and cours_ref!=0:
            return rel_dif(cours_pres,cours_ref)*100
        else:
            return 0

    except Exception as msg:
        print(action.symbol)
        print("exception in " + __name__)
        print(msg)

@connect_ib  
def place(buy,action,short,**kwargs): #quantity in euros
    contract =get_tradable_contract_ib(action,short)
    
    if contract is None:
        return "", 0, 0
    else:
        kwargs['client'].qualifyContracts(contract)
        
        if buy:
            order_size=kwargs.get("order_size",0)
            last_price=IBData.get_last_price(contract)
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
        trade = kwargs['client'].placeOrder(contract, order)

        kwargs['client'].sleep(1.0)
        if trade.orderStatus.status == 'Filled':
            fill = trade.fills[-1]
            txt=f'{fill.time} - {fill.execution.side} {fill.contract.symbol} {fill.execution.shares} @ {fill.execution.avgPrice}'
            price=fill.execution.avgPrice     
            return txt, price, quantity

@connect_ib  
def exit_order_sub(symbol,strategy, exchange,short,use_IB,**kwargs):   
    #type check necessary for indexes
    try:
        pf= get_pf(strategy, exchange,short,**kwargs)
        ocap=get_order_capital(strategy, exchange,**kwargs)
        action=Action.objects.get(symbol=symbol)
        action=action_to_etf(action,short)
        
        if symbol in pf.retrieve():
            c1 = Q(action=action)
            c2 = Q(active=True)
            
            order=Order.objects.filter(c1 & c2)

            #profit
            if len(order)>0:
                if use_IB:
                    txt, order[0].exiting_price, quantity= place(False,
                                           action,
                                           short,
                                           quantity=order[0].quantity)
                    
                    if order[0].entering_price is not None: 
                        order[0].profit=order[0].exiting_price-order[0].entering_price
                        order[0].profit_percent=(order[0].exiting_price/order[0].entering_price-1)*100
                    
                order[0].exiting_date=timezone.now()
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
    
@connect_ib 
def entry_order_sub(symbol,strategy, exchange,short,use_IB,**kwargs): 
    try:
        #type check necessary for indexes
        pf= get_pf(strategy, exchange,short,**kwargs)
        ocap=get_order_capital(strategy, exchange,**kwargs)
        
        if use_IB:
            order_size=10000
            balance=kwargs['client'].cash_balance()
        else:
            order_size=1
            balance=10 #to get true
        
        if balance<order_size and balance>0.9*order_size: #tolerance on order side
            order_size=balance
        
        action=Action.objects.get(symbol=symbol)
        strategy_none, _ = Strategy.objects.get_or_create(name="none")
        excluded, _=Excluded.objects.get_or_create(name="all",strategy=strategy_none) #list of actions completely excluded from entries
        
        if (symbol not in pf.retrieve() and 
            symbol not in excluded.retrieve() and  
            ocap.capital>0 and
            order_size<=balance):

            order=Order(action=action, pf=pf)

            if use_IB:
                txt, order.entering_price, order.quantity= place(True,
                                        action,
                                        short,
                                        order_size=order_size)

                if kwargs.get("sl",False):
                    sl=kwargs.get("sl")
                    order.sl_threshold=order.entering_price*(1-sl)
            else:
                order.entering_price=1.0                    
            
            order.save()
            pf.append(action.symbol)
            pf.save()
            ocap.capital-=1
            ocap.save()
            
            return True

        return False
    
    except Exception as msg:
        print("exception in " + __name__)
        print(msg)
        print("symbol: "+symbol)
        _, e_, exc_tb = sys.exc_info()
        print("line " + str(exc_tb.tb_lineno))
        pass
   
def check_hold_duration(symbol,strategy, exchange,short,**kwargs): 
        #type check necessary for indexes
    try:
        pf= get_pf(strategy, exchange,short,**kwargs)
        
        action=Action.objects.get(symbol=symbol)
        action=action_to_etf(action,short)
        #accountSummary
        if action.symbol in pf.retrieve():
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
     
@connect_ib 
def entry_order(symbol,strategy, exchange,short,auto,**kwargs):
    try:
        if kwargs['client'] and (PERFORM_ORDER and DIC_PERFORM_ORDER[strategy] #and not kwargs.get("index",False)
            and check_exchange_ib_permission(exchange) and not auto==False): #ETF trading requires too high permissions on IB, XETRA data too expansive
            print("automatic order execution")
            return entry_order_sub(symbol,strategy, exchange,short,True,**kwargs), True
        else: 
            print("manual")
            t=entry_order_sub(symbol,strategy, exchange,short,False,**kwargs)
            print(t)
            return t, False

    except Exception as msg:
         print("exception in " + __name__)
         print(msg)
         _, e_, exc_tb = sys.exc_info()
         print("line " + str(exc_tb.tb_lineno))
         return False, False

@connect_ib     
def exit_order(symbol,strategy, exchange,short,auto,**kwargs): 
    if kwargs['client'] and (PERFORM_ORDER and DIC_PERFORM_ORDER[strategy] #and not kwargs.get("index",False)
        and check_exchange_ib_permission(exchange) and not auto==False): #ETF trading requires too high permissions on IB, XETRA data too expansive
        return exit_order_sub(symbol,strategy, exchange,short,True,**kwargs), True
    else:   
        return exit_order_sub(symbol,strategy, exchange,short,False,**kwargs), False
 
def check_if_index(action):
    if action.category==ActionCategory.objects.get(short="IND"):
        return True
    else:
        return False    
 
# All symbols must be from same stock exchange
#IB need a ticker, an exchange and information about the type of product to find the correct contract
def retrieve_data_ib(actions,period,**kwargs):
    try:
        period=period_YF_to_ib(period)
        exchanges={}
        indexes={}
        ib_symbols=[]
        
        for a in actions:
            ib_symbol=a.ib_ticker()
            ib_symbols.append(ib_symbol)
            exchanges[ib_symbol]=a.stock_ex.ib_ticker
            indexes[ib_symbol]=kwargs.get("index",False)
        
        #add the index to the list of stocks downloaded. Useful to make calculation on the index to determine trends
        #by downloading at the same time, we are sure the signals are aligned
        if kwargs.get("index",False):
            index_symbol=ib_symbols[0]
            all_symbols=ib_symbols
        else:
            index_symbol_ib, index_symbol=exchange_to_index_symbol(actions[0].stock_ex.ib_ticker) 
            all_symbols= ib_symbols+[index_symbol_ib]
            indexes[index_symbol_ib]=True
            action=Action.objects.get(symbol=index_symbol)
            exchanges[index_symbol_ib]=action.stock_ex.ib_ticker    
        
        return IBData.fetch(
            all_symbols, 
            period=period,
            missing_index='drop',
            timeframe="1 day", #see also interval_YF_to_ib
            exchanges=exchanges,
            indexes=indexes),\
            ib_symbols,\
            index_symbol_ib
    except Exception as msg:
        print(msg)
        print("exception in " + __name__)
        _, e_, exc_tb = sys.exc_info()
        print("line " + str(exc_tb.tb_lineno))    

#YF can work with only the symbol to obtain the right contract
def retrieve_data_YF(actions,period,**kwargs):
    #add the index to the list of stocks downloaded. Useful to make calculation on the index to determine trends
    #by downloading at the same time, we are sure the signals are aligned
    try:
        symbols=[a.symbol for a in actions]
        if kwargs.get("index",False):
            index_symbol=symbols[0]
            all_symbols=symbols
        else:
            _, index_symbol=exchange_to_index_symbol(actions[0].stock_ex.ib_ticker)  
            all_symbols=symbols+[index_symbol]
            
        return vbt.YFData.fetch(all_symbols, period=period,missing_index='drop',**kwargs),\
               symbols,\
               index_symbol    
    except Exception as msg:
        print(msg)
        print("exception in " + __name__)
        _, e_, exc_tb = sys.exc_info()
        print("line " + str(exc_tb.tb_lineno))
        
def retrieve_data(actions,period,use_IB,**kwargs):
    if actions is None or len(actions)==0:
        raise ValueError("List of symbols empty")
    else:
        if use_IB:
            try:
                cours, symbols, index_symbol=retrieve_data_ib(actions,period,**kwargs)
            except:
                print("IB retrieval of symbol failed, fallback on YF")
                use_IB=False #fallback
        if not use_IB:
            cours, symbols, index_symbol=retrieve_data_YF(actions,period,**kwargs)
        
        print(symbols)
        print(index_symbol)
        print(cours.get('Open').columns)

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
        
        return cours_high, cours_low, cours_close, cours_open, cours_volume,  \
               cours_high_ind, cours_low_ind,  cours_close_ind, cours_open_ind,\
               cours_volume_ind, use_IB
               
               
               