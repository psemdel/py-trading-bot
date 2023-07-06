#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan  6 19:41:08 2023

@author: maxime
"""

from trading_bot.settings import _settings
from vectorbtpro.data.custom import RemoteData
from vectorbtpro import _typing as tp
import warnings
import math
from ib_insync import MarketOrder, util
from core.indicators import rel_dif
from django.db.models import Q
from django.utils import timezone
import numbers
from decimal import Decimal

try:
    import MetaTrader5 as mt5
except ImportError:
    mt5 = tp.Any

import vectorbtpro as vbt
import numpy as np
import pandas as pd

import logging
logger = logging.getLogger(__name__)
logger_trade = logging.getLogger('trade')

from orders.models import (Action, StockStatus, Order, ActionCategory, Excluded, Strategy,
                          action_to_etf, period_YF_to_ib, exchange_to_index_symbol, 
                          pf_retrieve_all_symbols)

#Module to handle IB connection
ib_cfg={"localhost":_settings["IB_LOCALHOST"],"port":_settings["IB_PORT"]}
ib_global={"connected":False, "client":None}


class mt5Data(RemoteData):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.client = None
        
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

    def get_contract_mt5(self, symbol, exchange, index):
        contract = mt5.symbol_info(symbol)
        if not contract.visible:
            raise ValueError(f"Symbol {symbol} is not available.")
        return contract

    def fetch_symbol(self, 
                     symbol, 
                     client=None, 
                     client_config=None, 
                     period=None, 
                     start=None, 
                     end=None, 
                     timeframe=None,
                     indexes=None, 
                     exchanges=None):
        
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

def get_last_price_mt5(self, contract):
    tick = mt5.symbol_info_tick(contract.name)
    return tick.bid if tick.bid != 0 else tick.last

def connect_mt5(func):
    def wrapper(self, *args, **kwargs):
        self.connect()
        return func(self, *args, **kwargs)
    return wrapper

@connect_mt5
def mt5_place(self, buy, action, short, **kwargs):
    symbol = kwargs.get('symbol')
    # Place market order using MT5 API
    if buy:
        # Place buy order
        if short:
            # Place short buy order
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": 0.01,  # Specify the desired volume for the trade
                "type": mt5.ORDER_TYPE_SELL,
                "deviation": 10,  # Specify the deviation value
                "magic": 12345,  # Specify the magic number for the order
                "comment": "Short Buy Order"  # Specify a comment for the order
            }
        else:
            # Place long buy order
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": 0.01,  # Specify the desired volume for the trade
                "type": mt5.ORDER_TYPE_BUY,
                "deviation": 10,  # Specify the deviation value
                "magic": 12345,  # Specify the magic number for the order
                "comment": "Long Buy Order"  # Specify a comment for the order
            }
    else:
        # Place sell order
        if short:
            # Place short sell order
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": 0.01,  # Specify the desired volume for the trade
                "type": mt5.ORDER_TYPE_BUY,
                "deviation": 10,  # Specify the deviation value
                "magic": 12345,  # Specify the magic number for the order
                "comment": "Short Sell Order"  # Specify a comment for the order
            }
        else:
            # Place long sell order
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": 0.01,  # Specify the desired volume for the trade
                "type": mt5.ORDER_TYPE_SELL,
                "deviation": 10,  # Specify the deviation value
                "magic": 12345,  # Specify the magic number for the order
                "comment": "Long Sell Order"  # Specify a comment for the order
            }

    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        raise ValueError(f"Failed to send trade order: {result.comment}")

    return result.order

def get_tradable_contract_mt5(
        self, 
        action, 
        short, 
        symbol:list=None,
        **kwargs):
    # Assuming the symbol and other required parameters are provided
    if action == 'buy':
        trade_action = mt5.TRADE_ACTION_DEAL
    elif action == 'sell':
        trade_action = mt5.TRADE_ACTION_DEAL
    else:
        raise ValueError(f"Invalid action: {action}")

    if short:
        trade_type = mt5.ORDER_TYPE_SELL
    else:
        trade_type = mt5.ORDER_TYPE_BUY

    request = {
        "action": trade_action,
        "symbol": symbol,
        "volume": 0.01,  # Specify the desired volume for the trade
        "type": trade_type,
        "deviation": 10,  # Specify the deviation value
        "magic": 12345,  # Specify the magic number for the order
        "comment": "Trade order"  # Specify a comment for the order
    }

    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        raise ValueError(f"Failed to send trade order: {result.comment}")

    return result.order


def retrieve_quantity_mt5(self, in_action, **kwargs):
    symbol = kwargs.get('symbol')
    # Assuming the symbol and other required parameters are provided
    if in_action == 'buy':
        position_type = mt5.POSITION_TYPE_BUY
    elif in_action == 'sell':
        position_type = mt5.POSITION_TYPE_SELL
    else:
        raise ValueError(f"Invalid action: {in_action}")

    # Get the positions for the specified symbol
    positions = mt5.positions_get(symbol=symbol)
    if not positions:
        return 0

    # Filter positions based on the specified action
    filtered_positions = [p for p in positions if p.type == position_type]

    # Calculate the total quantity for the filtered positions
    total_quantity = sum(p.volume for p in filtered_positions)

    return total_quantity

def retrieve_mt5_pf(self, **kwargs):
    # Get the current positions from the MetaTrader 5 API
    positions = mt5.positions_get()

    long_positions = []
    short_positions = []

    for position in positions:
        if position.volume > 0:
            # Long position
            long_positions.append({
                'symbol': position.symbol,
                'volume': position.volume,
                'entry_price': position.price_open,
                'current_price': position.price_current
            })
        elif position.volume < 0:
            # Short position
            short_positions.append({
                'symbol': position.symbol,
                'volume': abs(position.volume),
                'entry_price': position.price_open,
                'current_price': position.price_current
            })

    return long_positions, short_positions


def mt5_check_enough_cash(self, order_size, **kwargs):
    # Get the account information from the MetaTrader 5 API
    account_info = mt5.account_info()

    # Check if the account has enough cash balance to cover the order size
    if account_info.balance >= order_size:
        return True
    else:
        return False

def mt5_cash_balance(self, currency=None, **kwargs):
    # Get the account information from the MetaTrader 5 API
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

def mt5_get_ratio(self, action, symbol, exchange=None, index=None):
    # Get the current price using the mt5.symbol_info_tick() function
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        return None

    # Calculate the ratio based on the action (Buy or Sell)
    if action == 'Buy':
        current_price = tick.ask
    elif action == 'Sell':
        current_price = tick.bid
    else:
        return None

    # Get the reference price based on the provided exchange and index
    reference_price = None
    if exchange and index:
        # Retrieve the reference price using the mt5.copy_rates_from() function
        rates = mt5.copy_rates_from(symbol, mt5.TIMEFRAME_D1, self.start_date, self.end_date)
        if rates is None or len(rates) == 0:
            return None

        # Find the reference price based on the index
        for rate in rates:
            if rate.time == index:
                reference_price = rate.close
                break

    # Calculate the ratio as a percentage
    if reference_price is not None:
        ratio = (current_price / reference_price) * 100.0
        return ratio

    return None

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
    def resolve_client(cls, client: tp.Optional[tp.Any] = None, **client_config) -> tp.Any:
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
    def get_contract_ib(
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
            contract=cls.get_contract_ib(symbol,exchange,it_is_index)
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
        logger.info("stock "+action.ib_ticker() + " not found")
        return None
    else:
        if action.stock_ex.ib_auth:
            action=action_to_etf(action,short) #if index replace the index through the corresponding ETF
            return IBData.get_contract_ib(action.ib_ticker(),action.stock_ex.ib_ticker,False)
        else:
            logger.info("stock "+action.ib_ticker() + " not in authorized stock exchange")
            return None

@connect_ib
def retrieve_quantity(action: Action, **kwargs):
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
def actualize_ss(**kwargs):
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
def check_enough_cash(order_size: numbers.Number,currency:str=None,**kwargs)-> bool:
    """
    Simple check, to determine if we have enough currency to perform an 
    
    Arguments
    ----------
    order_size: Size of the order to be performed
    """ 
    if cash_balance(currency=currency,**kwargs) is not None and cash_balance(currency=currency,**kwargs)>=order_size:
        return True
    else:
        #fallback, if there is enough EUR, IB will convert
        if cash_balance(currency="EUR",**kwargs)>=order_size:
            return True
        else:
            return False
        
@connect_ib        
def cash_balance(currency:str="EUR",**kwargs) -> numbers.Number:
    """
    Return the cash balance for a certain currency
    """ 
    if kwargs['client'] and ib_global["connected"]:
        for v in kwargs['client'].accountValues():
            if v.tag == 'CashBalance' and v.currency==currency:
                return float(v.value)
    else:
        return 0

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
    try:
        if kwargs['client'] and ib_global["connected"] and\
            (_settings["USED API_FOR_DATA"]["alerting"]=="IB" and\
                               action.stock_ex.ib_auth and\
                                  action.symbol not in _settings["IB_STOCK_NO_PERMISSION"]):
            
            contract=IBData.get_contract_ib(action.ib_ticker(),action.stock_ex.ib_ticker,check_if_index(action))
            if contract is not None:
                cours_pres=IBData.get_last_price(contract)
        else: #YF
            cours=vbt.YFData.fetch([action.symbol], period="2d")
            cours_close=cours.get("Close")
            cours_pres=cours_close[action.symbol].iloc[-1]
    
        return cours_pres

    except Exception as e:
         logger.error(e, stack_info=True, exc_info=True)
         
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
    
#For alerting and TSL check        
@connect_ib  
def get_ratio(action,**kwargs):
    """
    Return the price change today, use both IB and YF
    
    Arguments
    ----------
    action: Action to be checked
    """     
    try:
        cours_pres=0
        cours_ref=0

        if ib_global["connected"] and kwargs['client']  and\
              (_settings["USED API_FOR_DATA"]["alerting"]=="IB" and\
                                 action.stock_ex.ib_auth and\
                                  action.symbol not in _settings["IB_STOCK_NO_PERMISSION"]):
            
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
                    cours_pres=IBData.get_last_price(contract)
   
        else: #YF
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

@connect_ib  
def place(
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
    action: Action to be checked
    quantity: quantity, in number of stocks, of the stock to be ordered
    order_size: size, in currency, of the stock to be ordered
    """       
    try:
        if kwargs['client'] and ib_global["connected"]:
            contract =get_tradable_contract_ib(action,buy) #to check if it is enough
            
            if contract is None:
                return "", Decimal(1.0), Decimal(0.0)
            else:
                kwargs['client'].qualifyContracts(contract)
                
                if quantity==0:
                    last_price=IBData.get_last_price(contract)
                    quantity=math.floor(order_size/last_price)
                
                if not testing:
                    if buy:
                        order = MarketOrder('BUY', quantity)
                        txt="buying "
                    else:
                        order = MarketOrder('SELL', quantity)
                        txt="selling "
                    trade = kwargs['client'].placeOrder(contract, order)
                    logger_trade.info(txt+"order sent to IB, action " + str(action)+ ", quantity: "+str(quantity))
            
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
        """
        if (kwargs['client'] and ib_global["connected"] and
               _settings["PERFORM_ORDER"] and
               (not check_if_index(self.action) or (check_if_index(self.action) and _settings["ETF_IB_auth"])) and #ETF trading requires too high 
               self.action.stock_ex.perform_order and  #ETF trading requires too high permissions on IB, XETRA data too expansive
               self.st.perform_order):

            self.api_used="IB"
        else: 
            self.api_used="YF"

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
            '''
            if (buy and self.order.short==True) or (sell and self.order.short==False):
                entry=False
            else:
                entry=True -> means normally no new order is needed
            '''
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
                if self.api_used=="IB":
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
        if self.api_used=="IB":
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
                    elif self.api_used=="IB":
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
            
            if self.api_used=="IB":
                enough_cash=check_enough_cash(self.delta_size,currency=self.action.currency.symbol)
            else:
                enough_cash=True
                
            if not enough_cash:
                logger.info(str(self.symbol) + " order not executed, not enough cash available")
            else:
                if self.new_order_bool: #we open a new long order
                    self.reverse=False
                    self.entry_place(True, order_size=self.target_size)
                    return self.executed
                else: 
                    self.entry=False
                    #we close or reverse an old short order
                    #profit
                    if self.delta_size>0:
                        #if reverse but excluded then close without further conditions
                        if self.reverse and self.symbol not in self.excluded.retrieve():
                            self.entry_place(True, order_size=self.delta_size)
                            self.order.exiting_price=self.new_order.entering_price
                        elif self.api_used=="IB" :
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

###Functions to retrieve data
@connect_ib 
def retrieve_data_ib(
        actions: list,
        period: str,
        it_is_index: bool=False
        ) -> (pd.core.frame.DataFrame, list, str):
    """
    Retrieve the data using IB

    Note: All symbols must be from same stock exchange
    IB need a ticker, an exchange and information about the type of product to find the correct contract

    Arguments
    ----------
        actions: list of products to be downloaded
        period: time period for which data should be downloaded
        it_is_index: is it indexes that are provided
    """   
    try:
        period=period_YF_to_ib(period)
        exchanges={}
        it_is_indexes={}
        ib_symbols=[]
        
        for a in actions:
            ib_symbol=a.ib_ticker()
            ib_symbols.append(ib_symbol)
            exchanges[ib_symbol]=a.stock_ex.ib_ticker
            it_is_indexes[ib_symbol]=it_is_index
        
        #add the index to the list of stocks downloaded. Useful to make calculation on the index to determine trends
        #by downloading at the same time, we are sure the signals are aligned
        if it_is_index:
            index_symbol=ib_symbols[0]
            all_symbols=ib_symbols
        else:
            index_symbol_ib, index_symbol=exchange_to_index_symbol(actions[0].stock_ex) 
            all_symbols= ib_symbols+[index_symbol_ib]
            it_is_indexes[index_symbol_ib]=True
            action=Action.objects.get(symbol=index_symbol)
            exchanges[index_symbol_ib]=action.stock_ex.ib_ticker    

        ok=False
        
        #test if the symbols were downloaded
        while not ok and len(ib_symbols)>=0:
            res=IBData.fetch(
                all_symbols, 
                period=period,
                missing_index='drop',
                timeframe="1 day", #see also interval_YF_to_ib
                exchanges=exchanges,
                it_is_indexes=it_is_indexes)
            ok=True
            o=res.get('Open')
            for s in ib_symbols:
                try:
                    o[s]
                except:
                    logger.info("symbol not found: "+s)
                    ok=False
                    ib_symbols.remove(s)
                    all_symbols.remove(s)

        return res,\
            ib_symbols,\
            index_symbol_ib
    except Exception as e:
         logger.error(e, stack_info=True, exc_info=True)
      

def retrieve_data_YF(
        actions: list,
        period: str,
        it_is_index: bool=False
        )-> (pd.core.frame.DataFrame, list, str):
    """
    Retrieve the data using YF

    YF can work with only the symbol to obtain the right contract

    Arguments
    ----------
        actions: list of products to be downloaded
        period: time period for which data should be downloaded
        it_is_index: is it indexes that are provided
    """
    #add the index to the list of stocks downloaded. Useful to make calculation on the index to determine trends
    #by downloading at the same time, we are sure the signals are aligned
    try:
        symbols=[a.symbol for a in actions]
        if it_is_index:
            index_symbol=symbols[0]
            all_symbols=symbols
        else:
            _, index_symbol=exchange_to_index_symbol(actions[0].stock_ex)  
            all_symbols=symbols+[index_symbol]
            
        ok=False
        first_round=True
        #look for anomaly
        if len(all_symbols)>2:
            res=vbt.YFData.fetch(all_symbols, period=period,missing_index='drop')
            avg=np.average(
                [len(vbt.YFData.fetch(all_symbols[0], period=period).get('Open')),
                len(vbt.YFData.fetch(all_symbols[1], period=period).get('Open')),
                len(vbt.YFData.fetch(all_symbols[-1], period=period).get('Open'))]
                )
                        
            if len(res.get('Open'))<avg-10:
                print("Anomaly found by downloading the symbols, check that the symbol with most nan is not delisted or if its introduction date is correct")
                logger.info("Anomaly found by downloading the symbols, check that the symbol with most nan is not delisted or if its introduction date is correct")
                res_nodrop=vbt.YFData.fetch(all_symbols, period=period)
                nb_nan={}
                for c in res.get('Open').columns:
                    nb_nan[c]=np.count_nonzero(np.isnan(res_nodrop.get('Open')[c]))

                nb_nan=sorted(nb_nan.items(), key=lambda tup: tup[1],reverse=True)
                print("Number of nan in each column: "+str(nb_nan))
        else:
            first_round=False
        
        #test if the symbols were downloaded
        while not ok and len(symbols)>=0:
            if not first_round:
                res=vbt.YFData.fetch(all_symbols, period=period,missing_index='drop')
            ok=True
            o=res.get('Open')
            
            for s in symbols:
                try:
                    o[s]
                except:
                    logger.info("symbol not found: "+s)
                    ok=False
                    symbols.remove(s)
                    all_symbols.remove(s)

        return res,\
               symbols,\
               index_symbol    
    except Exception as e:
         print(e)
         logger.error(e, stack_info=True, exc_info=True)

def retrieve_data(o,
                  actions: list,
                  period: str,
                  api_used: str="YF",
                  it_is_index: bool=False,
                  ) -> (bool, list):
    """
    Retrieve the data using IB or YF


    Arguments
    ----------
        o: object were to put the results
        actions: list of products to be downloaded
        period: time period for which data should be downloaded
        api_used: which API should be used to download data
        it_is_index: is it indexes that are provided
        
    """  
    if actions is None or len(actions)==0:
        raise ValueError("List of symbols empty, is there any stocks related to the requested stock exchange?")
    else:
        print("retrieve data")

        if api_used=="IB":
            try:
                cours, symbols, index_symbol=retrieve_data_ib(actions,period,it_is_index=it_is_index)
            except:
                logger.info("IB retrieval of symbol failed, fallback on YF")
                api_used="YF" #fallback
        if api_used=="YF":
            cours, symbols, index_symbol=retrieve_data_YF(actions,period,it_is_index=it_is_index)

        o.data=cours.select(symbols)
        o.data_ind=cours.select(index_symbol)
        
        for l in ["Close","Open","High","Low","Volume"]:
            setattr(o,l.lower(),o.data.get(l))
            setattr(o,l.lower()+"_ind",o.data_ind.get(l))
            
        logger.info("number of days retrieved: " + str(np.shape(o.close)[0]))
        if len(o.open_ind)==0 or len(o.open_ind)==0:
            raise ValueError("Retrieve data failed and returned empty Dataframe, check the symbols")

        return api_used, symbols
               
               
               