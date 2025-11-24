#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat May 14 21:28:42 2022

@author: maxime
"""

import vectorbtpro as vbt
import numpy as np
import pandas as pd

import os

from orders.models import Action, period_YF_to_ib, interval_YF_to_ib, exchange_to_index_symbol, check_ib_permission
from orders.ib import connect_ib, IBData
from trading_bot.settings import _settings, BASE_DIR

import warnings
import logging
logger = logging.getLogger(__name__)
logger_trade = logging.getLogger('trade')

'''
This file contains the logic to retrieve data from online source.

Note: this file is better separated from data_manager, as the Django needs to be loaded for online downloads.

To save data, just run this script (see at the bottom). It will generate 2 files: actions.h5 and index.h5. In the first, all prices for the actions is listed, in 
the second, the price of the main index (Nasdaq 100, Dow jones...) is listed. Their generation simulteneously ensures their alignment.
The idea behind it, is to determine in some strategies the trend using the index, and adapting the strategy depending on this trend.
'''

### Online retrieval ###
def retrieve_data_online(o,
                  actions: list,
                  period: str=None,
                  it_is_index: bool=False,
                  used_api_key:str="reporting",
                  save:bool=False,
                  start: str=None,
                  end: str=None,
                  file_name: str="NAME"
                  ) -> (bool, list):
    """
    Retrieve the data using any API
    The main index of the stock exchange related to the actions is added automatically

    Arguments
    ----------
        o: object were to put the results
        actions: list of products to be downloaded
        period: time period for which data should be downloaded
        api_used_key:  key in _settings["USED API"] to be modified / checked
        it_is_index: is it indexes that are provided
        save: should the downloaded data be saved locally
        start: start date for the data
        end: end date for the data        
    """  
    if actions is None or len(actions)==0:
        raise ValueError("List of symbols empty, is there any stocks related to the requested stock exchange?")
    else:
        try:
            print("retrieve data")
            if _settings["USED_API"][used_api_key]=="":
                check_ib_permission([a.symbol for a in actions])
    
            data=None
            used_api=_settings["USED_API"][used_api_key] #lighten the writting
            
            if used_api == "IB":
                try:
                    data, symbols, index_symbol, symbols_to_YF=retrieve_data_ib(
                        actions,
                        period=period,
                        it_is_index=it_is_index,
                        start=start,
                        end=end)
                except Exception as e:
                    logger.error(e, stack_info=True, exc_info=True)
            elif used_api in ["CCXT","MT5","TS"]:
                try:
                    data, symbols, index_symbol, symbols_to_YF=retrieve_data_notIB(
                        used_api,
                        actions,
                        period=period,
                        it_is_index=it_is_index,
                        start=start,
                        end=end)
                except Exception as e:
                    logger.error(e, stack_info=True, exc_info=True)
            #separated as could be used for fallback
            if used_api=="YF":
                data, symbols, index_symbol=retrieve_data_notIB(
                    "YF",
                    actions,
                    period=period,
                    it_is_index=it_is_index,
                    start=start,
                    end=end)
            _settings["USED_API"][used_api_key]=used_api #save potential change

            if save:
                data.to_hdf(path_or_buf=os.path.join(BASE_DIR,'saved_cours/'+file_name.upper()+'_period.h5'))
    
            if data is None:
                return None
            else:
                o.data=data.select_symbols(symbols)
                o.data_ind=data.select_symbols(index_symbol)
                
                for l in ["Close","Open","High","Low","Volume"]:
                    setattr(o,l.lower(),o.data.get(l))
                    setattr(o,l.lower()+"_ind",o.data_ind.get(l))
                    
                logger.info("number of days retrieved: " + str(np.shape(o.close)[0]))
                if len(o.open_ind)==0 or len(o.open_ind)==0:
                    raise Exception("Retrieve data failed and returned empty Dataframe, check the tickers, tickers: " +str(symbols) + ", index ticker: " + str(index_symbol))
        
                return symbols, symbols_to_YF #can be IB or YF symbols
        except Exception as e:
            logger.error(e, stack_info=True, exc_info=True)
            return None
        
@connect_ib 
def retrieve_data_ib(
        actions: list,
        period: str,
        it_is_index: bool=False,
        start: str=None,
        end: str='',
        timeframe: str="1 day",
        **kwargs
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
        start: start date for the data -> not supported
        end: end date for the data    
        timeframe: interval of time between each sample
    """   
    try:
        if start is not None:
            warnings.warn("Start is not supported by retrieve_data_ib, use period!")
        
        period=period_YF_to_ib(period)
        timeframe=interval_YF_to_ib(timeframe)
        exchanges={}
        it_is_indexes={}
        currencies={}
        ib_symbols=[]
        symbols_to_YF={}
        
        for a in actions:
            ib_symbol=a.ib_ticker()
            ib_symbols.append(ib_symbol)
            exchanges[ib_symbol]=a.stock_ex.ib_ticker
            it_is_indexes[ib_symbol]=it_is_index
            currencies[ib_symbol]=a.currency.symbol
            symbols_to_YF[ib_symbol]=a.symbol
        
        #add the index to the list of stocks downloaded. Useful to make calculation on the index to determine trends
        #by downloading at the same time, we are sure the signals are aligned
        
        if it_is_index:
            index_symbol=ib_symbols[0]
            all_symbols=ib_symbols
            index_symbol_ib=index_symbol
        else:
            index_symbol_ib, index_symbol=exchange_to_index_symbol(actions[0].stock_ex) 
            all_symbols= ib_symbols+[index_symbol_ib]
            it_is_indexes[index_symbol_ib]=True
            action=Action.objects.get(symbol=index_symbol)
            exchanges[index_symbol_ib]=action.stock_ex.ib_ticker  
            
        ok=False
        #test if the symbols were downloaded
        while not ok and len(ib_symbols)>=0:
            print("data pull")
            data=IBData.pull(
                all_symbols, 
                period=period,
                missing_index='drop',
                timeframe=timeframe,
                end=end,
                exchanges=exchanges,
                it_is_indexes=it_is_indexes,
                currencies=currencies)
            ok=True
            o=data.get('Open')
            for s in ib_symbols:
                try:
                    o[s]
                except:
                    logger.info("symbol not found: "+s)
                    ok=False
                    ib_symbols.remove(s)
                    all_symbols.remove(s)

        return data,\
            ib_symbols,\
            index_symbol_ib,\
            symbols_to_YF
    except Exception as e:
         logger.error(e, stack_info=True, exc_info=True)

def retrieve_data_notIB(
        used_api: str,
        actions: list,
        period: str,
        it_is_index: bool=False,
        start: str=None,
        end: str=None,
        timeframe: str="1 day",
        )-> (pd.core.frame.DataFrame, list, str):
    """
    Retrieve the data using YF

    YF can work with only the symbol to obtain the right contract

    Arguments
    ----------
        actions: list of products to be downloaded
        period: time period for which data should be downloaded
        it_is_index: is it indexes that are provided
        start: start date for the data -> not supported
        end: end date for the data  
        timeframe: interval of time between each sample
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
        symbols_to_YF={}
        
        for s in symbols:
            symbols_to_YF[s]=s
        
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
            data=f.pull(
                all_symbols, 
                period=period,
                missing_index='drop',
                start=start,
                end=end,                
                timeframe=timeframe
                )
            #we do the following supplementary download only on a sample of stocks as it is time consuming
            avg=np.average(
                [len(f.fetch(all_symbols[0], period=period).get('Open')),
                len(f.fetch(all_symbols[1], period=period).get('Open')),
                len(f.fetch(all_symbols[-1], period=period).get('Open'))]
                )
                        
            if len(data.get('Open'))<avg-10:
                print("Anomaly found by downloading the symbols, check that the symbol with most nan is not delisted or if its introduction date is correct")
                logger.info("Anomaly found by downloading the symbols, check that the symbol with most nan is not delisted or if its introduction date is correct")
                res_nodrop=f.fetch(all_symbols, period=period)
                nb_nan={}
                for c in res_nodrop.get('Open').columns:
                    nb_nan[c]=np.count_nonzero(np.isnan(res_nodrop.get('Open')[c]))

                nb_nan=sorted(nb_nan.items(), key=lambda tup: tup[1],reverse=True)
                print("Number of nan in each column: "+str(nb_nan))
        else:
            first_round=False
        
        #test if the symbols were downloaded
        while not ok and len(symbols)>=0:
            if not first_round:
                data=f.fetch(all_symbols, period=period,missing_index='drop')
            ok=True
            o=data.get('Open')
            
            for s in symbols:
                try:
                    o[s]
                except:
                    logger.info("symbol not found: "+s)
                    ok=False
                    symbols.remove(s)
                    all_symbols.remove(s)

        return data,\
               symbols,\
               index_symbol,\
               symbols_to_YF
    except Exception as e:
         print(e)
         logger.error(e, stack_info=True, exc_info=True)
