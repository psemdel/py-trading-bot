#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan  6 19:41:08 2023

@author: maxime
"""

from trading_bot.settings import _settings
from vectorbtpro.data.custom import RemoteData, CCXTData
from vectorbtpro import _typing as tp
import warnings
import math
from ib_insync import MarketOrder, util
from core.indicators import rel_dif
from django.db.models import Q
from django.utils import timezone
import numbers
from decimal import Decimal
import requests

try:
    import MetaTrader5 as mt5
except ImportError:
    mt5 = tp.Any

try:
    if not tp.TYPE_CHECKING:
        raise ImportError
    from ccxt.base.exchange import Exchange as CCXTExchangeT
except ImportError:
    CCXTExchangeT = tp.Any
    
###TS???
import socket
import json

import vectorbtpro as vbt
import numpy as np
import pandas as pd

import logging
logger = logging.getLogger(__name__)
logger_trade = logging.getLogger('trade')

from orders.models import (Action, StockStatus, Order, Excluded, Strategy,
                          action_to_etf, pf_retrieve_all_symbols, check_if_index, check_ib_permission,
                          get_pf)

#Module to handle IB connection
ib_cfg={"localhost":_settings["IB_LOCALHOST"],"port":_settings["IB_PORT"]}
ib_global={"connected":False, "client":None}

'''
This file contains the interfaces to IB, YF, MT5, TS and CCXT. For instance to perform orders or retrieve data.

Aditionnally the class OrderPerformer handles the Django part of the order performance.
'''
###General functions that will route to the used API
def retrieve_quantity(action: Action):
    """
    Get the size of present position owned for a product

    Note: assuming check permission already took place
    
    Arguments
    ----------
    action: stock to be checked
    """  
    if _settings["USED_API"]["orders"]=="IB":
        return retrieve_quantity_ib(action)
    elif _settings["USED_API"]["orders"]=="CCXT":
        ccxtData=CCXTDataExt()
        return ccxtData.retrieve_quantity(action.symbol)
    elif _settings["USED_API"]["orders"]=="MT5":
        mt5Data=Mt5Data()
        return mt5Data.retrieve_quantity(action.symbol)
    elif _settings["USED_API"]["orders"] =="TS":        
        tradeStationData=TradeStationData()
        return tradeStationData.retrieve_quantity(action.symbol)

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
    
    Note: a difficulty concerns how the platform handle the currency conversion. A convert to base currency function should be created to handle this.
    
    Arguments
    ----------
    order_size: Size of the order to be performed
    st: strategy used for the trade
    """ 
    t=cash_balance(**kwargs) #currency=currency,
    money_engaged=get_money_engaged(st.name,action.stock_ex.name,False)
    enough_cash=False
    excess_money_engaged=False
    out_order_size=0
    if t is not None: 
        if t>=order_size:
            enough_cash=True
            out_order_size=order_size
        elif st.minimum_order_size is not None and t>=st.minimum_order_size:
            enough_cash=True
            out_order_size=t
         
        if st.maximum_money_engaged is not None and (money_engaged+out_order_size>=st.maximum_money_engaged):
            excess_money_engaged=True
            
    return enough_cash, out_order_size, excess_money_engaged
      
def get_money_engaged(
        strategy: str,
        exchange:str,
        short:bool,
        ):
    """
    Determine the total amount of money engaged in a strategy
    
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
        total_money_engaged+=ss.quantity*Decimal(get_last_price(action)) 
        
    return total_money_engaged

def cash_balance(currency:str="EUR",**kwargs) -> numbers.Number:
    """
    Return the cash balance for a certain currency
    
    Note: assuming check permission already took place
    
    Arguments
    ----------
    currency: symbol of the currency to be checked
    """ 
    if _settings["USED_API"]["orders"]=="IB":
        return cash_balance_ib(currency)
    elif _settings["USED_API"]["orders"]=="CCXT":
        ccxtData=CCXTDataExt()
        return ccxtData.cash_balance(currency)
    elif _settings["USED_API"]["orders"]=="MT5":
        mt5Data=Mt5Data()
        return mt5Data.cash_balance(currency)
    elif _settings["USED_API"]["alerting"] =="TS":
        tradeStationData=TradeStationData()
        return tradeStationData.cash_balance(currency)
        
def actualize_ss():
    '''
    Synchronize ib and our bot, to know which stocks are owned (+direction)     
    '''
    if _settings["USED_API"]["alerting"]=="IB":
        actualize_ss_ib()
    elif _settings["USED_API"]["alerting"]=="CCXT":
        ccxtData=CCXTDataExt()
        ccxtData.actualize_ss_ib()
    elif _settings["USED_API"]["alerting"]=="MT5": 
        mt5Data=Mt5Data()
        mt5Data.actualize_ss()
    elif _settings["USED_API"]["alerting"] =="TS": 
        tradeStationData=TradeStationData()
        tradeStationData.actualize_ss()
            
#for SL check
def get_last_price(
        action:Action,
        **kwargs):
    """
    Return the last price for a product
    
    Arguments
    ----------
    action: stock to be checked
    """     
    try:
        check_ib_permission([action.symbol]) 
        cours_pres=0
        
        if _settings["USED_API"]["alerting"] =="CCXT":
            ccxtData=CCXTDataExt()
            cours_pres=ccxtData.get_last_price(action)
        elif _settings["USED_API"]["alerting"] =="MT5":
            mt5Data=Mt5Data()
            cours_pres=mt5Data.get_last_price(action)            
        elif _settings["USED_API"]["alerting"] =="TS": 
            tradeStationData=TradeStationData()
            cours_pres=tradeStationData.get_last_price(action)       
        elif (_settings["USED_API"]["alerting"]=="IB" and\
             action.stock_ex.ib_auth and\
             action.symbol not in _settings["IB_STOCK_NO_PERMISSION"]):
            
             cours_pres=get_last_price_ib(action)            
            
        if cours_pres==0: #YF and fallback
            cours=vbt.YFData.fetch([action.symbol], period="2d")
            cours_close=cours.get("Close")
            cours_pres=cours_close[action.symbol].iloc[-1]
    
        return cours_pres

    except Exception as e:
         logger.error(e, stack_info=True, exc_info=True)

#For alerting and TSL check  
def get_ratio(action):
    """
    Return the price change today, use both IB and YF
    
    Arguments
    ----------
    action: Action to be checked
    """     
    try:
        cours_pres=0
        cours_ref=0
        
        check_ib_permission([action.symbol])
        
        if _settings["USED_API"]["alerting"] =="CCXT":
            ccxtData=CCXTDataExt()
            cours_pres, cours_ref= ccxtData.get_ratio_input(action)
        elif _settings["USED_API"]["alerting"] =="MT5":
            mt5Data=Mt5Data()
            cours_pres, cours_ref= mt5Data.get_ratio_input(action)      
        elif _settings["USED_API"]["alerting"] =="TS":  
            tradeStationData=TradeStationData()
            cours_pres, cours_ref= tradeStationData.get_ratio_input(action)      
        elif (_settings["USED_API"]["alerting"]=="IB" and\
            action.stock_ex.ib_auth and\
            action.symbol not in _settings["IB_STOCK_NO_PERMISSION"]):
            
            cours_pres, cours_ref= get_ratio_input_ib(action)

        if cours_pres==0: #YF and fallback
            cours=vbt.YFData.fetch([action.symbol], period="2d")
            cours_close=cours.get("Close")
            cours_ref=cours_close[action.symbol].iloc[0]
            cours_pres=cours_close[action.symbol].iloc[-1]
                
        if cours_pres!=0 and cours_ref!=0:
            return rel_dif(cours_pres,cours_ref)*100
        else:
            return 0

    except Exception as e:
         logger.error(e, stack_info=True, exc_info=True)
         
#Place order
def place(
        buy: bool,
        action:Action,
        quantity: numbers.Number=0,
        order_size: numbers.Number=0,
        testing: bool=False,
        **kwargs): 
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
    try:
        if _settings["USED_API"]["orders"]=="IB":
            #IB is a bit different
            place_ib(buy,action,quantity=quantity,order_size=order_size,testing=testing)
        else:
            if quantity==0:
                last_price=get_last_price(action)
                if last_price!=0:
                    quantity=math.floor(order_size/last_price)
                else:
                    return "", Decimal(1.0), Decimal(0.0)
                
                if not testing:
                    if _settings["USED_API"]["orders"] =="CCXT":
                        ccxtData=CCXTDataExt()
                        ccxt_order=ccxtData.make_order(buy,action.symbol,quantity=quantity)
                    elif _settings["USED_API"]["alerting"] =="MT5":
                        mt5Data=Mt5Data()
                        mt5_order=mt5Data.make_order(buy,action.symbol,quantity=quantity)
                    elif _settings["USED_API"]["orders"]=="TS":
                        tradeStationData=TradeStationData()
                        order_id=tradeStationData.make_order(buy,action.symbol,quantity=quantity)
                    
                    if buy:
                        txt="buying "
                    else:
                        txt="selling "
                    logger_trade.info(txt+"order sent to IB, action " + str(action.symbol)+ ", quantity: "+str(quantity))
                    #get entering price???
                    return Decimal(1.0), Decimal(1.0)
                else:
                    return Decimal(1.0), Decimal(1.0)
    except Exception as e:
         logger.error(e, stack_info=True, exc_info=True)   

### Tradestation ###
TS_API_ENDPOINT = "api.tradestation.com"

class TradeStationData(RemoteData):
    def __init__(
            self, 
            api_key: str=_settings["TD_API_KEY"]
            ):
        self.api_key = api_key
        self.base_url = 'https://api.tradestation.com/v2'
        self.connect()

    def connect(self):
        # Connect to TradeStation using the specified host and port
        response = requests.get(f'{self.base_url}/connect', headers={'Authorization': f'Bearer {self.api_key}'})
        if response.status_code == 200:
            print("Connected to TradeStation")
        else:
            raise ConnectionError("Failed to connect to TradeStation")
    
    def resolve_client(self, client=None, **client_config):
        # Resolve the TradeStation client to use for API calls
        if client is None:
            # Create a new TradeStation client with the specified configuration
            client = TradeStationClient(**client_config)
        return client
    
    def fetch_symbol(
            self, 
            symbol, 
            client=None, 
            client_config=None, 
            period=None, 
            start=None, 
            end=None, 
            timeframe=None,
            indexes=None, 
            exchanges=None):
        # Fetch historical market data for the specified symbol using TradeStation API
    
        if client is None:
            client = self.resolve_client(**client_config)
        
        # Construct the API endpoint URL based on the specified parameters
        endpoint = f"{self.base_url}/symbol/{symbol}/history"
        params = {
            'period': period,
            'start': start,
            'end': end,
            'timeframe': timeframe,
            'indexes': indexes,
            'exchanges': exchanges
        }
    
        # Send a GET request to the TradeStation API to fetch the historical data
        response = requests.get(endpoint, headers={'Authorization': f'Bearer {self.api_key}'}, params=params)
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data)
            # Convert timestamp column to datetime format
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
            df.set_index('timestamp', inplace=True)
            return df
        else:
            raise ValueError(f"Failed to fetch symbol data for symbol: {symbol}")
            
    def make_order(
            self, 
            buy: bool, 
            symbol: str,
            quantity=None,
            ):
        # Place a market order (buy/sell) for the specified action and short status using TradeStation API
        ##To be checked
        if buy:
            a="buy"
        else:
            a="sell"

        endpoint = f"{self.base_url}/orders"
        payload = {
            'action': a,
            'symbol': symbol,
            'quantity': quantity,
            'orderType': 'market',
            'timeInForce': 'day'
        }
        response = requests.post(endpoint, headers={'Authorization': f'Bearer {self.api_key}'}, json=payload)
        if response.status_code == 200:
            order_data = response.json()
            order_id = order_data['orderId']
            return order_id
        else:
            raise ValueError("Failed to place order")
            
    def retrieve_quantity(
            self, 
            buy: bool,
            symbol:str,
            **kwargs):
        """
        Get the size of present position owned for a product
        
        Arguments
        ----------
        action: stock to be checked
        """  
        # Retrieve the quantity and sign of the specified action using TradeStation API
        return 0
            
    def cash_balance(self,  currency:str="EUR")-> numbers.Number:
        '''
        Return the cash balance for a certain currency
        
        Arguments
        ----------
        currency: symbol of the currency to be checked
        '''    
        endpoint = f"{self.base_url}/account"
        response = requests.get(endpoint, headers={'Authorization': f'Bearer {self.api_key}'})
        if response.status_code == 200:
            account_data = response.json()
            cash_balance = account_data['cashBalance']
            return cash_balance
        else:
            raise ValueError("Failed to retrieve cash balance")
    
    def actualize_ss(self):
        pass
    
    def get_last_price(self, action:Action):
        # Retrieve the last price for the specified contract using TradeStation API
    
        symbol=action.symbol
        endpoint = f"{self.base_url}/symbol/{symbol}/quote"
        response = requests.get(endpoint, headers={'Authorization': f'Bearer {self.api_key}'})
        if response.status_code == 200:
            quote_data = response.json()
            last_price = quote_data['lastPrice']
            return last_price
        else:
            raise ValueError(f"Failed to retrieve last price for contract: {symbol}")

    def get_ratio_input(self, action: Action)->numbers.Number:
        symbol=action.symbol
        cours_pres=self.get_last_price(action)
        
        #How to get price from yesterday??
        return cours_pres,0

### CCXT ###
class CCXTDataExt(CCXTData):
    def __init__(
            self,
            exchange=_settings["CCXT_EXCHANGE"]
            ):
        super().__init__()
        self.exchange = self.resolve_exchange(exchange=exchange)

    #fetch symbol and resolve exchange are in CCXTData
    def make_order(
            self, 
            buy: bool,
            symbol: str, 
            type_: str='market', 
            price=None, 
            quantity=None):
        """

        Arguments
        ----------
            symbol: CCXT ticker of a product
            side: 'buy' or 'sell'
            type_: 'limit' or 'market'
            price: price for a limit order
            quantity: amount of product to trade
        """ 
        if buy:
            side="buy"
        else:
            side="sell"
        
        order_params = {
            'symbol': symbol,
            'side': side,
            'type': type_,
            'price': price,
            'quantity': quantity
        }
        ccxt_order = self.exchange.create_order(**order_params)
        return ccxt_order

    def retrieve_quantity(
            self, 
            symbol,
            **kwargs
            ):
        """
        Get the size of present position owned for a product
        
        Arguments
        ----------
        action: stock to be checked
        """  
        return self.exchange.fetchPosition(symbol)

    def cash_balance(self,  currency:str="EUR")-> numbers.Number:
        '''
        Return the cash balance for a certain currency
        
        Arguments
        ----------
        currency: symbol of the currency to be checked
        '''
        # Get the account information from the CCXT API
        account_info = self.exchange.fetchBalance()
    
        # If currency is not specified, return the account balance in the account's base currency
        if currency is None:
            return account_info['total'][account_info['base']]
    
        # Get the balance for the specified currency
        currency_balance = account_info['total'][currency]
        return currency_balance
    
    def actualize_ss(self):
        pass    
    
    def get_last_price(self, action: Action)->numbers.Number:
        ticker = self.exchange.fetch_ticker(action.symbol)
        if ticker is None:
            return 0
        return ticker['ask']

    def get_ratio_input(self, action: Action)->numbers.Number:
        symbol=action.symbol
        cours_pres=self.get_last_price(action)
        
        #Reference price??
        return cours_pres,0
        
### MT5 ###
class Mt5Data(RemoteData):
    def __init__(
            self, 
            host=_settings["MT5_HOST"], 
            port=_settings["MT5_PORT"]
            ):
        
        #super().__init__() #needed??
        self.host = host
        self.port = port
        self.client = None
        self.connect()
        
    def connect(self):
        mt5.initialize()
        connected = mt5.terminal_info().update_type != 2
        if not connected:
            connected = mt5.wait_terminal(60)
        if not connected:
            raise ConnectionError("Failed to connect to MetaTrader 5 terminal.")
        return True
    
    def resolve_client(self, client=None, **client_config):
        if client is None:
            client = mt5.TerminalInfo()
            client.update_type = 2
            client.host = self.host
            client.port = self.port
            client.name = "MetaTrader 5"
            client.config = client_config
        return client

    def fetch_symbol(self, 
                     symbol, 
                     client=None, 
                     client_config=None, 
                     period=None, 
                     start=None, 
                     end=None, 
                     timeframe=None,
                     indexes=None, 
                     exchanges=None)-> tp.Any:
        
        if client is None:
            client = self.resolve_client(**client_config)
        if period is None:
            period = mt5.TIMEFRAME_D1
        if start is not None and end is not None:
            rates = mt5.copy_rates_range(symbol, period, start, end)
        else:
            rates = mt5.copy_rates_from_pos(symbol, period, 0, 1000)
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.set_index('time', inplace=True)
        return df
    
    def make_order(self,
              buy: bool, 
              symbol: str, 
              quantity: numbers.Number=0,
              ):
        # Place market order using MT5 API
        if buy:
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": quantity,  # Specify the desired volume for the trade
                "type": mt5.ORDER_TYPE_BUY,
                "deviation": 10,  # Specify the deviation value
                "magic": 12345,  # Specify the magic number for the order
                "comment": "Buy Order"  # Specify a comment for the order
            }
        else:
            # Place long sell order
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": quantity,  # Specify the desired volume for the trade
                "type": mt5.ORDER_TYPE_SELL,
                "deviation": 10,  # Specify the deviation value
                "magic": 12345,  # Specify the magic number for the order
                "comment": "Long Sell Order"  # Specify a comment for the order
            }
    
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            raise ValueError(f"Failed to send trade order: {result.comment}")
    
        return result.order    
    
    def retrieve_quantity(self, action: Action) -> numbers.Number:
        """
        Get the size of present position owned for a product
        
        Arguments
        ----------
        action: stock to be checked
        """  
        return mt5.positions_get(symbol=action.symbol)
    
    def cash_balance(
            self, 
            currency:str="EUR", 
            **kwargs):
        '''
        Return the cash balance for a certain currency
        
        Arguments
        ----------
        currency: symbol of the currency to be checked
        '''
        account_info = mt5.account_info()
    
        # If currency is not specified, return the account balance in the account's base currency
        if currency is None:
            return account_info.balance
    
        # Get the balance for the specified currency
        currency_balance = None
        for balance in account_info.balances:
            if balance.currency == currency:
                currency_balance = balance.amount
                break
    
        return currency_balance

    def actualize_ss(self):
        for pos in mt5.positions_get():
            actions=Action.objects.filter(symbol__contains=pos.symbol)
            if len(actions)==0:
                action=None
            elif len(actions)==1:
                action=actions[0]
            else:
                for a in actions:
                    if a.symbol==pos.symbol:
                        action=a
                        
            if action is not None: 
                present_ss=StockStatus.objects.get(action=action)
                present_ss.quantity=pos.volume
                present_ss.order_in_ib=True
                present_ss.save()
                
    def get_last_price(self, action: Action)->numbers.Number:
        symbol=action.symbol
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            return 0     
        return tick.bid if tick.bid != 0 else tick.last

    def get_ratio_input(
            self, 
            action: Action,
            exchange=None, 
            index=None
            )->(numbers.Number, numbers.Number):
        # Get the current price using the mt5.symbol_info_tick() function
        symbol=action.symbol
        cours_pres=self.get_last_price(action)
        
        # Get the reference price based on the provided exchange and index
        reference_price = None
        if exchange and index:
            # Retrieve the reference price using the mt5.copy_rates_from() function
            rates = mt5.copy_rates_from(symbol, mt5.TIMEFRAME_D1, self.start_date, self.end_date)
            if rates is None or len(rates) == 0:
                return None, None
    
            # Find the reference price based on the index
            for rate in rates:
                if rate.time == index:
                    reference_price = rate.close
                    break
    
        return cours_pres, reference_price

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

class IBData(RemoteData):
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
        #check everytime
        if cls.client.isConnected():
            ib_global["connected"]=True
        else:
            ib_global["connected"]=False
        
        return cls.client

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
        it_is_indexes: tp.Optional[dict] = None,
        exchanges: tp.Optional[dict] = None,
        ) -> tp.Any:
        """
        Download data for a symbol from IB
        
        Arguments
        ----------        
        
        it_is_indexes: dict containing if the symbol is an index or not
        exchanges: dict containing the stock exchange name associated to the symbol
        
        """
        from ib_insync import util
        
        exchange="SMART" #default
        if exchanges is not None:
            if symbol in exchanges:
                exchange=exchanges[symbol]
                
        it_is_index=False
        if it_is_indexes is not None:
            if symbol in it_is_indexes:
                it_is_index=it_is_indexes[symbol]        
        
        if client_config is None:
            client_config = {}
        cls.resolve_client(client=client, **client_config)

        if ib_global["connected"]:
            contract=cls.get_contract(symbol,exchange,it_is_index)
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
    def get_last_price_sub(cls,contract):
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

    @classmethod 
    def get_contract(
            cls, 
            symbol_ib: str,
            exchange_ib: str,
            it_is_index: bool):
        """
        Search the ib contract corresponding to the product

        Arguments
        ----------
            symbol_ib: IB ticker of a product
            exchange_ib: IB ticker of the stock exchange
            it_is_index: is it indexes that are provided
        """ 
        from ib_insync import Stock, Index
        if it_is_index:
            return Index(exchange=exchange_ib,symbol=symbol_ib)
        elif exchange_ib in ["NASDAQ","NYSE"]:
            return Stock(symbol_ib,"SMART", primaryExchange=exchange_ib)
        else:
            return Stock(symbol_ib,exchange_ib)

#Following functions should be part of IBData
@connect_ib
def get_last_price_ib(
        action:Action, 
        **kwargs):
    '''
    Get the present price for a product
    
    Arguments
    ----------
    action: stock to be checked
    '''
    if kwargs['client'] and ib_global["connected"]:
        contract=IBData.get_contract(action.ib_ticker(),action.stock_ex.ib_ticker,check_if_index(action))
        if contract is not None:
            return IBData.get_last_price_sub(contract)
    return 0

@connect_ib        
def cash_balance_ib(
        currency:str="BASE",
        **kwargs
        ) -> numbers.Number:
    """
    Return the cash balance for a certain currency
    
    Arguments
    ----------
    currency: symbol of the currency to be checked
    """ 
    if kwargs['client'] and ib_global["connected"]:
        for v in kwargs['client'].accountValues():
            if v.tag == 'CashBalance' and v.currency==currency:
                return float(v.value)
    else:
        return 0

@connect_ib
def actualize_ss_ib(**kwargs):
    """
    Synchronize ib and our bot, to know which stocks are owned (+direction)     
    """      
    if kwargs['client'] and ib_global["connected"]:
        print("myIB retrieve")
        action=None

        for pos in kwargs['client'].positions():
            contract=pos.contract
            actions=Action.objects.filter(symbol__contains=contract.localSymbol)
            if len(actions)==0:
                action=None
            elif len(actions)==1:
                action=actions[0]
            else:
                for a in actions:
                    if a.ib_ticker()==contract.localSymbol:
                        action=a
                        
            if action is not None: 
                present_ss=StockStatus.objects.get(action=action)
                present_ss.quantity=pos.position
                present_ss.order_in_ib=True
                present_ss.save()  
                
@connect_ib
def retrieve_quantity_ib(
        action: Action,
        **kwargs):
    """
    Call ib and get the size of present position owned for a product

    Arguments
    ----------
    action: stock to be checked
    """  
    if kwargs['client'] and ib_global["connected"]:
        for pos in kwargs['client'].positions():
            contract=pos.contract
            if action.ib_ticker()==contract.localSymbol:
                return abs(pos.position), np.sign(pos.position), pos.position>0
    return 0, 0, False  
        
@connect_ib
def get_tradable_contract(
        action:Action,
        short:bool=False,
        **kwargs):
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
            return IBData.get_contract(action.ib_ticker(),action.stock_ex.ib_ticker,False)
        else:
            logger.info("stock "+action.ib_ticker() + " not in authorized stock exchange")
            return None 

@connect_ib  
def get_ratio_input_ib(
        action:Action,
        **kwargs):
    '''
    Return the daily change
    
    Arguments
    ----------
        action: stock for which the ratio must be retrieved
    '''
    if ib_global["connected"] and kwargs['client']:
        contract=IBData.get_contract(action.ib_ticker(),action.stock_ex.ib_ticker,check_if_index(action))
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
                cours_pres=IBData.get_last_price(contract)
                return cours_pres, cours_ref
    return 0, 0    

@connect_ib  
def place_ib(
        buy,
        action,
        quantity: numbers.Number=0,
        order_size: numbers.Number=0,
        testing: bool=False,
        **kwargs): 
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
    try:
        if kwargs['client'] and ib_global["connected"]:
            contract =IBData.get_tradable_contract(action,short=buy) #to check if it is enough
            
            if contract is None:
                return "", Decimal(1.0), Decimal(0.0)
            else:
                kwargs['client'].qualifyContracts(contract)
                
                if quantity==0:
                    last_price=IBData.get_last_price(action)
                    if last_price!=0:
                        quantity=math.floor(order_size/last_price)
                    else:
                        return "", Decimal(1.0), Decimal(0.0)
                
                if not testing:
                    if buy:
                        order = MarketOrder('BUY', quantity)
                        txt="buying "
                    else:
                        order = MarketOrder('SELL', quantity)
                        txt="selling "
                    trade = kwargs['client'].placeOrder(contract, order)
                    logger_trade.info(txt+"order sent to IB, action " + str(action.symbol)+ ", quantity: "+str(quantity))
            
                    max_time=20
                    t=0
                    
                    while t<max_time:
                        kwargs['client'].sleep(1.0)
                        t+=1
        
                        if trade.orderStatus.status == 'Filled':
                            fill = trade.fills[-1]
                            logger_trade.info(f'{fill.time} - {fill.execution.side} {fill.contract.symbol} {fill.execution.shares} @ {fill.execution.avgPrice}')
                            price=fill.execution.avgPrice     
                            return Decimal(price), Decimal(quantity)
                        
                    logger_trade.info("order not filled, pending")
                    return Decimal(1.0), Decimal(1.0)
                else:
                    return Decimal(1.0), Decimal(1.0)
    except Exception as e:
         logger.error(e, stack_info=True, exc_info=True)              
    
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
            print("several active orders have been found for: "+self.action.symbol+" , check the database")
            logger.error("several active orders have been found for: "+self.action.symbol+" , check the database")      

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
        
        Arguments
        ----------
        buy: should the order buy or sell the stock
        quantity: quantity, in number of stocks, of the stock to be ordered
        order_size: size, in currency, of the stock to be ordered
        """
        try:
            if (self.symbol in self.excluded.retrieve() ):
                logger.info(str(self.symbol) + " excluded")  
            
            #entry
            if ((self.reverse or self.symbol not in pf_retrieve_all_symbols()) and 
                 self.symbol not in self.excluded.retrieve()):
                self.new_order=Order(action=self.action, strategy=self.st, short=not buy)
                self.entry=True
                buy_sell_txt={True:"buying ", False: "selling "}
                #add reverse info
                if _settings["USED_API"]["orders"]=="IB":
                    logger_trade.info("place "+  buy_sell_txt[buy] + "order symbol: "+self.symbol+" , strategy: " + self.st.name)
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
            
                    self.new_order.entering_price=Decimal(self.new_order.entering_price)
                    self.ss.order_in_ib=True               
                else:
                    self.new_order.entering_price=Decimal(1.0) 
                    logger_trade.info("Manual " + buy_sell_txt[buy] + "order symbol: "+self.symbol+" , strategy: " + self.st.name)
                    self.ss.order_in_ib=False

                    if not buy:
                        self.ss.quantity=Decimal(-1.0)
                    else:
                        self.ss.quantity=Decimal(1.0)
                self.new_order.save()
                self.ss.save()
                self.executed=True
        except Exception as e:
            import sys
            _, e_, exc_tb = sys.exc_info()
            print(e)
            print("line " + str(exc_tb.tb_lineno))

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
        """
        if _settings["USED_API"]["orders"]=="IB":
            #safer than looking in what we saved
            present_quantity, present_sign, _=retrieve_quantity(self.action) 
        else:
            present_quantity=abs(self.ss.quantity)
            present_sign=Decimal(np.sign(self.ss.quantity))
        if "order" in self.__dir__():
            self.order.quantity=present_quantity
            self.order.save()
            
        if present_quantity!=0:
            present_size= present_sign*present_quantity*Decimal(get_last_price(self.action))
            self.reverse=True
        else:
            present_size=0
            self.reverse=False
        self.delta_size=self.target_size-present_size

    def close_order(self):
        """
        Perform change related with a close order
        """
        self.order.exiting_date=timezone.now()
        self.order.active=False
        self.order.save()
    
    def close_quantity(self):        
        self.ss.quantity=0
        self.ss.save()
    
    def sell_order_sub(self):
        """
        Subfunction for sell order
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
                if self.delta_size<0:
                    #if reverse but excluded then close without further conditions
                    if self.reverse and self.symbol not in self.excluded.retrieve():
                        self.entry_place(False, order_size=self.delta_size,testing=self.testing)     
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
                        self.order.exiting_price=Decimal(self.order.exiting_price)
                        self.close_quantity()
                    else:
                        logger_trade.info("Manual exit order symbol: "+self.symbol+" , strategy: " + self.st.name + " which is in long direction")
                        self.close_quantity()
                    self.calc_profit()
                    self.close_order()
                    return True 

        except Exception as e:
            import sys
            _, e_, exc_tb = sys.exc_info()
            print(e)
            print("line " + str(exc_tb.tb_lineno))
            logger.error(str(e) + "symbol: "+str(self.symbol), stack_info=True, exc_info=True)
            pass
    #Can be open a buy position or close a short position
    def buy_order_sub(self): 
        """
        Subfunction for buy order
        
        Compared to sell, we need to check in the beginning if there is enough cash
        """
        try:
            #type check necessary for indexes
            self.get_order(True)
            self.get_delta_size()
            
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
                logger.info(str(self.symbol) + " order not executed, not enough cash available")
            elif excess_money_engaged:
                logger.info(str(self.symbol) + " order not executed, maximum money engaged for one strategy exceeded")
            else:
                if self.new_order_bool: #we open a new long order
                    self.reverse=False
                    self.entry_place(True, order_size=order_size)
                    return self.executed
                else: 
                    self.entry=False
                    #we close or reverse an old short order
                    #profit
                    if order_size>0:
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
                            self.order.exiting_price=Decimal(self.order.exiting_price)
                            self.close_quantity()
                        else:
                            logger_trade.info("Manual exit order symbol: "+self.symbol+" , strategy: " + self.st.name +  "which is in short position")
                            self.close_quantity()
                        self.calc_profit()
                        self.close_order()
                        return True
            return False
        
        except Exception as e:
            import sys
            _, e_, exc_tb = sys.exc_info()
            print(e)
            print("line " + str(exc_tb.tb_lineno))
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


               
               
               