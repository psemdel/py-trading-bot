#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jun  4 13:05:41 2022

@author: maxime
"""
import vectorbtpro as vbt
import core.indicators as ic

from core.strat import Strat
from core.bt import BT, WQ
import numpy as np
import pandas as pd

### To back stage recent data
# As strat but adapted to download every time the data
class StratLIVE(Strat):
    def __init__(self,symbols,period,index_symbol,**kwargs):
        self.period=period
        self.symbols=symbols
        self.index_symbol=index_symbol
        self.retrieve_live()
        
        if kwargs.get("index",False):
            #self.only_index=True
            self.close=self.close_ind
            self.open=self.open_ind
            self.low=self.low_ind
            self.high=self.high_ind
        
    ##to plot the last days for instance
    def retrieve_live(self):
        all_symbols=self.symbols+[self.index_symbol]
        
        cours=vbt.YFData.fetch(all_symbols, period=self.period,missing_index='drop')
        cours_action=cours.select(self.symbols)
        self.open =cours_action.get('Open')
        self.high=cours_action.get('High')
        self.low=cours_action.get('Low')
        self.close=cours_action.get('Close')
        self.volume=cours_action.get('Volume')
        print("number of days retrieved: " + str(np.shape(self.close)[0]))
        
        #assuming all actions in the same exchange here:
        #cours_ind=vbt.YFData.fetch(index_symbol, period=period,missing_index='drop',**kwargs)
        cours_index=cours.select(self.index_symbol)
        self.open_ind =cours_index.get('Open')
        self.high_ind=cours_index.get('High')
        self.low_ind=cours_index.get('Low')
        self.close_ind=cours_index.get('Close')
        self.volume_ind=cours_index.get('Volume')

#Same as bt but for recent data
class btLIVE(BT):
    def __init__(self,longshort,**kwargs):
        st=kwargs.get("st")
        
        self.high=st.high
        self.low=st.low
        self.close=st.close
        self.open=st.open
        self.volume=st.volume
        self.high_ind=st.high_ind
        self.low_ind=st.low_ind
        self.close_ind=st.close_ind
        self.open_ind=st.open_ind
        self.volume_ind=st.volume_ind
        
        self.symbols=self.close.columns.values
    
        self.start_capital=10000
        self.order_size=self.start_capital
        self.capital=self.start_capital
     
        self.longshort=longshort
     
        self.entries=pd.DataFrame.vbt.empty_like(self.close, fill_value=False)
        self.exits=pd.DataFrame.vbt.empty_like(self.close, fill_value=False)
     
        self.exits_short=pd.DataFrame.vbt.empty_like(self.close, fill_value=False)
        self.entries_short=pd.DataFrame.vbt.empty_like(self.close, fill_value=False)
     
        self.pf=[]
        self.pf_short=[]
        
        st.strat_kama_stoch_matrend_bbands()
        
        self.ent11=st.entries
        self.ex11=st.exits
 
        self.vol=ic.VBTNATR.run(self.high,self.low,self.close).natr
    
        self.excluded=[]
        self.hold_dur=0
         
        self.candidates=[[] for ii in range(len(self.close))]
        self.candidates_short=[[] for ii in range(len(self.close))]
         
        self.symbols_simple=self.close.columns.values
        self.symbols_complex=self.ent11.columns.values
         
        self.last_order_dir="long"    
        
#Same as WQ but for recent data        
class WQLIVE(WQ):
    def __init__(self, nb,**kwargs):
        st=kwargs.get("st")
        
        self.high=st.high
        self.low=st.low
        self.close=st.close
        self.open=st.open
        self.volume=st.volume
        self.high_ind=st.high_ind
        self.low_ind=st.low_ind
        self.close_ind=st.close_ind
        self.open_ind=st.open_ind
        self.volume_ind=st.volume_ind        
        
        self.candidates=[[] for ii in range(len(self.close))]
        self.pf=[]
        
        self.entries=pd.DataFrame.vbt.empty_like(self.close, fill_value=False)
        self.exits=pd.DataFrame.vbt.empty_like(self.close, fill_value=False)
        
        #actually only long are used in those strategy
        self.exits_short=pd.DataFrame.vbt.empty_like(self.close, fill_value=False)
        self.entries_short=pd.DataFrame.vbt.empty_like(self.close, fill_value=False)

        self.start_capital=10000
        self.order_size=self.start_capital
        self.capital=self.start_capital
        
        self.symbols_simple=self.close.columns.values
        
        self.nb=nb
        self.out = vbt.wqa101(self.nb).run(open=self.open, high=self.high,\
                                      low=self.low, close=self.close,volume=self.volume).out       