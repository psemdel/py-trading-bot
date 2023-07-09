#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat May 14 21:28:42 2022

@author: maxime
"""

import vectorbtpro as vbt
import numpy as np
import pandas as pd
import sys

from orders.models import Action, period_YF_to_ib, exchange_to_index_symbol, check_ib_permission
from orders.ib import connect_ib, IBData
from trading_bot.settings import _settings

import logging
logger = logging.getLogger(__name__)
logger_trade = logging.getLogger('trade')

'''
This file contains the logic to retrieve data online

To save data, just run this script (see at the bottom). It will generate 2 files: actions.h5 and index.h5. In the first, all prices for the actions is listed, in 
the second, the price of the main index (Nasdaq 100, Dow jones...) is listed. Their generation simulteneously ensures their alignment.
The idea behind it, is to determine in some strategies the trend using the index, and adapting the strategy depending on this trend.
'''

### Online retrieval ###
def retrieve_data_online(o,
                  actions: list,
                  period: str,
                  it_is_index: bool=False,
                  used_api_key:str="reporting",
                  ) -> (bool, list):
    """
    Retrieve the data using any API

    Arguments
    ----------
        o: object were to put the results
        actions: list of products to be downloaded
        period: time period for which data should be downloaded
        api_used_key:  key in _settings["USED API"] to be modified / checked
        it_is_index: is it indexes that are provided
        
    """  
    if actions is None or len(actions)==0:
        raise ValueError("List of symbols empty, is there any stocks related to the requested stock exchange?")
    else:
        print("retrieve data")
        if _settings["USED_API"][used_api_key]=="":
            check_ib_permission([a.symbol for a in actions])

        used_api=_settings["USED_API"][used_api_key] #lighten the writting
        if used_api == "IB":
            try:
                cours, symbols, index_symbol=retrieve_data_ib(used_api,actions,period,it_is_index=it_is_index)
            except:
                logger.info("IB retrieval of symbol failed, fallback on YF")
                used_api="YF" #fallback            
        elif used_api in ["CCXT","MT5","TS"]:
            try:
                cours, symbols, index_symbol=retrieve_data_notIB(used_api,actions,period,it_is_index=it_is_index)
            except:
                logger.info("IB retrieval of symbol failed, fallback on YF")
                used_api="YF" #fallback
        if used_api=="YF":
            cours, symbols, index_symbol=retrieve_data_notIB("YF",actions,period,it_is_index=it_is_index)
        _settings["USED_API"][used_api_key]=used_api #save potential change

        o.data=cours.select(symbols)
        o.data_ind=cours.select(index_symbol)
        
        for l in ["Close","Open","High","Low","Volume"]:
            setattr(o,l.lower(),o.data.get(l))
            setattr(o,l.lower()+"_ind",o.data_ind.get(l))
            
        logger.info("number of days retrieved: " + str(np.shape(o.close)[0]))
        if len(o.open_ind)==0 or len(o.open_ind)==0:
            raise ValueError("Retrieve data failed and returned empty Dataframe, check the symbols")

        return symbols

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

def retrieve_data_notIB(
        used_api: str,
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
        used_api_to_class={
            "YF":"YFData",
            "CCXT":"CCXTData",
            "MT5":"MT5Data",
            "TS":"TradeStationData"
            }
        f=getattr(vbt,used_api_to_class[used_api])
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
            res=f.fetch(all_symbols, period=period,missing_index='drop')
            avg=np.average(
                [len(f.fetch(all_symbols[0], period=period).get('Open')),
                len(f.fetch(all_symbols[1], period=period).get('Open')),
                len(f.fetch(all_symbols[-1], period=period).get('Open'))]
                )
                        
            if len(res.get('Open'))<avg-10:
                print("Anomaly found by downloading the symbols, check that the symbol with most nan is not delisted or if its introduction date is correct")
                logger.info("Anomaly found by downloading the symbols, check that the symbol with most nan is not delisted or if its introduction date is correct")
                res_nodrop=f.fetch(all_symbols, period=period)
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
                res=f.fetch(all_symbols, period=period,missing_index='drop')
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
