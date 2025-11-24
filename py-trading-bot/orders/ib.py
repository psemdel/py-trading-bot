#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan  6 19:41:08 2023

@author: maxime
"""
from trading_bot.settings import _settings

import vectorbtpro as vbt
from vectorbtpro.data.custom import RemoteData
from vectorbtpro import _typing as tp

import warnings
import math
from ib_async import MarketOrder, util, Forex, Option
from core.indicators import rel_dif
from django.db.models import Q
from django.utils import timezone
import numbers
import sys

from datetime import datetime, timedelta

import numpy as np

import logging
logger = logging.getLogger(__name__)
logger_trade = logging.getLogger('trade')

from orders.models import (Action, StockStatus, Order, Excluded, Strategy,
                          action_to_etf, pf_retrieve_all_symbols, check_if_index, check_ib_permission,
                          get_pf, pf_retrieve_all)

#Module to handle IB connection
ib_cfg={"localhost":_settings["IB_LOCALHOST"],"port":_settings["IB_PORT"]}
ib_global={"connected":False, "client":None}

'''
This file contains the interfaces to IB, YF, and potentially other APIs. For instance to perform orders or retrieve data.

Aditionnally the class OrderPerformer handles the Django part of the order performance.
'''
###General functions that will route to the used API
### Interactive brokers ###
def connect_ib(func):
    '''
    Wrapper to check that the connection to IB has been established
    
    Establishing the connection if one is already opened leads to a crash, that's why we need such a complex logic
    '''
    def wrapper(*args,**kwargs):
        kwargs['client'] = IBData.resolve_client(None)
        return func(*args,**kwargs)
    return wrapper

@connect_ib
def retrieve_quantity(
        action: Action,
        **kwargs
        ):
    """
    Get the size of present position owned for a product

    Note: assuming check permission already took place
    
    Arguments
    ----------
    action: stock to be checked
    """  
    if _settings["USED_API"]["orders"]=="IB":
        return IBData.retrieve_quantity(action)

@connect_ib
def convert_to_base(
        currency: str,
        quantity: numbers.Number,
        inverse: bool=False,
        **kwargs
        ):
    """
    Convert the amount in the base currency

    Arguments
    ----------
        currency: symbol of the origin currency of the amount to be converted
        quantity: amount to be converted
        inverse: convert in the other way
    """   
    if _settings["USED_API"]["orders"]=="":
        logger.error("_settings[USED_API][orders] is empty in convert_to_base")
    
    if _settings["USED_API"]["orders"]=="IB":
        return IBData.convert_to_base(currency, quantity, inverse=inverse)
    
    #no implementatation for YF yet, normally ticket in the form EUR=X, JPX=X

@connect_ib
def check_enough_cash(
        order_size: numbers.Number,
        st:Strategy, 
        action:Action, 
        currency:str=None,
        **kwargs
        )-> (bool, numbers.Number, bool):
    """
    Simple check, to determine if we have enough currency to perform an order. Adjust the order is necessary. 
    Also check that the maximum amount of money engaged is not too high.
    
    In IB, BASE is amount of cash you have in your base currency after conversion of the others currencies in your account.
    
    out_order_size is in the custom currency
    
    Arguments
    ----------
        order_size: Size of the order to be performed
        st: strategy used for the trade
        action: stock implyed in the order
        currency: symbol of the currency of the product
    """ 
    base_order_size=convert_to_base(currency,order_size)
    base_cash=cash_balance(None) #for IB "BASE" is the one that allows determining if you 
    money_engaged=get_money_engaged(st.name,action.stock_ex.name,False)
    
    enough_cash=False
    excess_money_engaged=False
    out_order_size=0
    base_out_order_size=0

    if base_cash is not None: 
        if base_cash>=base_order_size:
            enough_cash=True
            out_order_size=order_size
            base_out_order_size=convert_to_base(currency,out_order_size)
        elif st.minimum_order_size is not None and base_cash>=st.minimum_order_size:
            enough_cash=True
            out_order_size=convert_to_base(currency,base_cash,inverse=True)
            base_out_order_size=base_cash
        
        if st.maximum_money_engaged is not None and (money_engaged+base_out_order_size>st.maximum_money_engaged):
            logger.info("excess_money_engaged for strategy: "+st.name+" candidate: "+action.name)
            excess_money_engaged=True
            
    return enough_cash, out_order_size, excess_money_engaged
 
@connect_ib       
def get_money_engaged(
        strategy: str,
        exchange:str,
        short:bool,
        **kwargs
        )-> float:
    """
    Determine the total amount of money engaged in a strategy
    
    total_money_engaged in base currency
    
    Arguments
    ----------
        strategy: name of the strategy
        exchange: name of the stock exchange
        short: if the products are presently in a short direction
    """ 
    symbols=get_pf(strategy, exchange, short)
    
    total_money_engaged=0
    for symbol in symbols:
        action=Action.objects.get(symbol=symbol)
        ss=StockStatus.objects.get(action=action)
        price=get_last_price(action)

        if price is not None:
            price_base=convert_to_base(action.currency.symbol,price)
            total_money_engaged+=ss.quantity*price_base
        else:
            logger.info("price for "+symbol+" is nan")
        
    return total_money_engaged

@connect_ib
def cash_balance(currency:str,**kwargs) -> numbers.Number:
    """
    Return the cash balance for a certain currency
    
    Default currency may depend on the platform, BASE is probably only available on IB  
    Note: assuming check permission already took place
    
    Arguments
    ----------
    currency: symbol of the currency to be checked
    """ 
    if _settings["USED_API"]["orders"]=="":
        logger.error("_settings[USED_API][orders] is empty in cash balance")
    
    if _settings["USED_API"]["orders"]=="IB":
        if currency is None:
            currency="BASE"
            
        return IBData.cash_balance(currency)
    
@connect_ib        
def actualize_ss(**kwargs):
    '''
    Synchronize ib and our bot, to know which stocks are owned (+direction)     
    
    Here we don't need to check really the permission, we just want to check the pf
    '''
    if _settings["USED_API_DEFAULT"]["orders"]=="IB":
        IBData.actualize_ss()

#for SL check
@connect_ib
def get_last_price(
        action:Action,
        **kwargs):
    """
    Return the last price for a product
    
    Arguments
    ----------
    action: stock to be checked
    """     
  
    check_ib_permission([action.symbol],verbose=False) #to populate USED_API
    cours_pres=0
   
    if (_settings["USED_API"]["alerting"]=="IB" and\
         action.stock_ex.ib_auth and\
         action.symbol not in _settings["IB_STOCK_NO_PERMISSION"]):

         cours_pres=IBData.get_last_price(action)           

    if cours_pres==0: #YF and fallback
        cours=vbt.YFData.fetch([action.symbol], period="2d")
        cours_close=cours.get("Close")
        cours_pres=cours_close[action.symbol].iloc[-1]

    return cours_pres

#For alerting and TSL check 
@connect_ib 
def get_ratio(action,**kwargs):
    """
    Return the price change today, use both IB and YF
    
    Arguments
    ----------
    action: Action to be checked
    """     
    cours_pres=0
    cours_ref=0
    
    check_ib_permission([action.symbol],verbose=False) #to populate USED_API
    
    if (_settings["USED_API"]["alerting"]=="IB" and\
        action.stock_ex.ib_auth and\
        action.symbol not in _settings["IB_STOCK_NO_PERMISSION"]):
        
        cours_pres, cours_ref= IBData.get_ratio_input(action)

    if cours_pres==0: #YF and fallback
        cours=vbt.YFData.fetch([action.symbol], period="2d")
        cours_close=cours.get("Close")
        cours_ref=cours_close[action.symbol].iloc[0]
        cours_pres=cours_close[action.symbol].iloc[-1]
            
    if cours_pres!=0 and cours_ref!=0:
        return rel_dif(cours_pres,cours_ref)*100
    else:
        return 0
         
#Place order
@connect_ib
def place(
        buy: bool,
        action:Action,
        quantity: numbers.Number=0,
        order_size: numbers.Number=0,
        testing: bool=False,
        **kwargs) -> (numbers.Number, numbers.Number): 
    """
    Place an order
    
    Arguments
    ----------
    buy: should the order buy or sell the stock
    action: stock to be checked
    quantity: quantity, in number of stocks, of the stock to be ordered
    order_size: size, in currency, of the stock to be ordered
    testing: set to True to perform unittest on the function
    """       
    if _settings["USED_API"]["orders"]=="IB":
        #IB is a bit different
        if not testing:
            return IBData.place(buy,action,quantity=quantity,order_size=order_size,testing=testing)
        else:
            return 1.0, 1.0
    else:
        if quantity==0:
            last_price=get_last_price(action)
            if last_price!=0:
                quantity=math.floor(order_size/last_price)
            else:
                logger.info("last price is zero for "+action.symbol)
                return 1.0, 0.0
            
            if not testing:
                if buy:
                    txt="buying "
                else:
                    txt="selling "
                logger_trade.info(txt+"order sent to IB, action " + str(action.symbol)+ ", quantity: "+str(quantity))
                #get entering price???
                return 1.0, 1.0
            else:
                return 1.0, 1.0

class IBData(RemoteData):
    def __init__(cls,*args,**kwargs):
        cls.resolve_client(None)
        super().__init__(*args,**kwargs)
    
    @classmethod
    def connect(cls):
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
    def resolve_client(
            cls, 
            client: tp.Optional[tp.Any] = None, 
            **client_config) -> tp.Any:
        from ib_async import IB
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
        #check everytime
        if cls.client.isConnected():
            ib_global["connected"]=True
        else:
            ib_global["connected"]=False
        
        return cls.client

    @classmethod
    def convert_end_date(cls,input_date):
        if input_date=='' or type(input_date)==datetime:
            return input_date
        elif type(input_date)==str:
            return datetime.strptime(input_date,"%Y-%m-%d") #format normally used by YF and assumed        

    @classmethod
    def fetch_symbol(
        cls,
        symbol: str, 
        client: tp.Optional[tp.Any] = None,
        client_config: tp.KwargsLike = None,
        period: tp.Optional[str] = None,
        start: tp.Optional[tp.DatetimeLike] = None,
        end: tp.Optional[tp.DatetimeLike] = '',
        timeframe: tp.Optional[str] = None,
        it_is_indexes: tp.Optional[dict] = None,
        exchanges: tp.Optional[dict] = None,
        currencies: tp.Optional[dict] = None,
        ) -> tp.Any:
        """
        Download data for a symbol from IB
        
        Arguments
        ----------        
        
        it_is_indexes: dict containing if the symbol is an index or not
        exchanges: dict containing the stock exchange name associated to the symbol
        
        """
        from ib_async import util

        exchange="SMART" #default
        if exchanges is not None:
            if symbol in exchanges:
                exchange=exchanges[symbol]
                
        it_is_index=False
        if it_is_indexes is not None:
            if symbol in it_is_indexes:
                it_is_index=it_is_indexes[symbol]  
                
        currency=None
        if currencies is not None:
            if symbol in currencies:
                currency=currencies[symbol]

        if client_config is None:
            client_config = {}
        cls.resolve_client(client=client, **client_config)

        if ib_global["connected"]:
    
            contract=cls.get_contract(symbol,exchange,it_is_index,currency)
            #check period and timeframe
            bars = cls.client.reqHistoricalData(
                    contract,
                    endDateTime=cls.convert_end_date(end),
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
    def get_last_price_sub(cls,contract):
        timeout=2
        t=0
        out=0
        cls.resolve_client(client=None)
        cls.client.qualifyContracts(contract)
        m_data = cls.client.reqMktData(contract)
        while (m_data.last != m_data.last) and (m_data.bid != m_data.bid) and t<timeout:  #Wait until data is in. 
            t+=0.1
            cls.client.sleep(0.1)

        if np.isnan(m_data.last):
            if not np.isnan(m_data.bid):
                out=m_data.bid
        else:
            out=m_data.last
        cls.client.cancelMktData(contract)

        return out
    
    @classmethod 
    def get_contract(
            cls, 
            symbol_ib: str,
            exchange_ib: str,
            it_is_index: bool,
            currency: str):
        """
        Search the ib contract corresponding to the product

        Arguments
        ----------
            symbol_ib: IB ticker of a product
            exchange_ib: IB ticker of the stock exchange
            it_is_index: is it indexes that are provided
            currency: currency symbol
        """ 
        from ib_async import Stock, Index
        
        if it_is_index:
            return Index(exchange=exchange_ib,symbol=symbol_ib)
        else:
            if currency is None:
                return Stock(symbol_ib,"SMART", primaryExchange=exchange_ib)
            else:
                return Stock(symbol_ib,"SMART", currency, primaryExchange=exchange_ib)
            
    @classmethod 
    def convert_to_base(
            cls, 
            currency: str,
            quantity: numbers.Number,
            inverse: bool=False
            ):    
        """
        Convert the amount in the base currency

        Arguments
        ----------
            currency: symbol of the origin currency of the amount to be converted
            quantity: amount to be converted
            inverse: convert in the other way
        """     
        if currency==_settings["IB_BASE_CURRENCY"]:
            return quantity
        
        revert=False
        if currency in ["USD","GBP"]: #no need to make a try and fail
            revert=True
            contract=Forex(_settings["IB_BASE_CURRENCY"]+currency)
        else:
            try:
                contract=Forex(currency+_settings["IB_BASE_CURRENCY"])
            except:
                contract=Forex(_settings["IB_BASE_CURRENCY"]+currency)
                revert=True
        
        price=cls.get_last_price_sub(contract)
        if price==0 or np.isnan(price) and not revert:
            contract=Forex(_settings["IB_BASE_CURRENCY"]+currency)
            revert=True
            price=cls.get_last_price_sub(contract)
        
        if price==0 or np.isnan(price):
            logger.info("Currency conversion from "+currency+" to BASE, failed.")
            return quantity
        
        if (not inverse and not revert) or (inverse and revert):
            return quantity*price
        else:
            return quantity/price
    
    @classmethod     
    def find_option(cls,
                    action: Action,
                    buy:bool, 
                    min_days_distance: int,
                    max_strike_distance_per: numbers.Number,
                    ):
        '''
        Find the cheapest option for a set of predefined parameters

        Arguments
        ----------
            action: stock to be checked
            buy: should the order buy or sell the stock
            max_strike_distance_per: distance in percent between the strike price and present price
            min_days_distance: minimum time between now and the expiration of the option
        '''
        if type(action)==str:
            action=Action.objects.get(symbol=action)  
        
        contract=cls.get_contract(action.ib_ticker(),action.stock_ex.ib_ticker,False,action.currency.symbol)
        cls.client.qualifyContracts(contract)
        price=cls.get_last_price_sub(contract)
        
        if buy:
            min_strike_abs=price
            max_strike_abs=price*(1+max_strike_distance_per/100)
        else:
            min_strike_abs=price*(1-max_strike_distance_per/100)
            max_strike_abs=price
        
        chains = cls.client.reqSecDefOptParams(contract.symbol, '', contract.secType, contract.conId)

        if len(chains)>0:
            chain = next(c for c in chains) # if c.tradingClass == action.ib_ticker() and c.exchange == action.stock_ex.ib_ticker
            buy_to_right={True:"C",False:"P"}
            
            date_limit=datetime.now()+timedelta(days=min_days_distance)
            expirations = sorted(exp for exp in chain.expirations)
            
            for kk, e in enumerate(expirations):
                if datetime(int(e[:4]),int(e[4:6]),int(e[6:8]))>date_limit:
                    break
            expirations=expirations[kk:]    
            
            strikes = [strike for strike in chain.strikes if min_strike_abs < strike < max_strike_abs]
            
            contracts = [ Option(action.ib_ticker(), expiration, strike, buy_to_right[buy], 'SMART', tradingClass=action.ib_ticker()) 
            for expiration in expirations 
            for strike in strikes]

            contracts = cls.client.qualifyContracts(*contracts)
            tickers = cls.client.reqTickers(*contracts)
            tickers =sorted(tickers, key=lambda tup: tup.bid)
            return tickers[0]
        else:
            print("no option found")
    

    @classmethod 
    def get_last_price(
            self,
            action:Action, 
            ):
        '''
        Get the present price for a product
        
        Arguments
        ----------
        action: stock to be checked
        '''
        if self.client and ib_global["connected"]:
            contract=self.get_contract(action.ib_ticker(),action.stock_ex.ib_ticker,check_if_index(action),action.currency.symbol)
            if contract is not None:
                return self.get_last_price_sub(contract)
        logger.info("return 0")
        return 0
    
    @classmethod 
    def cash_balance(
            self,
            currency:str="BASE",
            **kwargs
            ) -> numbers.Number:
        """
        Return the cash balance for a certain currency
        
        Arguments
        ----------
        currency: symbol of the currency to be checked
        """ 
        if self.client and ib_global["connected"]:
            for v in self.client.accountValues():
                if v.tag == 'CashBalance' and v.currency==currency:
                    return float(v.value)
        else:
            return 0
    
    @classmethod 
    def actualize_ss(self,**kwargs):
        """
        Synchronize ib and our bot, to know which stocks are owned (+direction)     
        """      
        actions_in_pf=pf_retrieve_all(only_in_ib=True)
        if self.client and ib_global["connected"]:
            print("myIB retrieve")

            #check already in IB but not in pf, so bought manually
            for pos in self.client.positions():
                contract=pos.contract
                actions=Action.objects.filter(symbol__contains=contract.localSymbol)
                action=None
                action_back_up=None
                actions_back_up=[]
                
                if len(actions)==1:
                    action=actions[0]
                elif len(actions)>1:
                    for a in actions:
                        if a.ib_ticker()==contract.localSymbol and a.stock_ex.ib_ticker==contract.exchange:
                            action=a
                        elif a.ib_ticker()==contract.localSymbol:
                            action_back_up=a
                            actions_back_up.append(action_back_up)
                        
                    if action is None:
                        logger.info("Combination, ticker: "+contract.localSymbol+" exchange: "+contract.exchange + " not found in database")
                        if action_back_up is not None:
                            logger.info("But combination, ticker: "+contract.localSymbol+" exchange: "+action_back_up.stock_ex.ib_ticker + " found in database")

                if action is not None: 
                    if action in actions_in_pf:
                        actions_in_pf.remove(action)
                    
                    present_ss=StockStatus.objects.get(action=action)
                    if present_ss.quantity!=pos.position:
                        if pos.position==0:
                            logger.info(action.symbol+" quantity actualized from "+ str(present_ss.quantity) +" to " + str(pos.position) + ", strategy set to none")
                        else:
                            logger.info(action.symbol+" quantity actualized from "+ str(present_ss.quantity) +" to " + str(pos.position) + ", update manually the strategy")
                        present_ss.quantity=pos.position
                        present_ss.strategy=Strategy.objects.get(name="none")
                        present_ss.order_in_ib=True
                        present_ss.save() 
            #in pf but not anymore in IB, so sold manually
            for action in actions_in_pf: #only those remaining
                if action not in actions_back_up: #to avoid the case of ISLAND exchange used outside of business hours
                    logger_trade.info(action.symbol+" quantity actualized from "+ str(present_ss.quantity) +" to 0")
                    present_ss=StockStatus.objects.get(action=action)
                    present_ss.quantity=0
                    present_ss.strategy=Strategy.objects.get(name="none")
                    present_ss.order_in_ib=False
                    present_ss.save() 
    
    @classmethod 
    def retrieve_quantity(
            self,
            action: Action,
            ):
        """
        Call ib and get the size of present position owned for a product
    
        Arguments
        ----------
        action: stock to be checked
        """  
        if self.client and ib_global["connected"]:
            for pos in self.client.positions():
                contract=pos.contract
                if action.ib_ticker()==contract.localSymbol:
                    logger.info("position")
                    logger.info(pos.position)
                    logger.info(abs(pos.position))
                    
                    return abs(pos.position), np.sign(pos.position), pos.position<0
        return 0, 0, False  
    
    @classmethod 
    def get_tradable_contract(
            self,
            action:Action,
            short:bool=False,
            ):
        """
        IB works with contract, this function find the contract
    
        Arguments
        ----------
            action: Action for which the contract must be retrieved
            short: direction of the trade
        """       
        if action.ib_ticker()=="AAA":
            logger.info("stock "+action.ib_ticker() + " not found")
            return None
        else:
            if action.stock_ex.ib_auth:
                action=action_to_etf(action,short) #if index replace the index through the corresponding ETF
                return self.get_contract(action.ib_ticker(),action.stock_ex.ib_ticker,False, action.currency.symbol)
            else:
                logger.info("stock "+action.ib_ticker() + " not in authorized stock exchange")
                return None 
            
    @classmethod 
    def get_ratio_input(
            self,
            action:Action,
            **kwargs):
        '''
        Return the daily change
        
        Arguments
        ----------
            action: stock for which the ratio must be retrieved
        '''
        if ib_global["connected"] and self.client:
            contract=self.get_contract(action.ib_ticker(),action.stock_ex.ib_ticker,check_if_index(action),action.currency.symbol)
            if contract is not None:
                bars = self.client.reqHistoricalData(
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
                    cours_pres=self.get_last_price_sub(contract)

                    if cours_pres in [0, -1]: #probably market closed presently
                        logger.error("Present price not found in IB for: "+action.ib_ticker()+ " falling back on historical data")
                        cours_pres=df.iloc[-1]["close"]
                    
                    return cours_pres, cours_ref
            else:
                print("Contract for: "+action.ib_ticker()+ " not found")
        return 0, 0    
    
    @classmethod 
    def place(
            self,
            buy,
            action,
            quantity: numbers.Number=0,
            order_size: numbers.Number=0,
            testing: bool=False,
            ) -> (numbers.Number, numbers.Number): 
        """
        Place an order
        
        IB needs a quantity>0, if none is available, it will be deduced from the quantity
        
        Arguments
        ----------
        buy: should the order buy or sell the stock
        action: stock to be checked
        quantity: quantity, in number of stocks, of the stock to be ordered
        order_size: size, in currency, of the stock to be ordered
        testing: set to True to perform unittest on the function
        """       
        if self.client and ib_global["connected"]:
            contract =self.get_tradable_contract(action,short=not buy) #to check if it is enough
            
            if contract is None:
                return 1.0, 0.0
            else:
                self.client.qualifyContracts(contract)
                if quantity==0 or quantity is None:
                    last_price=self.get_last_price(action)
                    if last_price!=0:
                        if order_size is not None and order_size!=0:
                            quantity=math.floor(abs(order_size)/last_price)
                        else:
                            logger.error("quantity and order size for : " + action.symbol + " are None or 0!")
                            return 1.0, 0.0
                    else:
                        logger.error("last price for symbol: " + action.symbol + " is nan!")
                        return 1.0, 0.0
                else:
                    quantity=abs(quantity)
                    logger.info("quantity got from quantity")
                    logger.info(quantity)
               
                if not testing:
                    if buy:
                        order = MarketOrder('BUY', quantity)
                        txt="buying "
                    else:
                        order = MarketOrder('SELL', quantity)
                        txt="selling "
                    trade = self.client.placeOrder(contract, order)
                    logger_trade.info(txt+"order sent to IB, action " + str(action.symbol)+ ", quantity: "+str(quantity))
            
                    max_time=20
                    t=0
                    
                    while t<max_time:
                        self.client.sleep(1.0)
                        t+=1
        
                        if trade.orderStatus.status == 'Filled':
                            fill = trade.fills[-1]
                            logger_trade.info(f'{fill.time} - {fill.execution.side} {fill.contract.symbol} {fill.execution.shares} @ {fill.execution.avgPrice}')
                            price=fill.execution.avgPrice     
                            return price, quantity
                        
                    logger_trade.info("order not filled, pending")
                    return 1.0, 1.0
                else:
                    return 1.0, 1.0
    
class OrderPerformer():
    def __init__(
            self,
            symbol: str,
            strategy_id: int,
            target_size: numbers.Number,
            testing: bool=False):
        """
        Class which contains all methods related to performing order, independently from the brocker

        Arguments
        ----------
        symbol: YF ticker of the stock
        strategy_id: id of the strategy used to determine which orders must be performed
        target_size: after the order, which position should we have for this stock
        testing: set to True to perform unittest on the function
        """
        for k in ["symbol","strategy_id","target_size","testing"]:
            setattr(self,k,locals()[k])

        self.executed=False
        
        try: 
            self.action=Action.objects.get(symbol=symbol) #action_to_etf not anymore needed normally
            self.st=Strategy.objects.get(id=strategy_id)
            self.ss=StockStatus.objects.get(action=self.action)
            
            strategy_none, _ = Strategy.objects.get_or_create(name="none")
            self.excluded, _=Excluded.objects.get_or_create(name="all",strategy=strategy_none) #list of actions completely excluded from entries
        except Exception as e:
            logger.error(e, stack_info=True, exc_info=True)
            logger.error("action: " + str(symbol)+ ", strat: " + str(strategy_id) + " not found")
    
    @connect_ib    
    def check_auto_manual(self,**kwargs):
        """
        Check if an order should be performed automatically (in IB) or manually (here noted as YF, but you cannot perform orders with YF)
        
        Similar to check_ib_permission
        """
        _settings["USED_API"]["orders"]="YF" #default
        
        if self.action.stock_ex.perform_order and self.st.perform_order and _settings["PERFORM_ORDER"]: #auto
            if _settings["USED_API_DEFAULT"]["orders"] in ["IB","CCXT","MT5","TS"]:
                
                _settings["USED_API"]["orders"]=_settings["USED_API_DEFAULT"]["orders"]
                
            elif ( _settings["USED_API"]["orders"]=="IB" and
                (self.action.symbol in _settings["IB_STOCK_NO_PERMISSION"]) and
                (self.action.stock_ex.ib_auth) and
                (not check_if_index(self.action) or (check_if_index(self.action) and _settings["ETF_IB_auth"])) #ETF trading requires too high permissions on IB, XETRA data too expansive
                (ib_global["connected"] and kwargs['client'])
                ):
                
                _settings["USED_API"]["orders"]=_settings["USED_API_DEFAULT"]["orders"]

    def get_order(self,buy: bool):
        """
        Search for an open order corresponding to the new one
        
        Arguments
        ----------
        buy: should the order buy or sell the stock
        """
        c1 = Q(action=self.action)
        c2 = Q(active=True)
        orders=Order.objects.filter(c1 & c2)

        if len(orders)>1:
            logger.error("several active orders have been found for: "+self.action.symbol+", check the database")      

        if len(orders)==0:
            self.new_order_bool=True
        else: #Already and order
            self.new_order_bool=False
            self.order=orders[0]

    def entry_place(
            self, 
            buy: bool,
            quantity: numbers.Number=None,
            order_size: numbers.Number=None,
            ):
        """
        Function to perform an entry order, the Django part is within it. Place has the IB part
        
        It always create a new order. In case of reverse, the old order needs to be closed elsewhere. It populates the new order
        Contains the logic to make the split between stock size and option size to be traded
        The conversion quantity / order_size is in place(), except if no IB is used       
        
        Arguments
        ----------
        buy: should the order buy or sell the stock
        quantity: quantity, in number of stocks, of the stock to be ordered
        order_size: size, in currency, of the stock to be ordered, has a sign
        """
        
        if (self.symbol in self.excluded.retrieve() ):
            logger.info(str(self.symbol) + " excluded")  
        
        #entry
        if ((self.reverse or self.symbol not in pf_retrieve_all_symbols()) and 
             self.symbol not in self.excluded.retrieve()):
            self.new_order=Order(action=self.action, strategy=self.st, short=not buy)
            self.entry=True
            self.ss.strategy=self.st
            buy_sell_txt={True:"buying ", False: "selling "}
            #add reverse info
            if _settings["USED_API"]["orders"]=="IB":
                logger_trade.info("place "+  buy_sell_txt[buy] + "order symbol: "+self.symbol+" , strategy: " + self.st.name)
                
                if order_size is not None:
                    order_size_option=self.st.option_share_per*order_size
                    order_size_stock=order_size-order_size_option
                else:
                    order_size_option=0

                self.new_order.entering_price, _= place(buy,
                                        self.action,
                                        quantity=quantity,
                                        order_size=order_size,
                                        testing=self.testing
                                        )
                logger_trade.info("entering_price: "+ str(self.new_order.entering_price))
                self.new_order.quantity, sign, short=retrieve_quantity(self.action)
     
                self.ss.quantity=sign*self.new_order.quantity
                
                self.new_order.short=short
        
                if self.st.sl_threshold is not None and self.st.sl_threshold !=0:
                    if short:
                        self.new_order.sl_threshold=self.new_order.entering_price*(1+self.st.sl_threshold)
                    else:
                        self.new_order.sl_threshold=self.new_order.entering_price*(1-self.st.sl_threshold)
                if self.st.daily_sl_threshold is not None and self.st.daily_sl_threshold !=0:
                    self.new_order.daily_sl_threshold=self.st.daily_sl_threshold
        
                self.new_order.entering_price=self.new_order.entering_price
                self.ss.order_in_ib=True   
                
                if order_size_option!=0:
                    option=self.find_option(
                        self.action, 
                        buy, 
                        self.st.option_min_days_distance,
                        self.option_max_strike_distance_per
                        )
                    if option is not None:
                        place(buy,
                            self.action,
                            order_size=order_size_option,
                            testing=self.testing
                            )
            else:
                last_price=get_last_price(self.action)
                if last_price!=0 and order_size is not None:
                    quantity=math.floor(abs(order_size)/last_price) #sign is brought back with buy
                else:
                    quantity=1
                self.new_order.entering_price=1.0
                logger_trade.info("Manual " + buy_sell_txt[buy] + "order symbol: "+self.symbol+" , strategy: " + self.st.name)
                self.ss.order_in_ib=False

                if not buy:
                    self.ss.quantity=-1.0*quantity
                else:
                    self.ss.quantity=1.0*quantity
                    
            self.new_order.save()
            self.ss.save()
            self.executed=True

    def calc_profit(self):
        """
        Calculate the profit realized on an order that is going to be closed
        """
        if self.order.exiting_price is not None and self.order is not None and self.order.entering_price is not None: 
            self.order.profit=self.order.exiting_price-self.order.entering_price
            if self.order.entering_price != 0:
                self.order.profit_percent=(self.order.exiting_price/self.order.entering_price-1)*100
        self.order.save()
        
    def get_delta_size(self):
        """
        Calculate the difference between the desired final position (self.target_size)
        and the present position (self.order.quantity) for a stock (self.action)
        
        It returns a size = price, not a quantity
        
        self.target_size has a sign, self.delta_size has a sign also
        """
        if _settings["USED_API"]["orders"]=="IB":
            #safer than looking in what we saved
            present_quantity, present_sign, _=retrieve_quantity(self.action) 
        else:
            present_quantity=abs(self.ss.quantity)
            present_sign=np.sign(self.ss.quantity)

        if "order" in self.__dir__():
            self.order.quantity=present_quantity
            self.order.save()
        self.reverse=False    
        
        if present_quantity!=0:
            self.present_size= present_sign*present_quantity*get_last_price(self.action)

            if present_sign !=0 and np.sign(self.target_size)!=0 and present_sign!= np.sign(self.target_size):
                self.reverse=True
        else:
            self.present_size=0
        
        self.delta_size=self.target_size-self.present_size 

    def close_order(self):
        """
        Perform change related with a close order
        """
        self.order.exiting_date=timezone.now()
        self.order.active=False
        self.order.save()
    
    def close_quantity(self):        
        self.ss.quantity=0
        self.ss.strategy=Strategy.objects.get(name="none")
        self.ss.save()
    
    def sell_order_sub(self):
        """
        Subfunction for sell order
        
        Main logic:
            - If it is a new order, do it
            - If present position >0 and we want <-0, it is a reverse, close present order and create a new one. get_delta_size() calculate the correct amount.
              Rest of the logic is in entry_place()
            - If present position >0 and we want 0, then it is not a reverse, we just close
            - If the symbol is now excluded we need to go to 0, see last step
            - If we want 0 and are not using IB, then send a telegram order
        """
        try:
            self.get_order(False)
            
            if self.new_order_bool:   #we open a short order
                self.reverse=False
                self.entry_place(False, order_size=self.target_size)
                return self.executed   
            else:#we close or reverse an old long order
                self.entry=False
                self.get_delta_size()
                #profit
                if self.delta_size<0 and self.present_size>=0: #if self.present_size is negative, no change
                    #if reverse but excluded then close without further conditions
                    if self.reverse and self.symbol not in self.excluded.retrieve():
                        self.entry_place(False, order_size=self.delta_size)     
                        self.order.exiting_price=self.new_order.entering_price
                    elif _settings["USED_API"]["orders"]=="IB":
                        if self.reverse:
                            logger.info(str(self.symbol) + " excluded, reverse order converted to close") 
                        
                        logger_trade.info("place exit order symbol: "+self.symbol+" , strategy: " + self.st.name + " which was in long direction")
                        self.order.exiting_price, quantity= place(False,
                                               self.action,
                                               quantity=self.order.quantity,
                                               testing=self.testing
                                               )
                        self.close_quantity()
                    else:
                        logger_trade.info("Manual exit order symbol: "+self.symbol+" , strategy: " + self.st.name + " which is in long direction")
                        self.close_quantity()
                    self.calc_profit()
                    self.close_order()
                    return True 

        except Exception as e:
            _, e_, exc_tb = sys.exc_info()
            logger.error(str(e) + "symbol: "+str(self.symbol), stack_info=True, exc_info=True)
            pass
    #Can be open a buy position or close a short position
    def buy_order_sub(self): 
        """
        Subfunction for buy order
        
        Compared to sell_order_sub, we need to check in the beginning if there is enough cash. The order_size is therefore not always equal to
        self.delta_size
        """
        try:
            #type check necessary for indexes
            self.get_order(True)
            self.get_delta_size()
            
            #The order_size need to be corrected if the money is not sufficient
            if _settings["USED_API"]["orders"]!="YF":
                enough_cash, order_size, excess_money_engaged=check_enough_cash(
                                                                self.delta_size,
                                                                self.st,
                                                                self.action, 
                                                                currency=self.action.currency.symbol
                                                                )
            else:
                enough_cash=True
                order_size=self.delta_size
                excess_money_engaged=False    

            if not enough_cash:
                logger_trade.info(str(self.symbol) + " order not executed, not enough cash available")
            elif excess_money_engaged:
                logger_trade.info(str(self.symbol) + " order not executed, maximum money engaged for one strategy exceeded")
            else:
                if self.new_order_bool: #we open a new long order
                    self.reverse=False
                    self.entry_place(True, order_size=order_size)
                    return self.executed
                else: 
                    self.entry=False
                    #we close or reverse an old short order
                    #profit
                    if order_size>0 and self.present_size<=0:
                        #if reverse but excluded then close without further conditions
                        if self.reverse and self.symbol not in self.excluded.retrieve():
                            self.entry_place(True, order_size=order_size)
                            self.order.exiting_price=self.new_order.entering_price
                        elif _settings["USED_API"]["orders"]=="IB" :
                            if self.reverse:
                                logger.info(str(self.symbol) + " excluded, reverse order converted to close") 
                                
                            logger_trade.info("place exit order symbol: "+self.symbol+" , strategy: " + self.st.name + " which was in short position")
                            self.order.exiting_price, quantity= place(True,
                                                   self.action,
                                                   quantity=self.order.quantity,
                                                   testing=self.testing)
                            self.order.exiting_price=self.order.exiting_price
                            self.close_quantity()
                        else:
                            logger_trade.info("Manual exit order symbol: "+self.symbol+" , strategy: " + self.st.name +  " which is in short position")
                            self.close_quantity()
                        self.calc_profit()
                        self.close_order()
                        return True
            return False
        
        except Exception as e:
            _, e_, exc_tb = sys.exc_info()
            logger.error(str(e) + "symbol: "+str(self.symbol), stack_info=True, exc_info=True)
            pass

    @connect_ib     
    def buy_order(self,**kwargs):
        '''
        Main function to place a buy order
        '''
        self.check_auto_manual(**kwargs)
        return self.buy_order_sub()
    
    @connect_ib     
    def sell_order(self,**kwargs):
        '''
        Main function to place a sell order
        '''
        self.check_auto_manual(**kwargs)
        return self.sell_order_sub()


               
               
               
