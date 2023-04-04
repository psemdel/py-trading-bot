#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat May 14 22:36:16 2022

@author: maxime
"""
import vectorbtpro as vbt
from core.macro import VBTMACROTRENDPRD
from core.stratP import StratPRD
import core.indicators as ic
from core.presel import Presel, WQ
from core.common import copy_attr

from orders.ib import retrieve_data,check_hold_duration
from orders.models import  get_candidates, Excluded, Strategy

from trading_bot.settings import _settings

"""
Strategies with preselection
a) It select one, two,... actions
b) It applies a "one action" strategy on it

For production
We try to mutualize the calculation as much as possible to avoid re-calculating the same several times
The orders are handled somewhere else, only the candidates need to be determined here 
"""

class PreselPRD(Presel):
    def __init__(self,use_IB,**kwargs):
 
        if kwargs.get("st",False):
            st=kwargs.get("st")
            self.st=st
            copy_attr(self,st)
        else:
            self.actions=kwargs.get("actions1")
            self.period=kwargs.get("period1")
            
            use_IB, symbols=retrieve_data(self,self.actions,self.period,use_IB )
                
        self.candidates=[[] for ii in range(len(self.close))]
        self.candidates_short=[[] for ii in range(len(self.close))]

        #avoid re-calculating what could have been calculated before
        if kwargs.get("vol",False):
            self.vol=kwargs.get("vol")
        else:
            self.vol=ic.VBTNATR.run(self.high,self.low,self.close).natr
        
        if kwargs.get("st",False): 
            self.ent11=st.entries
            self.ex11=st.exits
        else:
            st=StratPRD(use_IB,**kwargs)
            st.strat_kama_stoch_matrend_bbands()
            
            self.ent11=st.entries
            self.ex11=st.exits
            
        if kwargs.get("macd_tot",False):
            self.macd_tot=kwargs.get("macd_tot")
        else:
            self.macd_tot=vbt.MACD.run(self.close)
        
        if kwargs.get("macro_trend_ind",False):
            self.macro_trend_ind=kwargs.get("macro_trend_ind")
        else:
            self.macro_trend_ind=VBTMACROTRENDPRD.run(self.close_ind).macro_trend
        
        if kwargs.get("macro_trend",False):
            self.macro_trend=kwargs.get("macro_trend")
        else:
            self.macro_trend=VBTMACROTRENDPRD.run(self.close).macro_trend

        self.symbols_simple=self.close.columns.values
        self.symbols_complex=self.ent11.columns.values 
        self.exchange=kwargs.get("exchange")
        self.excluded=None
        self.start_capital=0 #required for overwrite_strat11
         
    def call_strat(self,name,**kwargs):
        meth=getattr(self,name)
        meth(PRD=True,**kwargs)
        
    def get_candidates(self):
        return self.candidates[-1], self.candidates_short[-1]     

    def actualize_hist_vol_slow(self,exchange):
         max_candidates_nb=_settings["HIST_VOL_SLOW_MAX_CANDIDATES_NB"]
         #take stoch
         v={}
         #to be saved longterm
         cand=get_candidates("hist_slow",exchange)
         cand.reset()
         
         macd_tot=vbt.MACD.run(self.close)
         macd=macd_tot.hist
         
         for symbol in self.symbols_simple:
             v[symbol]=self.vol[symbol].values[-1]
         res=sorted(v.items(), key=lambda tup: tup[1], reverse=True)
         
         for e in res:
             if len(cand.retrieve())<max_candidates_nb:
                 symbol=e[0]
             
                 if macd[symbol].values[-1]>0:
                    cand.append(symbol)   

    def actualize_realmadrid(self,exchange):
         max_candidates_nb=_settings["REALMADRID_MAX_CANDIDATES_NB"]
         distance=_settings["REALMADRID_DISTANCE"]
         #take stoch
         v={}
         self.excluded=Excluded.objects.get(name="realmadrid")
         
         #to be saved longterm
         cand=get_candidates("realmadrid",exchange)
         cand.reset()
         
         grow=ic.VBTGROW.run(self.close,distance=distance,ma=True).out 

         for symbol in self.symbols_simple:
             v[symbol]=grow[(distance,True,symbol)].values[-1]
         res=sorted(v.items(), key=lambda tup: tup[1], reverse=True)
         
         for e in res:
             if len(cand.retrieve())<max_candidates_nb:
                 symbol=e[0]
                 if symbol not in self.excluded.retrieve():
                     cand.append(symbol)  

    def check_dur(self, symbol,strategy, exchange,short,**kwargs):
        dur=check_hold_duration(symbol,strategy, exchange,short,**kwargs)
        if dur > _settings["RETARD_MAX_HOLD_DURATION"]: #max duration
            print("Retard: excluding " + symbol + " max duration exceeded")
            self.excluded.append(symbol)

    def preselect_retard_sub(self,ii,short,**kwargs):
        if self.excluded is None:
            retard_strat, _=Strategy.objects.get_or_create(name="retard")
            self.excluded, _=Excluded.objects.get_or_create(name="retard",strategy=retard_strat) 
            #can be the same for all exchange, no need for excluded short, as action cannot be in both
            # categories at the same time
        
        v={}       
        for symbol in self.symbols_simple:
            v[symbol]=self.dur[symbol].loc[self.close.index[ii]]
            if symbol in self.get_exclu_list(**kwargs): #if exclude take the next
                if v[symbol]==0: #trend change
                    self.excluded.remove(symbol)
     
        res=sorted(v.items(), key=lambda tup: tup[1], reverse=not short)
        
        for e in res:
            symbol=e[0]
            if kwargs.get("PRD",False):
                self.check_dur(symbol,"retard", self.exchange,short,**kwargs)
            if symbol not in self.get_exclu_list(**kwargs):
                if short:
                    self.candidates_short[ii].append(symbol)
                    break 
                else:   
                    self.candidates[ii].append(symbol)
                    break

        return res

#As WQ but for production
class WQPRD(WQ):
    def __init__(self,use_IB ,**kwargs):    
        if kwargs.get("st",False):
            st=kwargs.get("st")
            self.st=st
            copy_attr(self,st)

        else:
            self.actions=kwargs.get("actions1")
            self.period=kwargs.get("period1")
            
            use_IB, symbols=retrieve_data(self,self.actions,self.period,use_IB )
                
        self.candidates=[[] for ii in range(len(self.close))]
        self.trend=ic.VBTBBANDSTREND.run(self.close_ind).trend  
        
        self.symbols_simple=self.close.columns.values
        self.exchange=kwargs.get("exchange")
        
    def call_wqa(self, nb):
        self.nb=nb
        self.out = vbt.wqa101(nb).run(open=self.open, high=self.high,\
                                      low=self.low, close=self.close,volume=self.volume).out

    def get_candidates(self):
        return self.candidates[-1]