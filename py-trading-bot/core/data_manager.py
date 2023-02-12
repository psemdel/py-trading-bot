#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat May 14 21:28:42 2022

@author: maxime
"""

import vectorbtpro as vbt
import math
from trading_bot.settings import BASE_DIR
import os

if __name__ != '__main__':
    from core import constants

###Prepare and save data for local usage
def save_data(symbols, index, action_symbols, start_date, end_date):
    
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
    data_index=data.select(index)
    data_index.to_hdf(file_path="index.h5")
    
    data_others=data.select(action_symbols)
    data_others.to_hdf(file_path="actions.h5")

### Read local data
def retrieve(index, period):
    data=vbt.HDFData.fetch(os.path.join(BASE_DIR,'saved_cours/'+index+'_' + period+'.h5'))
    
    close=data.get("Close")
    open_=data.get("Open")
    high=data.get("High")
    low=data.get("Low")
    volume=data.get("Volume")
      
    if index=="CAC40":
        ind_sym="FCHI"
    elif index=="DAX":
        ind_sym="GDAXI"
    elif index=="NASDAQ":
        ind_sym="IXIC"
    else:
        ind_sym="DJI"

    data=vbt.HDFData.fetch(os.path.join(BASE_DIR,'saved_cours/'+ind_sym+'_' + period+'.h5'))
    close_ind=data.get("Close")
    open_ind=data.get("Open")
    high_ind=data.get("High")
    low_ind=data.get("Low")
    volume_ind=data.get("Volume")
    
    return high, low, close, open_, volume, high_ind, low_ind, close_ind, open_ind, volume_ind

if __name__ == '__main__':
    import constants
    
    selector="materials"
    start_date='2007-01-01'
    end_date='2022-08-30'
    
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