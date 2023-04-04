#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jun  4 13:05:41 2022

@author: maxime
"""
import vectorbtpro as vbt
import core.indicators as ic

from core.strat import Strat
from core.presel import Presel, WQ
from core import common, constants
from core.common import copy_attr
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
            for l in ["close","open","high","low","volume","data"]:
                setattr(self,l,getattr(self,l+"_ind"))
        
    ##to plot the last days for instance
    def retrieve_live(self):
        all_symbols=self.symbols+[self.index_symbol]
        
        cours=vbt.YFData.fetch(all_symbols, period=self.period,missing_index='drop')
        self.data=cours.select(self.symbols)
        self.data_ind=cours.select(self.index_symbol)
        for l in ["Close","Open","High","Low","Volume"]:
            setattr(self,l.lower(),self.data.get(l))
            setattr(self,l.lower()+"_ind",self.data_ind.get(l))
        
        print("number of days retrieved: " + str(np.shape(self.close)[0]))

def scan_strat(strat_dic, key,**kwargs):
    res=kwargs.get('res',{})
    res[key]={}
    st=kwargs.get("st")
    fees=kwargs.get("fees",0)
    #limit the range for the calculation of the return to x market days, 
    #set your period to be significantly longer than the restriction to avoid calculation errors
    restriction=kwargs.get("restriction",None) 
    
    for p in strat_dic:
        getattr(st,p)()
        if restriction is not None and type(restriction)==int:
            pf=vbt.Portfolio.from_signals(st.close[-restriction:], 
                                          st.entries[-restriction:],
                                          st.exits[-restriction:],
                                          short_entries=st.entries_short[-restriction:],
                                          short_exits  =st.exits_short[-restriction:],
                                          freq="1d",
                                          call_seq='auto',
                                          fees=fees
                                 )            
        else:
            pf=vbt.Portfolio.from_signals(st.close, 
                                          st.entries,
                                          st.exits,
                                          short_entries=st.entries_short,
                                          short_exits  =st.exits_short,
                                          freq="1d",
                                          call_seq='auto',
                                          cash_sharing=True,
                                          fees=fees
                                 )
    res[key][p]=pf.get_total_return()
    return res        

#Same as bt but for recent data
#Only import with strat supported
class PreselLIVE(Presel):
    def __init__(self,**kwargs):
        st=kwargs.get("st")
        self.st=st
        copy_attr(self,st)
        
        self.symbols=self.close.columns.values
    
        self.start_capital=10000
        self.order_size=self.start_capital
        self.capital=self.start_capital
     
        self.longshort=kwargs.get("longshort","long")
     
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
        symbols=common.filter_intro_symbol(v["symbols"],period)
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
        bti=PreselLIVE("long",st=st) #has to be recalculated everytime, otherwise it caches
        if type(p)==int:
            bti=WQLIVE(p,st=st)
            bti.def_cand()
            bti.calculate(nostrat11=True)
        else:
            getattr(bti,"preselect_"+p)()
            
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
        copy_attr(self,st)

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