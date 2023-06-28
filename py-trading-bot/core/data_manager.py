#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat May 14 21:28:42 2022

@author: maxime
"""

import vectorbtpro as vbt
import math
import os

if __name__ != '__main__':
    from trading_bot.settings import BASE_DIR
    from core import constants

def save_data(
        symbols: list, 
        index: str, 
        stock_symbols: list, 
        start_date: str, 
        end_date: str):
    '''
    Prepare and save data for local usage

    Arguments
    ----------
       symbols: list of all YF tickers to be downloaded (see comment below for the reason)
       index: YF ticker of the index
       action_symbols: list of YF tickers to be downloaded for the stocks
       start_date: start date for the download
       end_date: end date for the download
    '''
    #Everything is downloaded together to use missing_index function
    data=vbt.YFData.fetch(symbols,start=start_date,end=end_date,\
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
            
    #print(close.columns[7])            
    data=vbt.YFData.fetch(symbols,start=start_date,end=end_date,\
                                 timeframe='1d',missing_index="drop")    
    
    #splitting index from the other actions
    data_ind=data.select(index)
    data_ind.to_hdf(file_path="index.h5")
    
    data_others=data.select(stock_symbols)
    data_others.to_hdf(file_path="actions.h5")

def retrieve(o, 
             index: str, 
             period: str):
    '''
    Read local data

    Arguments
    ----------
       o: object where to put the data
       index: YF ticker of the index
       period: period in which we want to have the data

    '''
    if index=="CAC40":
        ind_sym="FCHI"
    elif index=="DAX":
        ind_sym="GDAXI"
    elif index=="NASDAQ":
        ind_sym="IXIC"
    elif index=="Brent":
        ind_sym="Brent"
    else:
        ind_sym="DJI"
        
    o.data=vbt.HDFData.fetch(os.path.join(BASE_DIR,'saved_cours/'+index+'_' + period+'.h5'))
    o.data_ind=vbt.HDFData.fetch(os.path.join(BASE_DIR,'saved_cours/'+ind_sym+'_' + period+'.h5'))
    for l in ["Close","Open","High","Low","Volume"]:
        setattr(o,l.lower(),o.data.get(l))
        setattr(o,l.lower()+"_ind",o.data_ind.get(l))

if __name__ == '__main__':
    '''
    Write a file actions.h5 with the content of "all_symbols" and a file index.h5 with the content of "index"
    
    You can download anything using
    
    all_symbols=["YF_ticker1","YF_ticker2"]
    index="YF_ticker3"
    '''
    import constants
    
    selector="CAC40"
    start_date='2007-01-01'
    end_date='2023-01-01'
    
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
        if s in constants.INTRO: #cannot rely on the database, as django is not running at this point.
            if constants.INTRO[s]<start_date:
                new_list.append(s)
        else:
            new_list.append(s)
                
    total_symbols=new_list+[index]
    save_data(total_symbols,index,all_symbols, start_date, end_date)