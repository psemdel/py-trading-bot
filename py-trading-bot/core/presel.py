#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat May 14 22:36:16 2022

@author: maxime
"""
import vectorbtpro as vbt
import pandas as pd
import numpy as np

from core.strat import Strat
from core.macro import VBTMACROTREND
import core.indicators as ic
from core.common import VBTfunc, copy_attr#, save_vbt_both

from trading_bot.settings import _settings
import logging
logger = logging.getLogger(__name__)
"""
Strategies with preselection
a) It select one, two,... actions
b) (optional) It applies a "one action" strategy on it

Note that I don't weight the portfolio, like in https://nbviewer.org/github/polakowo/vectorbt/blob/master/examples/PortfolioOptimization.ipynb
I just select one, two,... actions and put all my orders on them

Those strategies are home made (even though quite similar to classic one). For classic ones look at presel_classic
"""

class Presel(VBTfunc):
    def __init__(self,symbol_index,period,**kwargs):
        self.period=period
        self.symbol_index=symbol_index
        self.st=Strat(symbol_index,period,**kwargs)
        
        copy_attr(self,self.st)
        
        if kwargs.get("suffix"):
            self.suffix="_" + kwargs.get("suffix")
        else:
            self.suffix=""
        
        self.start_capital=10000
        self.order_size=self.start_capital
        self.capital=self.start_capital
        
        self.longshort=kwargs.get("longshort","long")
        
        self.entries=pd.DataFrame.vbt.empty_like(self.close, fill_value=False)
        self.exits=pd.DataFrame.vbt.empty_like(self.close, fill_value=False)
        
        self.exits_short=pd.DataFrame.vbt.empty_like(self.close, fill_value=False)
        self.entries_short=pd.DataFrame.vbt.empty_like(self.close, fill_value=False)

        self.entries2=pd.DataFrame.vbt.empty_like(self.close, fill_value=False)
        self.exits2=pd.DataFrame.vbt.empty_like(self.close, fill_value=False)
        
        self.exits_short2=pd.DataFrame.vbt.empty_like(self.close, fill_value=False)
        self.entries_short2=pd.DataFrame.vbt.empty_like(self.close, fill_value=False)
        
        self.pf=[]
        self.pf_short=[]
        self.pf_keep=[]
        self.pf_short_keep=[]
        
        self.vol=ic.VBTNATR.run(self.high,self.low,self.close).natr

        self.excluded=[]
        self.hold_dur=0
        
        self.candidates=[[] for ii in range(len(self.close))]
        self.candidates_short=[[] for ii in range(len(self.close))]
        
        self.symbols_simple=self.close.columns.values
        self.last_order_dir="long"
    
    def reinit(self):
        self.capital=self.start_capital        
        self.pf=[]
        self.pf_short=[]
        self.pf_keep=[]
        self.pf_short_keep=[]
        self.entries=pd.DataFrame.vbt.empty_like(self.close, fill_value=False)
        self.exits=pd.DataFrame.vbt.empty_like(self.close, fill_value=False)
        self.exits_short=pd.DataFrame.vbt.empty_like(self.close, fill_value=False)
        self.entries_short=pd.DataFrame.vbt.empty_like(self.close, fill_value=False)
    
    def overwrite_strat_underlying(self,ent,ex):
        self.reinit()
        self.ent_underlying=ent
        self.ex_underlying=ex
        self.symbols_complex_ent=self.ent_underlying.columns.values
        self.symbols_complex_ex=self.ex_underlying.columns.values
        
    def overwrite_ex_strat_underlying(self,ex):
        self.reinit()
        self.ex_underlying=ex
        self.symbols_complex_ex=self.ex_underlying.columns.values
        
    def symbols_simple_to_complex(self,symbol_simple,ent_or_ex):
        if ent_or_ex=="ent":
            symbols=self.symbols_complex_ent
        else:
            symbols=self.symbols_complex_ex

        if type(symbols[0])==str:
            return symbol_simple
        for ii, e in enumerate(symbols):
            if e[-1]==symbol_simple: #9
                return e
            
    ##create buy/sell from candidates
    def calculate(self,**kwargs): #day basis
        daily_sl=kwargs.get("daily_sl")
        sl=kwargs.get("sl")
        last_entry_price=0
    
        for ii in range(len(self.close.index)): #for each day
            if ii!=0:
                if not kwargs.get("short",False):
                    #sell
                    new_pf=self.pf.copy()
                    for symbol_simple in self.pf:
                        symbol_complex=self.symbols_simple_to_complex(symbol_simple,"ex")
                        
                        if self.ex_underlying[symbol_complex].values[ii] or kwargs.get("nostrat_underlying",False) or\
                        (daily_sl is not None and self.close[symbol_simple].iloc[ii]/self.close[symbol_simple].iloc[ii-1]<(1-daily_sl)) or\
                        (sl is not None and last_entry_price!=0 and self.close[symbol_simple].iloc[ii]/last_entry_price<(1-sl)):
                            new_pf.remove(symbol_simple)
                            self.capital+=self.order_size
                            self.exits[symbol_simple].iloc[ii]=True
                                
                    self.pf=new_pf
                    #buy
                    for symbol_simple in self.candidates[ii]:
                        symbol_complex=self.symbols_simple_to_complex(symbol_simple,"ent")
                        
                        if self.capital>=self.order_size and\
                            (kwargs.get("nostrat_underlying",False)
                             or kwargs.get("only_exit_strat_underlying",False) or self.ent_underlying[symbol_complex].values[ii]):
                            self.pf.append(symbol_simple)
                            self.capital-=self.order_size
                            self.entries[symbol_simple].iloc[ii]=True
                            last_entry_price=self.close[symbol_simple].iloc[ii]
                            
                if kwargs.get("short",False):
                    #re-buy
                    new_pf=self.pf_short.copy()
                    for symbol_simple in self.pf_short:
                        symbol_complex=self.symbols_simple_to_complex(symbol_simple,"ent")
              
                        if kwargs.get("nostrat_underlying",False) or self.ent_underlying[symbol_complex].values[ii]:
                            new_pf.remove(symbol_simple)
                            self.capital+=self.order_size #wrong but I want only one
                            self.exits_short[symbol_simple].iloc[ii]=True 
                    self.pf_short=new_pf

                    for symbol_simple in self.candidates_short[ii]:
                        symbol_complex=self.symbols_simple_to_complex(symbol_simple,"ex")
                        
                        if self.capital>=self.order_size and\
                        (kwargs.get("nostrat_underlying",False) or 
                         kwargs.get("only_exit_strat_underlying",False) or 
                         self.ex_underlying[symbol_complex].values[ii]):
                            self.pf_short.append(symbol_simple)
                            self.capital-=self.order_size
                            self.entries_short[symbol_simple].iloc[ii]=True  
                            
    ##create buy/sell from candidates, when macro trend is involved
    def calculate_macro(self,**kwargs):
        for ii in range(len(self.close.index)): #for each day
            #sell
            for symbol_simple in self.pf:
                symbol_complex_ent=self.symbols_simple_to_complex(symbol_simple,"ent")
                symbol_complex_ex=self.symbols_simple_to_complex(symbol_simple,"ex")
                
                if (self.last_order_dir=="long" and self.ex_underlying[symbol_complex_ex].values[ii] ) or\
                   (self.last_order_dir!="long" and self.ent_underlying[symbol_complex_ent].values[ii] ) or\
                    kwargs.get("nostrat_underlying",False):
                        
                    self.pf.remove(symbol_simple)
                    self.capital+=self.order_size
                    
                    if self.last_order_dir=="long":
                        self.exits[symbol_simple].iloc[ii]=True
                    else:
                        self.exits_short[symbol_simple].iloc[ii]=True 
            #buy
            if len(self.candidates[ii])==0 and len(self.candidates_short[ii])!=0:
                short=True
                cand=self.candidates_short[ii]
            else:
                short=False
                cand=self.candidates[ii]
                
            
            for symbol_simple in cand:
                symbol_complex_ent=self.symbols_simple_to_complex(symbol_simple,"ent")
                symbol_complex_ex=self.symbols_simple_to_complex(symbol_simple,"ex")
                
                if self.capital>=self.order_size and\
                    (not short and (self.ent_underlying[symbol_complex_ent].values[ii] or kwargs.get("nostrat_underlying",False)
                     or kwargs.get("only_exit_strat_underlying",False))) or \
                    (short and (self.ex_underlying[symbol_complex_ex].values[ii] or kwargs.get("nostrat_underlying",False)
                     or kwargs.get("only_exit_strat_underlying",False))):
                        
                    self.pf.append(symbol_simple)
                    self.capital-=self.order_size
 
                    if short:
                        self.entries_short[symbol_simple].iloc[ii]=True
                        self.last_order_dir="short"                    
                    else:               
                        self.entries[symbol_simple].iloc[ii]=True
                        self.last_order_dir="long"
    
    def get_exclu_list(self, **kwargs):
        if kwargs.get("PRD",False):
            return self.excluded.retrieve()
        else:
            return self.excluded
        
    #same with hold_dur and exclusion
    def calculate_retard(self,ii,short,**kwargs):
        
        if ii!=0:
             if kwargs.get("keep",False):
                 for symbol_simple in self.pf_keep:
                     symbol_complex=self.symbols_simple_to_complex(symbol_simple,"ex")
                     if self.ex_underlying[symbol_complex].values[ii]:
                         self.pf_keep.remove(symbol_simple)
                         self.exits2[symbol_simple].iloc[ii]=True
                         
                 for symbol_simple in self.pf_short_keep:
                     symbol_complex=self.symbols_simple_to_complex(symbol_simple,"ent")
                     if self.ent_underlying[symbol_complex].values[ii]:
                         self.pf_short_keep.remove(symbol_simple)
                         self.exits_short2[symbol_simple].iloc[ii]=True       
                         #print("exiting short " + str(ii))

             #sell
             if short:
                 cand=self.candidates_short[ii]
             else:
                 cand=self.candidates[ii]   
  
             for symbol in self.pf:
                 if symbol not in cand:
                     self.pf.remove(symbol)
                     self.capital+=self.order_size
                     
                     if self.last_order_dir=="long":
                         self.exits[symbol].iloc[ii]=True
                     else:
                         self.exits_short[symbol].iloc[ii]=True
                     self.hold_dur=0
                     
                     if kwargs.get("keep",False):
                         if self.last_order_dir=="long":
                             if len(self.pf_keep)==0:
                                 self.pf_keep.append(symbol)
                                 self.entries2[symbol].iloc[ii]=True  
                         else:
                             if len(self.pf_short_keep)==0:
                                 self.pf_short_keep.append(symbol)
                                 self.entries_short2[symbol].iloc[ii]=True 
                 else:
                     self.hold_dur+=1

             #buy
             for symbol in cand:
                 if symbol not in self.pf and symbol not in self.excluded: #should not be called in production
                     if self.capital>=self.order_size:
                         self.pf.append(symbol)
                         self.capital-=self.order_size #not correct, but we want only 1 order
                          
                         if short:
                             self.entries_short[symbol].iloc[ii]=True 
                             self.last_order_dir="short"                             
                         else:
                             self.entries[symbol].iloc[ii]=True  
                             self.last_order_dir="long"
            
    #See preselect_vol
    def preselect_vol_sub(self, ii, **kwargs):
        v={}
        self.candidates[ii]=[]
        self.max_candidates_nb=_settings["VOL_MAX_CANDIDATES_NB"]
        
        for symbol in self.symbols_simple:
            v[symbol]=self.vol[symbol].values[ii]
        res=sorted(v.items(), key=lambda tup: tup[1], reverse=True)
        
        for e in res:
            symbol_simple=e[0]
            symbol_complex=self.symbols_simple_to_complex(symbol_simple,"ent")

            #we need a candidate that fulfill strat_underlying criterium
            #otherwise the chance to buy something is very low.
            if (len(self.candidates[ii])<self.max_candidates_nb and
               self.ent_underlying[symbol_complex].values[ii] or kwargs.get("nostrat_underlying",False)):
               self.candidates[ii].append(symbol_simple)
        return res
     
    #Preselect action based on the volatility. The highest volatility is chosen.      
    def preselect_vol(self, **kwargs):
        self.st.strat_kama_stoch_matrend_bbands()
        self.overwrite_strat_underlying(self.st.entries,self.st.exits)        

        #take stoch
        if kwargs.get("PRD",False):
            res=self.preselect_vol_sub(len(self.close)-1,**kwargs)
        else:
            for ii in range(len(self.close.index)):
                res=self.preselect_vol_sub(ii,**kwargs)
            self.calculate(**kwargs)
        self.out=res #last one                 

    #See preselect_retard
    #Coded only for one candidate
    def preselect_retard_sub(self,ii,short,**kwargs):
        v={}       
        self.candidates[ii]=[]
        self.candidates_short[ii]=[]
             
        for symbol in self.symbols_simple:
            v[symbol]=self.dur[symbol].loc[self.close.index[ii]]
            if symbol in self.get_exclu_list(**kwargs): #if exclude take the next
                if v[symbol]==0: #trend change
                    self.excluded.remove(symbol)
   
        res=sorted(v.items(), key=lambda tup: tup[1], reverse=not short)
            
        for e in res:
            symbol=e[0]
            if kwargs.get("PRD",False):
                print("retard for production is defined in BtP")
                #self.check_dur(symbol,**kwargs)
            if symbol not in self.get_exclu_list(**kwargs):
                if short:
                    self.candidates_short[ii].append(symbol)
                    break                 
                else:
                    self.candidates[ii].append(symbol)
                    break

        return res

    #Calculate the number of day in a row when the smoother price of an action has been decreasing
    #The action the longest duration is bought
    #(Follow the loser) similar to RMR
    def preselect_retard(self,**kwargs):
        self.dur=ic.VBTKAMATREND.run(self.close).duration
           
        short=kwargs.get("short",False)
        if kwargs.get("PRD",False):
            self.preselect_retard_sub(len(self.close.index)-1,short,**kwargs)   
        else:
            for ii in range(len(self.close.index)):
                 if self.hold_dur > _settings["RETARD_MAX_HOLD_DURATION"]:
                     self.excluded.append(self.pf[0])
                  
                 res=self.preselect_retard_sub(ii,short,**kwargs)                         
                 self.calculate_retard(ii,short,**kwargs)
                    
        self.out=res #last one  
        return res                   

        
    #See preselect_macd_vol
    def preselect_macd_vol_sub(self,ii,short,**kwargs):    
        v={}
        macd=self.macd_tot.macd
        self.candidates[ii]=[]
        self.candidates_short[ii]=[]
        self.max_candidates_nb=_settings["MACD_VOL_MAX_CANDIDATES_NB"]
        
        for symbol in self.symbols_simple:
            v[symbol]=self.vol[symbol].values[ii]
        res=sorted(v.items(), key=lambda tup: tup[1], reverse=True)
        
        for e in res:
            if len(self.candidates[ii])<self.max_candidates_nb:
                symbol=e[0]
                
                if short and macd[('simple','simple',symbol)].values[ii]<0:
                   self.candidates_short[ii].append(symbol)
                elif not short and macd[('simple','simple',symbol)].values[ii]>0:
                   self.candidates[ii].append(symbol)
        return res
    
    #Preselect action based on the volatility. The highest volatility is chosen.  
    #As supplementary criterium, the MACD must be positive for the long variant.
    def preselect_macd_vol(self,**kwargs):
         self.st.strat_kama_stoch_matrend_bbands()
         self.overwrite_strat_underlying(self.st.entries,self.st.exits)
        
         short=kwargs.get("short",False)
         
         if kwargs.get("PRD",False):
             res=self.preselect_macd_vol_sub(len(self.close.index)-1,short)
         else:
             self.macd_tot=vbt.MACD.run(self.close, macd_wtype='simple',signal_wtype='simple')

             for ii in range(len(self.close.index)):
                 res=self.preselect_macd_vol_sub(ii,short)

             self.calculate(**kwargs)
         self.out=res #last one 
                
    #See preselect_hist_vol
    def preselect_hist_vol_sub(self,ii,short,**kwargs):  
        v={}
        hist=self.macd_tot.hist
        self.candidates[ii]=[]
        self.candidates_short[ii]=[]
        self.max_candidates_nb=_settings["HIST_VOL_MAX_CANDIDATES_NB"]
        
        for symbol in self.symbols_simple:
            v[symbol]=self.vol[symbol].values[ii]
        res=sorted(v.items(), key=lambda tup: tup[1], reverse=True)
        
        for e in res:
            if len(self.candidates[ii])<self.max_candidates_nb:
                symbol=e[0]
                if short and hist[('simple','simple',symbol)].values[ii]<0:
                   self.candidates_short[ii].append(symbol)
                elif not short and hist[('simple','simple',symbol)].values[ii]>0:
                   self.candidates[ii].append(symbol)
        return res   
      
    #Preselect action based on the volatility. The highest volatility is chosen.  
    #As supplementary criterium, the hist (see MACD) must be positive for the long variant.           
    def preselect_hist_vol(self,**kwargs):
         self.st.stratF()        
         self.overwrite_strat_underlying(self.st.entries,self.st.exits)
         short=kwargs.get("short",False)

         if kwargs.get("PRD",False):
             res=self.preselect_hist_vol_sub(len(self.close.index)-1,short)
         else:
             self.macd_tot=vbt.MACD.run(self.close, macd_wtype='simple',signal_wtype='simple')
             
             for ii in range(len(self.close.index)):
                 res=self.preselect_hist_vol_sub(ii,short)

         self.calculate(**kwargs)                
         self.out=res #last one 

### Macro trend ### 
# Preselection using the macro trend

    #See preselect_macd_vol_macro
    def preselect_macd_vol_macro_sub(self,ii,**kwargs):
        try:
            v={}       
            macd=self.macd_tot.macd
            self.candidates[ii]=[]
            self.candidates_short[ii]=[]
            
            for symbol in self.symbols_simple:
                v[symbol]=self.vol[symbol].values[ii]
            res=sorted(v.items(), key=lambda tup: tup[1], reverse=True)
            
            for e in res:
                symbol=e[0]
                #symbol_complex=self.symbols_simple_to_complex(symbol)
                
                if kwargs.get("macro_trend_index",False):
                    short=(self.macro_trend.values[ii]==1)
                else:
                    short=(self.macro_trend[symbol].values[ii]==1)
                    
                if short and macd[('simple','simple',symbol)].values[ii]<0:
                   self.candidates_short[ii].append(symbol)
                   break              
                else:
                   self.candidates[ii].append(symbol)
                   break
     
            return res
        
        except Exception as e:
            logger.error(e, stack_info=True, exc_info=True)
        
    #Like preselect_macd_vol, but the long/short is decided in function of the macro trend
    def preselect_macd_vol_macro(self,**kwargs):
         self.st.stratD()        
         self.overwrite_strat_underlying(self.st.entries,self.st.exits)
        
         if kwargs.get("macro_trend_index",False):
             self.macro_trend=VBTMACROTREND.run(self.close_ind).macro_trend
         else:
             self.macro_trend=VBTMACROTREND.run(self.close).macro_trend
         #self.macro_trend=kwargs.get("macro_trend")
         self.macd_tot=vbt.MACD.run(self.close, macd_wtype='simple',signal_wtype='simple')
         
         if kwargs.get("PRD",False):
             res=self.preselect_macd_vol_macro_sub(len(self.close.index)-1,**kwargs)
         else:
             #self.macd_tot=kwargs.get("macd") 
             for ii in range(len(self.close.index)):
                res=self.preselect_macd_vol_macro_sub(ii,**kwargs)
           
             self.calculate_macro(**kwargs)
         self.out=res #last one 

     #Like retard, but the long/short is decided in function of the macro trend
     #Obviously the logic is reverted
    def preselect_retard_macro(self,**kwargs):
        if kwargs.get("keep",False):
            self.st.stratF()        
            self.overwrite_strat_underlying(self.st.entries,self.st.exits)            
        
        self.dur=ic.VBTKAMATREND.run(self.close).duration
        self.macro_trend=VBTMACROTREND.run(self.close_ind,threshold=0.03).macro_trend #theshold 3% is clearly better in this case than 4%
                
        if kwargs.get("PRD",False) and not kwargs.get("reset_excluded",False):
            short=(self.macro_trend.values[-1]==1)
            res=self.preselect_retard_sub(len(self.close.index)-1,short,**kwargs)
        else:    
            if kwargs.get("reset_excluded",False):
                self.excluded.reset()

            for ii in range(len(self.close.index)):
                short=(self.macro_trend.values[ii]==1)
                
                if self.hold_dur > _settings["RETARD_MAX_HOLD_DURATION"]:
                    self.excluded.append(self.pf[0])

                res=self.preselect_retard_sub(ii,short,**kwargs)           
                self.calculate_retard(ii,short,**kwargs)
        self.out=res #last one    
        self.last_short=short
        #return res #for display

    #See preselect_divergence
    def preselect_divergence_sub(self,ii,short,**kwargs):
        v={}
        self.candidates[ii]=[]
        self.candidates_short[ii]=[]
        
        threshold=_settings["DIVERGENCE_THRESHOLD"]

       # if not short:
        for symbol in self.divergence.columns:
            v[symbol]=self.divergence[symbol].values[ii]
            
        res=sorted(v.items(), key=lambda tup: tup[1], reverse=short)

        for e in res:
            if not short and e[1]<-threshold:
                symbol=e[0]
                self.candidates[ii].append(symbol)
                break
            elif short and e[1]>threshold:
                symbol=e[0]
                self.candidates_short[ii].append(symbol)
                break
               
    #This strategy measures the difference between the variation of each action smoothed price and 
    #the variation of the corresponding smoothed price
    #When the difference is negative, the action is bought. So the action which evolves lower than 
    #the index is bought
    #(Follow the loser)
    def preselect_divergence(self,**kwargs):
        self.st.stratDiv()
        self.overwrite_strat_underlying(self.st.entries,self.st.exits)
        
        self.divergence=ic.VBTDIVERGENCE.run(self.close,self.close_ind).out

        if kwargs.get("PRD",False):
            self.preselect_divergence_sub(len(self.close.index)-1,False,**kwargs)
        else:
            for ii in range(len(self.close)):
                self.preselect_divergence_sub(ii,False,**kwargs)
            self.calculate(only_exit_strat_underlying=True,**kwargs) 
            #self.entries.to_csv('initial')
            
    #Like preselect_divergence, but the mechanism is blocked when macro_trend is bear
    #Reverting the mechanism did not prove to be very rewarding for this strategy
    def preselect_divergence_blocked(self,**kwargs):
        self.st.stratDiv()
        self.overwrite_strat_underlying(self.st.entries,self.st.exits)
        
        self.divergence=ic.VBTDIVERGENCE.run(self.close,self.close_ind).out
        self.macro_trend=VBTMACROTREND.run(self.close_ind).macro_trend   
        
        if kwargs.get("PRD",False):
            short=(self.macro_trend.values[-1]==1)
            self.preselect_divergence_sub(len(self.close.index)-1,short,**kwargs)
        else:
            for ii in range(len(self.close)):
                short=(self.macro_trend.values[ii]==1)
                self.preselect_divergence_sub(ii,short,**kwargs)
            self.calculate(only_exit_strat_underlying=True,**kwargs) #for a blocked behavior
            #self.calculate_macro(only_exit_strat_underlying=True,**kwargs)  #for a macro behavior

    def preselect_divergence_sl(self,**kwargs):
        self.st.stratDiv()
        self.overwrite_strat_underlying(self.st.entries,self.st.exits)
        
        self.divergence=ic.VBTDIVERGENCE.run(self.close,self.close_ind).out

        if kwargs.get("PRD",False):
            self.preselect_divergence_sub(len(self.close.index)-1,False,**kwargs)
        else:
            for ii in range(len(self.close)):
                self.preselect_divergence_sub(ii,False,**kwargs)
            self.calculate(only_exit_strat_underlying=True,sl=0.1, **kwargs) 
            #self.entries.to_csv('initial')            
### Slow ###
#Not called for production

#Slow strategy re-actualise the candidates on a given frequency, typically every 10 days
#The issue with strategy that reactualize the candidates every day is that the entry mechanism replace the one
#from the underlying strategy.

    #Like preselect_vol but slow
    def preselect_vol_slow(self, **kwargs):
        #take stoch
        self.st.stratF()        
        self.overwrite_strat_underlying(self.st.entries,self.st.exits)

        v={}
        self.frequency=_settings["VOL_SLOW_FREQUENCY"]
        self.max_candidates_nb=_settings["VOL_SLOW_MAX_CANDIDATES_NB"]
        
        for ii in range(len(self.close.index)):
            if ii%self.frequency==0: #every 10 days
                for symbol in self.symbols_simple:
                    v[symbol]=self.vol[symbol].values[ii]
                res=sorted(v.items(), key=lambda tup: tup[1], reverse=True)
            
                for e in res:
                    if len(self.candidates[ii])<self.max_candidates_nb:
                        symbol_simple=e[0]
                        #start _underlying managed in calculate
                        self.candidates[ii].append(symbol_simple)
            elif ii!=0:
                self.candidates[ii]=self.candidates[ii-1]
               
        self.calculate(**kwargs)

    #Like preselect_macd_vol but slow
    def preselect_macd_vol_slow(self,**kwargs):
         self.st.strat_kama_stoch_matrend_bbands()
         self.overwrite_strat_underlying(self.st.entries,self.st.exits)
         v={}
         
         self.frequency=_settings["MACD_VOL_SLOW_FREQUENCY"]
         self.max_candidates_nb=_settings["MACD_VOL_SLOW_MAX_CANDIDATES_NB"]
         
         macd_tot=vbt.MACD.run(self.close, macd_wtype='simple',signal_wtype='simple')
         macd=macd_tot.macd

         for ii in range(len(self.close.index)):
             if ii%self.frequency==0: #every 10 days
                 for symbol in self.symbols_simple:
                     v[symbol]=self.vol[symbol].values[ii]
                 res=sorted(v.items(), key=lambda tup: tup[1], reverse=True)
                 
                 for e in res:
                     if len(self.candidates[ii])<self.max_candidates_nb:
                         symbol=e[0]
                     
                         if not kwargs.get("short",False) and macd[('simple','simple',symbol)].values[ii]>0:
                            self.candidates[ii].append(symbol)
                         elif kwargs.get("short",False) and macd[('simple','simple',symbol)].values[ii]<0:
                            self.candidates_short[ii].append(symbol)
             elif ii!=0:
                 self.candidates[ii]=self.candidates[ii-1]                            
                            
         self.calculate(**kwargs)
         
    #Like preselect_hist_vol but slow
    def preselect_hist_vol_slow(self,**kwargs):
         self.st.stratE()        
         self.overwrite_strat_underlying(self.st.entries,self.st.exits)
        
         v={}
         
         self.frequency=_settings["HIST_VOL_SLOW_FREQUENCY"]  
         self.max_candidates_nb=_settings["HIST_VOL_SLOW_MAX_CANDIDATES_NB"]
         
         macd_tot=vbt.MACD.run(self.close, macd_wtype='simple',signal_wtype='simple')
         macd=macd_tot.hist

         for ii in range(len(self.close.index)):
             if ii%self.frequency==0: #every 10 days
                 for symbol in self.symbols_simple:
                     v[symbol]=self.vol[symbol].values[ii]
                 res=sorted(v.items(), key=lambda tup: tup[1], reverse=True)
                 
                 for e in res:
                     if len(self.candidates[ii])<self.max_candidates_nb:
                         symbol=e[0]
                     
                         if not kwargs.get("short",False) and macd[('simple','simple',symbol)].values[ii]>0:
                            self.candidates[ii].append(symbol)
                         elif kwargs.get("short",False) and macd[('simple','simple',symbol)].values[ii]<0:
                            self.candidates_short[ii].append(symbol)
             elif ii!=0:
                 self.candidates[ii]=self.candidates[ii-1]
                 
         self.calculate(**kwargs)   
         
#Strategy that bet on the actions that growed the most in the past (Follow the winner)
#Bet on the one that usually win    
    def preselect_realmadrid(self,**kwargs):   
         self.st.stratReal()
         self.overwrite_strat_underlying(self.st.entries,self.st.exits)

         distance=_settings["REALMADRID_DISTANCE"]
         self.frequency=_settings["REALMADRID_FREQUENCY"]
         self.max_candidates_nb=_settings["REALMADRID_MAX_CANDIDATES_NB"]

         v={}
         grow=ic.VBTGROW.run(self.close,distance=distance,ma=True).out
        
         for ii in range(len(self.close.index)):
             if ii%self.frequency==0: #every 10 days
                 for symbol in self.symbols_simple:
                     v[symbol]=grow[(distance,True,symbol)].values[ii]
                 res=sorted(v.items(), key=lambda tup: tup[1], reverse=True)

                 for e in res:
                    if len(self.candidates[ii])<self.max_candidates_nb:
                        symbol=e[0]
                        self.candidates[ii].append(symbol)
             elif ii!=0:
                 self.candidates[ii]=self.candidates[ii-1]                         
         self.calculate(**kwargs)           

    def preselect_realmadrid_blocked(self,**kwargs):   
         self.st.stratReal()
         self.overwrite_strat_underlying(self.st.entries,self.st.exits)
        
         distance=_settings["REALMADRID_DISTANCE"]
         self.frequency=_settings["REALMADRID_FREQUENCY"]
         self.max_candidates_nb=_settings["REALMADRID_MAX_CANDIDATES_NB"]
         self.macro_trend=VBTMACROTREND.run(self.close_ind).macro_trend  
         v={}
         grow=ic.VBTGROW.run(self.close,distance=distance,ma=True).out
        
         for ii in range(len(self.close.index)):
             short=(self.macro_trend.values[ii]==1)
             if ii%self.frequency==0: #every 10 days
                 if not short:
                     for symbol in self.symbols_simple:
                         v[symbol]=grow[(distance,True,symbol)].values[ii]
                     res=sorted(v.items(), key=lambda tup: tup[1], reverse=True)
    
                     for e in res:
                         if len(self.candidates[ii])<self.max_candidates_nb:
                             symbol=e[0]
                             self.candidates[ii].append(symbol)
             elif ii!=0 and not short:
                 self.candidates[ii]=self.candidates[ii-1]                         
         self.calculate(**kwargs)   
         
    def preselect_realmadrid_sl(self,**kwargs):   
         self.st.stratReal()
         self.overwrite_strat_underlying(self.st.entries,self.st.exits)

         distance=_settings["REALMADRID_DISTANCE"]
         self.frequency=_settings["REALMADRID_FREQUENCY"]
         self.max_candidates_nb=_settings["REALMADRID_MAX_CANDIDATES_NB"]

         v={}
         grow=ic.VBTGROW.run(self.close,distance=distance,ma=True).out
        
         for ii in range(len(self.close.index)):
             if ii%self.frequency==0: #every 10 days
                 for symbol in self.symbols_simple:
                     v[symbol]=grow[(distance,True,symbol)].values[ii]
                 res=sorted(v.items(), key=lambda tup: tup[1], reverse=True)

                 for e in res:
                    if len(self.candidates[ii])<self.max_candidates_nb:
                        symbol=e[0]
                        self.candidates[ii].append(symbol)
             elif ii!=0:
                 self.candidates[ii]=self.candidates[ii-1]                         
         self.calculate(sl=0.005,**kwargs)             
         
    def preselect_onlybull_vol(self,**kwargs):
        self.macro_trend=VBTMACROTREND.run(self.close).macro_trend   
        
        for ii in range(len(self.close.index)):
            bull_symbols=self.macro_trend.loc[:,(self.macro_trend.iloc[ii] == -1)].columns

            #we want to change the action only if it is not anymore bull
            find_new_cand=True
            
            if ii!=0 and len(self.candidates[ii-1])>0:
                if self.candidates[ii-1][0] in bull_symbols:
                    find_new_cand=False #keep the same
                    self.candidates[ii]=self.candidates[ii-1]
                    
            if find_new_cand:
                v={}    
                self.candidates[ii]=[]
                for symbol in bull_symbols:
                    v[symbol]=self.vol[symbol].values[ii]
                res=sorted(v.items(), key=lambda tup: tup[1], reverse=False)
                for e in res:
                    symbol=e[0]
                    self.candidates[ii].append(symbol)
                    break
            self.calculate_retard(ii,False,**kwargs)            

    def preselect_onlybull_hist(self,**kwargs):
        self.macro_trend=VBTMACROTREND.run(self.close).macro_trend   
        macd_tot=vbt.MACD.run(self.close, macd_wtype='simple',signal_wtype='simple')
        macd=macd_tot.macd
        
        for ii in range(len(self.close.index)):
            bull_symbols=self.macro_trend.loc[:,(self.macro_trend.iloc[ii] == -1)].columns

            #we want to change the action only if it is not anymore bull
            find_new_cand=True
            
            if ii!=0 and len(self.candidates[ii-1])>0:
                if self.candidates[ii-1][0] in bull_symbols:
                    find_new_cand=False #keep the same
                    self.candidates[ii]=self.candidates[ii-1]
                    
            if find_new_cand:
                v={}    
                self.candidates[ii]=[]
                for symbol in bull_symbols:
                    v[symbol]=macd[('simple','simple',symbol)].values[ii]/self.close[symbol].values[ii]
                res=sorted(v.items(), key=lambda tup: tup[1], reverse=False)
                for e in res:
                    symbol=e[0]
                    self.candidates[ii].append(symbol)
                    break
            self.calculate_retard(ii,False,**kwargs)     
 
    def preselect_onlybull_grow(self,**kwargs):
        distance=_settings["REALMADRID_DISTANCE"]
        self.macro_trend=VBTMACROTREND.run(self.close).macro_trend   
        grow=ic.VBTGROW.run(self.close,distance=distance,ma=True).out
        
        for ii in range(len(self.close.index)):
            bull_symbols=self.macro_trend.loc[:,(self.macro_trend.iloc[ii] == -1)].columns

            #we want to change the action only if it is not anymore bull
            find_new_cand=True
            
            if ii!=0 and len(self.candidates[ii-1])>0:
                if self.candidates[ii-1][0] in bull_symbols:
                    find_new_cand=False #keep the same
                    self.candidates[ii]=self.candidates[ii-1]
                    
            if find_new_cand:
                v={}    
                self.candidates[ii]=[]
                for symbol in bull_symbols:
                    v[symbol]=v[symbol]=grow[(distance,True,symbol)].values[ii]
                res=sorted(v.items(), key=lambda tup: tup[1], reverse=True)
                for e in res:
                    symbol=e[0]
                    self.candidates[ii].append(symbol)
                    break
            self.calculate_retard(ii,False,**kwargs)     

#WQ uses the prebuild 101 Formulaic Alphas
#No underlying strategy is necessary
class WQ(VBTfunc):
    def __init__(self,symbol_index,period, nb):
        super().__init__(symbol_index,period)
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

    ##create buy/sell from candidates
    def calculate(self,**kwargs): #day basis
        for ii in range(len(self.close.index)): #for each day
            if ii!=0:
                #sell
                for symbol_simple in self.pf:
                    if symbol_simple not in self.candidates[ii]:
                        self.pf.remove(symbol_simple)
                        self.capital+=self.order_size
                        self.exits[symbol_simple].iloc[ii]=True
            
                #buy
                for symbol_simple in self.candidates[ii]:
                    if self.capital>=self.order_size:
                        self.pf.append(symbol_simple)
                        self.capital-=self.order_size
                        self.entries[symbol_simple].iloc[ii]=True

    def def_cand(self):
        self.candidates=[[] for ii in range(len(self.close))]
        if self.nb in [1]:
            threshold= np.sum(self.out.iloc[0].values)/len(self.out.iloc[0].values)*1.1

        for ii in range(len(self.out)):
            try:
                ind_max=np.nanargmax(self.out.iloc[ii].values)
                if self.nb in [1]:
                    if self.out.iloc[ii,ind_max]>threshold:
                        symbol=self.out.columns[ind_max]
                        self.candidates[ii].append(symbol)
                else:
                    symbol=self.out.columns[ind_max]
                    self.candidates[ii].append(symbol) 
            except:
                pass

