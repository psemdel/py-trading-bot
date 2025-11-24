#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat May 14 21:28:42 2022

@author: maxime
"""

import vectorbtpro as vbt
import math
import os
import numpy as np
from pathlib import Path

if __name__ != '__main__':
    from trading_bot.settings import BASE_DIR
    from core import constants

'''
This module contains the logic to retrieve data from file, or save it in files. 
It does not use Django and does not load modules needing Django.

To save data, just run this script (see at the bottom). It will generate 1 files: actions.h5. The main index (Nasdaq 100, Dow jones...) should be the last column by convention.
The idea behind it, is to determine in some strategies the trend using the index, and adapting the strategy depending on this trend.
'''

### Offline retrieval ###
def save_data_from_YF(
        selector: str,
        symbol_index: str, 
        stock_symbols: list, 
        start_date: str, 
        end_date: str        
        ):
    '''
    Prepare and save data to file for local usage. Use YF.

    Arguments
    ----------
       selector: for the naming of the file
       symbol_index: YF ticker of the index
       stock_symbols: list of YF tickers to be downloaded for the stocks
       start_date: start date for the download
       end_date: end date for the download
    '''
    symbols=stock_symbols+[symbol_index]
    data=vbt.YFData.pull(symbols,start=start_date,end=end_date,\
                            timeframe='1d')
    #knowing what we drop
    close=data.get("Close")

    for jj in range(len(close.columns)):
        for ii in range(len(close[close.columns[jj]])):
            if math.isnan(close[close.columns[jj]].values[ii]):
                print("dropping at least " + str(close.index[ii]) + " column: "+ str(close.columns[jj]))
    for ii in range(len(close[close.columns[-1]])):
        if math.isnan(close[close.columns[-1]].values[ii]):
            print("dropping at least " + str(close.index[ii]))
            
            
    data=vbt.YFData.pull(symbols,start=start_date,end=end_date,\
                                 timeframe='1d',missing_index="drop")   

    BASE_DIR = Path(__file__).resolve().parent.parent
    data.to_hdf(path_or_buf=os.path.join(BASE_DIR,'saved_cours/'+selector.upper()+'_period.h5'))

def retrieve_data_offline(
             o, 
             symbol_index: str, 
             period: str):
    '''
    Read local data

    Arguments
    ----------
       o: object where to put the data
       symbol_index: YF ticker of the index
       period: period in which we want to have the data
    '''
    data_all=vbt.HDFData.pull(os.path.join(BASE_DIR,'saved_cours/'+symbol_index+'_' + period+'.h5'))
    retrieve_data_sub(o, data_all)

### Online retrieval for backtesting purpose, it is downloaded everytime then
def retrieve_data_live(
        o,
        stock_symbols: list,
        symbol_index: str,
        period: str,
        it_is_index: bool=False,
        source: str="YF"
        ):
    '''
    To plot the last days for instance
    Different from retrieve_data in strat as it needs to work outside of Django
    
    Arguments
    ----------
       o: object where to put the data
       stock_symbols: list of YF or IB tickers to be downloaded for the stocks
       symbol_index: YF or IB ticker of the index
       period: period in which we want to have the data
       it_is_index: is it indexes that are provided
    '''
    
    symbols=stock_symbols+[symbol_index]
    data_all=vbt.YFData.pull(symbols, period=period,missing_index='drop')
    retrieve_data_sub(o, data_all, it_is_index=it_is_index)

def retrieve_data_sub(
        o,
        data_all,
        it_is_index: bool=False
        ):
    '''
    Sub function to retrieve data

    Arguments
    ----------
        o: object where to put the data
        data_all : all data, stocks and index
        it_is_index: is it indexes that are provided
    '''
    cols=list(data_all.get("Open").columns)
    o.data=data_all.select_symbols(cols[:-1]) #all columns except last one
    o.data_ind=data_all.select_symbols(cols[-1]) #only last column
    
    for l in ["Close","Open","High","Low","Volume"]:
        setattr(o,l.lower(),o.data.get(l))
        setattr(o,l.lower()+"_ind",o.data_ind.get(l))
    
    print("number of days retrieved: " + str(np.shape(o.close)[0]))
    
    #If we want to optimize underlying strategies implying the main index
    if it_is_index:
        for l in ["close","open","high","low","volume","data"]:
            setattr(o,l,getattr(o,l+"_ind"))    

def retrieve_from_YF_debug(
        stock_symbols: list,
        symbol_index: str,
        period: str,
        it_is_index: bool=False
        ):
    '''
    To find which stock was delisted, from YF
    
    Arguments
    ----------
       stock_symbols: list of YF tickers to be downloaded for the stocks
       symbol_index: YF ticker of the index
       period: period in which we want to have the data
       it_is_index: is it indexes that are provided
    '''    
    symbols=stock_symbols+[symbol_index]
    data_all=vbt.YFData.pull(symbols, period=period)

    nb_nan={}
    for c in data_all.get('Open').columns:
        nb_nan[c]=np.count_nonzero(np.isnan(data_all.get('Open')[c]))
        
    nb_nan=sorted(nb_nan.items(), key=lambda tup: tup[1],reverse=True)
    print("Number of nan in each column: "+str(int(nb_nan)))

if __name__ == '__main__':
    '''
    Write a file actions.h5
    
    You can download anything using
    
    all_symbols=["YF_ticker1","YF_ticker2"]
    index="YF_ticker3"
    '''
    import constants
    
    selector="CAC40"
    start_date='2020-01-01'
    end_date='2025-11-02'
    
    if selector=="CAC40":
        all_symbols=constants.CAC40
        index="^FCHI"
    elif selector=="NASDAQ":
        all_symbols=constants.NASDAQ
        index="^IXIC"
    elif selector=="DAX":
        all_symbols=constants.DAX
        index="^GDAXI" 
    elif selector=="NYSE": #too big!
        all_symbols=constants.NYSE
        index="^DJI"
    elif selector=="Brent":
        all_symbols=["BZ=F"]
        index="BZ=F"
    elif selector in ["realestate","industry","it","com","staples","consumer","energy","utilities",
                      "fin","healthcare","materials"]:
        index="^DJI"
        if selector=="realestate":
            all_symbols=constants.REALESTATE
        elif selector=="industry":
            all_symbols=constants.INDUSTRY
        elif selector=="it":
            all_symbols=constants.IT
        elif selector=="com":
            all_symbols=constants.COM
        elif selector=="staples":
            all_symbols=constants.STAPLES
        elif selector=="consumer":
            all_symbols=constants.CONSUMER
        elif selector=="energy":
            all_symbols=constants.ENERGY
        elif selector=="utilities":
            all_symbols=constants.UTILITIES
        elif selector=="fin":
            all_symbols=constants.FIN
        elif selector=="healthcare":
            all_symbols=constants.HEALTHCARE
        elif selector=="materials":
            all_symbols=constants.MATERIALS

    new_list=[]
    for s in all_symbols:
        ok=True
        if s in constants.DELIST:
            if constants.DELIST[s]<end_date:
                ok=False
            
        if s in constants.INTRO: #cannot rely on the database, as django is not running at this point.
            if constants.INTRO[s]>start_date:
                ok=False
                
        if ok:
            new_list.append(s)

    save_data_from_YF(selector,index,new_list, start_date, end_date)

