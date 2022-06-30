#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat May 14 21:28:42 2022

@author: maxime
"""

import vectorbtpro as vbt
import math

from core import constants
#import constants #when started directly here.
#

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
                print("dropping at least " + str(close.index[ii]) + " column: "+ str(jj))
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
    data=vbt.HDFData.fetch('saved_cours/'+index+'_' + period+'.h5')
    
    close=data.get("Close")
    open_=data.get("Open")
    high=data.get("High")
    low=data.get("Low")
    volume=data.get("Volume")
      
    if index=="CAC40":
        ind_sym="FCHI"
    elif index=="DAX":
        ind_sym="GDAXI"
    else:
        ind_sym="IXIC"

    data=vbt.HDFData.fetch('saved_cours/'+ind_sym+'_' + period+'.h5')
    close_ind=data.get("Close")
    open_ind=data.get("Open")
    high_ind=data.get("High")
    low_ind=data.get("Low")
    volume_ind=data.get("Volume")
    
    return high, low, close, open_, volume, high_ind, low_ind, close_ind, open_ind, volume_ind

if __name__ == '__main__':

    if False:
        all_symbols=constants.cac40() 
        all_symbols.remove("LR.PA")
        all_symbols.remove("WLN.PA")
        all_symbols.remove("ACA.PA")
        all_symbols.remove("SW.PA")
        #all_symbols.remove("STLA.PA")
        index="^FCHI"
    elif True:
        all_symbols=constants.nasdaq()
        #all_symbols.remove("XLNX")
        all_symbols.remove("ZS")
        #all_symbols.remove("ABNB")
        all_symbols.remove("CHTR")
        #all_symbols.remove("CRWD")
        #all_symbols.remove("DDOG")
        all_symbols.remove("DOCU")
        all_symbols.remove("FB")
        all_symbols.remove("FTNT")
        all_symbols.remove("JD")  
        all_symbols.remove("KDP")
        all_symbols.remove("KHC")
        #all_symbols.remove("LCID")        
        all_symbols.remove("LULU")
        all_symbols.remove("MELI")
        all_symbols.remove("MRNA")        
        all_symbols.remove("NXPI")        
        all_symbols.remove("OKTA")
        all_symbols.remove("PANW")
        all_symbols.remove("PDD")   
        #all_symbols.remove("PTON")        
        all_symbols.remove("PYPL")
        all_symbols.remove("SPLK")
        all_symbols.remove("TEAM")       
        all_symbols.remove("TMUS")        
        all_symbols.remove("TSLA")
        all_symbols.remove("VRSK")
        all_symbols.remove("WDAY")       
        #all_symbols.remove("ZM")
        all_symbols.remove("AVGO")
        index="^IXIC"
    elif False:
        all_symbols=constants.dax()
        all_symbols.remove("LIN.DE")
        all_symbols.remove("DHER.DE")
        all_symbols.remove("HFG.DE")
        all_symbols.remove("1COV.DE")
        all_symbols.remove("SHL.DE")
        #all_symbols.remove("ENR.DE")
        all_symbols.remove("ZAL.DE")
        all_symbols.remove("PAH3.DE")
        all_symbols.remove("BNR.DE")
        index="^GDAXI"        

    total_symbols=all_symbols+[index]
    
    start_date='2007-01-01'
    end_date='2022-06-30'
    
    save_data(total_symbols,index,all_symbols, start_date, end_date)