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
from core import common, constants
import numpy as np
import pandas as pd

### To back stage recent data
#Need to be called outside of Django!!!
# As strat but adapted to download every time the data
class StratLIVE(Strat):
    def __init__(self,symbols,period,index_symbol,**kwargs):
        self.period=period
        self.symbols=symbols
        self.index_symbol=index_symbol
        self.retrieve_live()
        
        if kwargs.get("index",False):
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
#Only import with strat supported
class btLIVE(BT):
    def __init__(self,longshort,**kwargs):
        st=kwargs.get("st")
        self.st=st
        
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

#Allow you to evaluate how performed preselection strategies on past period finishing today, so in a close past
def scan_presel_all(period,**kwargs):
    d={"CAC40":{"symbols":constants.CAC40,"index":"^FCHI"},
       "DAX":  {"symbols":constants.DAX,"index":"^GDAXI"},
       "NASDAQ":  {"symbols":constants.NASDAQ,"index":"^IXIC"},
       "REALESTATE": {"symbols":constants.REALESTATE, "index":"^DJI"},
       "INDUSTRY": {"symbols":constants.INDUSTRY, "index":"^DJI"},
       "IT": {"symbols":constants.IT, "index":"^DJI"},
       "COM": {"symbols":constants.COM, "index":"^DJI"},
       "STAPLES": {"symbols":constants.STAPLES, "index":"^DJI"},
       "CONSUMER": {"symbols":constants.CONSUMER, "index":"^DJI"},
       "ENERGY": {"symbols":constants.ENERGY, "index":"^DJI"},
       "UTILITIES": {"symbols":constants.UTILITIES, "index":"^DJI"},
       "FIN": {"symbols":constants.FIN, "index":"^DJI"},
       "MATERIALS": {"symbols":constants.MATERIALS, "index":"^DJI"},
    }
    presel_dic=["vol","realmadrid","retard","retard_macro","divergence","divergence_blocked",7,31,53,54]
    res={}
    
    for k, v in d.items():
        symbols=common.filter_intro(v["symbols"],period)
        st=StratLIVE(symbols,str(period)+"y",v["index"])
        res=scan_presel(presel_dic, k,res=res,st=st,**kwargs)
        
    return res

def scan_presel(presel_dic, key,**kwargs):
    res=kwargs.get('res',{})
    res[key]={}
    st=kwargs.get("st")
    fees=kwargs.get("fees",0)
    #limit the range for the calculation of the return to x market days, 
    #set your period to be significantly longer than the restriction to avoid calculation errors
    restriction=kwargs.get("restriction",None) 
    
    for p in presel_dic:
        bti=btLIVE("long",st=st) #has to be recalculated everytime, otherwise it caches
        if p=="vol":
            bti.preselect_vol()
        elif p=="retard":
            bti.preselect_retard()
        elif p=="macd_vol":
            bti.preselect_macd_vol()
        elif p=="hist_vol":
            bti.preselect_hist_vol()
        elif p=="divergence":
            bti.preselect_divergence()
        elif p=="macd_vol_macro":
            bti.preselect_macd_vol_macro()
        elif p=="retard_macro":
            bti.preselect_retard_macro()
        elif p=="divergence_blocked":
            bti.preselect_divergence_blocked()
        elif p=="macd_vol_slow":
            bti.preselect_macd_vol_slow()
        elif p=="realmadrid":
            bti.preselect_realmadrid()
        elif p=="macd_vol_slow":
            bti.preselect_macd_vol_slow()
        elif p=="hist_vol_slow":
            bti.preselect_hist_vol_slow() 
        elif type(p)==int:
            bti=WQLIVE(p,st=st)
            bti.def_cand()
            bti.calculate(nostrat11=True)
            
        if restriction is not None and type(restriction)==int:
            pf=vbt.Portfolio.from_signals(bti.close[-restriction:], 
                                          bti.entries[-restriction:],
                                          bti.exits[-restriction:],
                                          short_entries=bti.entries_short[-restriction:],
                                          short_exits  =bti.exits_short[-restriction:],
                                          freq="1d",
                                          call_seq='auto',
                                          cash_sharing=True,
                                          fees=fees
                                 )            
        else:
            pf=vbt.Portfolio.from_signals(bti.close, 
                                          bti.entries,
                                          bti.exits,
                                          short_entries=bti.entries_short,
                                          short_exits  =bti.exits_short,
                                          freq="1d",
                                          call_seq='auto',
                                          cash_sharing=True,
                                          fees=fees
                                 )
        res[key][p]=pf.get_total_return()
    return res
        
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