#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat May 14 22:36:16 2022

@author: maxime
"""
import vectorbtpro as vbt
import numpy as np

import inspect
from core.common import VBTfunc, save_vbt_both
import core.indicators as ic
from core.macro import major_int, VBTMACROFILTER, VBTMACROMODE, VBTMACROTREND, VBTMACROTRENDPRD
from core.constants import BEAR_PATTERNS, BULL_PATTERNS

import sys
### Strategies on one action, no preselection ###
#So it determines entries and exits for one action to optimize the return


#wrapper for talib function
def function_to_res(f_name, open_, high, low, close,**kwargs):
    f_callable=getattr(ic,f_name)
    needed_args=inspect.getfullargspec(f_callable.run).args

    if ('open_' in needed_args) and ('close' in needed_args) and\
       ('high' in needed_args) and ('low' in needed_args) :
        if "light" in needed_args:
            res = f_callable.run(open_, high, low, close,**kwargs)
        else:
            res = f_callable.run(open_, high, low, close)
            
    elif ('close' in needed_args) and\
       ('high' in needed_args) and ('low' in needed_args) :  
        if "light" in needed_args:
            res = f_callable.run(high, low, close,**kwargs)
        else:
            res = f_callable.run(high, low, close)
    elif ('open_' in needed_args) and\
          ('high' in needed_args) and ('low' in needed_args) :  
        if "light" in needed_args:
            res = f_callable.run(open_,  low, close,**kwargs)
        else:
            res = f_callable.run(open_,  low, close)
    elif  ('close' in needed_args)  and ('low' in needed_args) :  
        if "light" in needed_args:
               res = f_callable.run(low, close,**kwargs)
        else:
               res = f_callable.run(low, close)
    elif  ('high' in needed_args)  and ('low' in needed_args) :  
        if "light" in needed_args:           
           res = f_callable.run(high, low,**kwargs)
        else:
           res = f_callable.run(high, low) 
    else:
        if "light" in needed_args:  
           res = f_callable.run(close,**kwargs)
        else:
           res = f_callable.run(close)
    
    return res.entries, res.exits

#Convert a binary array intro entries and exits
#A faster algorithm is possible, but then the optimization algorithm would differ
#Speed should still be acceptable
def defi_i( open_,high, low, close):
    
    try:
        all_t_ent=[]
        all_t_ex=[]
        
        t=ic.VBTMA.run(close)
        all_t_ent.append(t.entries)
        all_t_ex.append(t.exits)
        
        t=ic.VBTSTOCHKAMA.run(high,low,close)
        all_t_ent.append(t.entries_stoch)
        all_t_ex.append(t.exits_stoch)   
    
        all_t_ent.append(t.entries_kama)
        all_t_ex.append(t.exits_kama)   
    
        t=ic.VBTSUPERTREND.run(high,low,close)
        all_t_ent.append(t.entries)
        all_t_ex.append(t.exits)
                        
        t=vbt.BBANDS.run(close)
        all_t_ent.append(t.lower_above(close))
        all_t_ex.append(t.upper_below(close))
    
        t=vbt.RSI.run(close,wtype='simple')
        all_t_ent.append(t.rsi_crossed_below(20))
        all_t_ex.append(t.rsi_crossed_above(80))
        
        all_t_ent.append(t.rsi_crossed_below(30))
        all_t_ex.append(t.rsi_crossed_above(70))
    
        for func_name in BULL_PATTERNS:
            t=ic.VBTPATTERNONE.run(open_,high,low,close,func_name, "ent").out
            all_t_ent.append(t)
            
        for func_name in BEAR_PATTERNS:
            t=ic.VBTPATTERNONE.run(open_,high,low,close,func_name, "ex").out
            all_t_ex.append(t)        
        return all_t_ent, all_t_ex
    except Exception as msg:
        print(msg)
        print("exception in " + __name__)
        _, e_, exc_tb = sys.exc_info()
        print("line " + str(exc_tb.tb_lineno))
        print(msg)  
        
def defi(close,all_t,ent_or_ex, calc_arrs,macro_trend):
    len_ent=7+len(BULL_PATTERNS)
    len_ex=7+len(BEAR_PATTERNS)
    ents_raw=None 
    
    for nb_macro_mode in range(3): #bull, bear, uncertain
        calc_arr=calc_arrs[nb_macro_mode]

        if ent_or_ex=="ent":
            arr=calc_arr[0:len_ent] 
        else:
            arr=calc_arr[len_ent:len_ent+len_ex]  

        for ii in range(len(arr)):
            if arr[ii]:
                t=all_t[ii]
                        
                if ents_raw is None:
                    ents_raw=t
                else:
                    ents_raw=ic.VBTOR.run(ents_raw,t).out
        
        #agregate the signals for different macro trends
        if nb_macro_mode==0:
            ent=VBTMACROFILTER.run(ents_raw,macro_trend,-1).out
        elif nb_macro_mode==1:
            ents_raw=VBTMACROFILTER.run(ents_raw,macro_trend,1).out
            ent=ic.VBTOR.run(ent, ents_raw).out
        else:
            ents_raw=VBTMACROFILTER.run(ents_raw,macro_trend,0).out
            ent=ic.VBTOR.run(ent, ents_raw).out                    
    
    return ent

def defi_nomacro(close,all_t,ent_or_ex, calc_arr):
    len_ent=7+len(BULL_PATTERNS)
    len_ex=7+len(BEAR_PATTERNS)
    ent=None

    if ent_or_ex=="ent":
        arr=calc_arr[0:len_ent] 
    else:
        arr=calc_arr[len_ent:len_ent+len_ex]  
    
    for ii in range(len(arr)):
        if arr[ii]:
            t=all_t[ii]
                    
            if ent is None:
                ent=t
            else:
                ent=ic.VBTOR.run(ent,t).out
                
    default=ic.VBTAND.run(ent, np.full(all_t[0].shape, False)).out #trick to keep the right shape
    return ent, default

#wrapper for the different strategy functions
def strat_wrapper_simple(open_,high, low, close, arr,
                        direction="long"):
   
    #calculate all signals and patterns, is a bit long
    all_t_ent, all_t_ex=defi_i(open_,high, low, close)
    
    #combine for the given array the signals and patterns
    ent, _=defi_nomacro(close,all_t_ent,"ent", arr)
    ex, default=defi_nomacro(close,all_t_ex,"ex", arr)

    if direction in ["long","both"]:
        entries=ent
        exits=ex
    else:
        entries=default
        exits=default
        
    if direction in ["both","short"]:
        entries_short=ex
        exits_short=ent
    else:
        entries_short=default
        exits_short=default

    return entries, exits, entries_short, exits_short

#not called from a IF, because it cannot interpret correctly the input arrays
def strat_wrapper_macro(open_,high, low, close, a_bull, a_bear, a_uncertain,
                        macro_trend_bull="long", macro_trend_bear="both",
                        macro_trend_uncertain="both",**kwargs):
    
    try:
        if kwargs.get("prd"):
            t=VBTMACROTRENDPRD.run(close)
        else:
            t=VBTMACROTREND.run(close)

        macro_trend=t.macro_trend
        min_ind=t.min_ind
        max_ind=t.max_ind
        
        #calculate all signals and patterns, is a bit long
        all_t_ent, all_t_ex=defi_i(open_,high, low, close)
        calc_arrs=[]
        
        calc_arrs.append(a_bull)
        calc_arrs.append(a_bear)
        calc_arrs.append(a_uncertain)
        
        #combine for the given array the signals and patterns
        ent=defi(close,all_t_ent,"ent", calc_arrs,macro_trend)
        ex=defi(close,all_t_ex,"ex", calc_arrs,macro_trend)
    
        t=VBTMACROMODE.run(ent,ex, macro_trend,\
                           macro_trend_bull=macro_trend_bull,
                           macro_trend_bear=macro_trend_bear,
                           macro_trend_uncertain=macro_trend_uncertain)
    
        return t.entries, t.exits, t.entries_short, t.exits_short, macro_trend, min_ind, max_ind  
    except Exception as msg:
        print(msg)
        print("exception in " + __name__)
        _, e_, exc_tb = sys.exc_info()
        print("line " + str(exc_tb.tb_lineno))
        print(msg)  

#wrapper for the different strategy functions
def strat_wrapper(open_,high, low, close, close_ind,
                f_bull="VBTSTOCHKAMA", f_bear="VBTSTOCHKAMA", f_uncertain="VBTSTOCHKAMA",
                f_very_bull="VBTSTOCHKAMA", f_very_bear="VBTSTOCHKAMA",
                trend_lim=1.5, trend_lim2=10, macro_trend_bool=False,macro_trend_bull="long", macro_trend_bear="short",
                macro_trend_uncertain="both",trend_key="bbands",macro_trend_index=False,light=True):
    
    macro_trend=np.full(close.shape, 0)  
    min_ind=np.full(close.shape, 0)   
    max_ind=np.full(close.shape, 0)   
    
    if macro_trend_bool:
        if macro_trend_index:
            macro_trend,min_ind, max_ind=major_int(close_ind)
        else:   
            macro_trend,min_ind, max_ind=major_int(close,threshold=0.03)
        
    if trend_key=="bbands":
        t=ic.VBTBBANDSTREND.run(close)
    else:
        t=ic.VBTMACDBBTREND.run(close)
        
    trend=t.trend
    kama=t.kama
    bb_bw=t.bb_bw
        
    ent_very_bull, ex_very_bull=function_to_res(f_very_bull,open_, high, low, close,light=light)
    
    ent_very_bear, ex_very_bear=function_to_res(f_very_bear, open_, high, low, close,light=light)
    ent_bull, ex_bull=function_to_res(f_bull,open_, high, low, close,light=light)
    ent_bear, ex_bear=function_to_res(f_bear, open_, high, low, close,light=light)
    ent_uncertain, ex_uncertain=function_to_res(f_uncertain, open_, high, low, close,light=light)

    temp_ent= np.full(close.shape, False)   
    temp_ex= np.full(close.shape, False)       
    entries= np.full(close.shape, False)   
    exits= np.full(close.shape, False)   
    entries_short= np.full(close.shape, False)   
    exits_short= np.full(close.shape, False)
    
    temp=2
    
    for ii in range(len(close)):
          if trend_lim!=100:
              if trend[ii]<=-trend_lim2:
                  temp_ent[ii] = ent_very_bull[ii]
                  temp_ex[ii] = ex_very_bull[ii] 
              elif trend[ii]>=trend_lim2:
                  temp_ent[ii] = ent_very_bear[ii]
                  temp_ex[ii] = ex_very_bear[ii]                   
              elif trend[ii]<-trend_lim:
                  temp_ent[ii] = ent_bull[ii]
                  temp_ex[ii] = ex_bull[ii] 
              elif trend[ii]>trend_lim:
                  temp_ent[ii] = ent_bear[ii]
                  temp_ex[ii] = ex_bear[ii]
              else:
                  temp_ent[ii] = ent_uncertain[ii]    
                  temp_ex[ii] = ex_uncertain[ii]  
          else:
              temp_ent[ii] = ent_uncertain[ii]    
              temp_ex[ii] = ex_uncertain[ii]  

          if macro_trend_bool:
              if macro_trend[ii]==-1:
                  if (temp!=0 and macro_trend_bull not in ["both", "short"]):
                      exits_short[ii] = True
                  if (temp!=0 and macro_trend_bull not in ["both", "long"]):
                      exits[ii] = True

                  if macro_trend_bull in ["both", "short"]:
                      entries_short[ii] = temp_ex[ii]
                      exits_short[ii] = temp_ent[ii] 
                      
                  if macro_trend_bull in ["both", "long"]:
                      entries[ii] = temp_ent[ii]
                      exits[ii] = temp_ex[ii]

                  temp=0
                  
              elif macro_trend[ii]==1:
                  if (temp!=1 and macro_trend_bear not in ["both", "short"]):
                      exits_short[ii] = True
                  if (temp!=1 and macro_trend_bear not in ["both", "long"]):
                      exits[ii] = True

                  if macro_trend_bear in ["both", "short"]:
                      entries_short[ii] = temp_ex[ii]
                      exits_short[ii] = temp_ent[ii] 
                      
                  if macro_trend_bear in ["both", "long"]:
                      entries[ii] = temp_ent[ii]
                      exits[ii] = temp_ex[ii]

                  temp=1
              else:
                  if (temp!=2 and macro_trend_uncertain not in ["both", "short"]):
                      exits_short[ii] = True
                  if (temp!=2 and macro_trend_uncertain not in ["both", "long"]):
                      exits[ii] = True
                  
                  if macro_trend_uncertain in ["both", "short"]:
                      entries_short[ii] = temp_ex[ii]
                      exits_short[ii] = temp_ent[ii] 
                      
                  if macro_trend_uncertain in ["both", "long"]:
                      entries[ii] = temp_ent[ii]
                      exits[ii] = temp_ex[ii]                  

                  temp=2
          else: #no macro trend
              if macro_trend_uncertain in ["both", "short"]:
                  entries_short[ii] = temp_ex[ii]
                  exits_short[ii] = temp_ent[ii] 
                
              if macro_trend_uncertain in ["both", "long"]:
                  entries[ii] = temp_ent[ii]
                  exits[ii] = temp_ex[ii]    
     
    return entries, exits, entries_short, exits_short, trend, macro_trend, kama, bb_bw, min_ind, max_ind  
  
STRATWRAPPER = vbt.IF(
     class_name='StratWrapper',
     short_name='st_wrapper',
     input_names=['high', 'low', 'close','open_','close_ind'],
     param_names=['f_bull', 'f_bear', 'f_uncertain','f_very_bull', 'f_very_bear','trend_lim', 
                  'trend_lim2', 
                  'macro_trend_bool','macro_trend_bull',
                  'macro_trend_bear','macro_trend_uncertain','trend_key','macro_trend_index'],
     output_names=['entries', 'exits', 'entries_short', 'exits_short','trend','macro_trend',
                   'kama','bb_bw','min_ind', 'max_ind'] 
).with_apply_func(
     strat_wrapper, 
     takes_1d=True, 
     trend_lim=1.5,
     trend_lim2=10,
     macro_trend_bool=False,
     macro_trend_bull="long", 
     macro_trend_bear="short",
     macro_trend_uncertain="both",
     f_bull="VBTSTOCHKAMA", 
     f_bear="VBTSTOCHKAMA", 
     f_uncertain="VBTSTOCHKAMA",
     f_very_bull="VBTSTOCHKAMA", 
     f_very_bear="VBTSTOCHKAMA", 
     trend_key="bbands",
     macro_trend_index=False,
     light=True
)    

### For backtesting ###
class Strat(VBTfunc):
    def __init__(self,symbol_index,period,suffix,**kwargs):
        super().__init__(symbol_index,period)
        
        if kwargs.get("index",False):
            #self.only_index=True
            self.close=self.close_ind
            self.open=self.open_ind
            self.low=self.low_ind
            self.high=self.high_ind
        else:
            #self.only_index=False
            self.symbols_simple=self.close.columns.values
        self.suffix="_" + suffix
        
    def get_output(self,s):
        self.entries=s.entries
        self.exits=s.exits
        self.entries_short=s.entries_short
        self.exits_short=s.exits_short
        self.trend=s.trend
        self.kama=s.kama
        self.bb_bw=s.bb_bw
        self.macro_trend=s.macro_trend
        self.max_ind=s.max_ind
        self.min_ind=s.min_ind
  
    def symbols_simple_to_complex(self,symbol_simple,ent_or_ex):
        if ent_or_ex=="ent":
            self.symbols_complex=self.entries.columns.values
        else:
            self.symbols_complex=self.exits.columns.values
        
        for ii, e in enumerate(self.symbols_complex):
            if e[-1]==symbol_simple: #9
                return e
 
    def save(self):
        save_vbt_both(self.close, 
                 self.entries, 
                 self.exits, 
                 self.entries_short,
                 self.exits_short,                  
                 suffix=self.suffix
                 )

    def get_return(self,**kwargs):
        pf=vbt.Portfolio.from_signals(self.close, 
                                      entries =self.entries,
                                      exits =  self.exits,
                                      short_entries=self.entries_short,
                                      short_exits  =self.exits_short,
                                      upon_opposite_entry="Reverse"
                                      )
        #benchmark_return makes sense only for bull
        delta=pf.total_return().values[0]
        return delta

########## Strats ##############
# Example of simple strategy for pedagogic purposes
    def stratRSI(self,**kwargs):
        t=vbt.RSI.run(close,wtype='simple')
        self.entries=t.rsi_crossed_below(20)
        self.exits=t.rsi_crossed_above(80)
        t2=ic.VBTFALSE.run(close)
        self.entries_short=t2.entries
        self.exits_short=t2.entries
        
    def stratRSIeq(self,**kwargs):
        a=[0., 0., 0., 0., 0., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
       0., 0., 0., 0., 0., 
           0., 0., 0., 0., 0., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 
       0., 0., 0., 0., 0.]

        self.entries, self.exits, self.entries_short, self.exits_short= \
        strat_wrapper_simple(
                            self.open,
                            self.high, 
                            self.low,
                            self.close,
                            #self.close_ind,
                            a)     
        

# The best strategy without macro is hold, here strat D bear is acceptable and provides some signals
# to define pattern light
    def stratDbear(self,**kwargs):
        a=[0., 0., 0., 0., 0., 0., 1., 0., 1., 0., 0., 0., 0., 1., 1., 0., 0.,
       0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 1., 0., 0., 0., 0., 0., 0.,
       0., 1., 0., 0., 0., 0., 0., 0., 1., 0.]


        self.entries, self.exits, self.entries_short, self.exits_short= \
        strat_wrapper_simple(
                            self.open,
                            self.high, 
                            self.low,
                            self.close,
                            #self.close_ind,
                            a)
        
    def stratReal(self,**kwargs):
        a_bull=[1., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 1., 0., 1., 0., 0.,
       1., 0., 0., 0., 0., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
       1., 0., 0., 0., 0., 0., 0., 0., 0., 0.]
        a_bear=[1., 1., 0., 0., 0., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
       0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
       1., 0., 0., 0., 0., 1., 0., 0., 0., 0.]
        a_uncertain= [1., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
       0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 1.,
       1., 0., 0., 0., 0., 1., 0., 1., 1., 0.]
        
        self.entries, self.exits, self.entries_short, self.exits_short, \
        self.macro_trend, self.min_ind, self.max_ind=\
        strat_wrapper_macro(
                            self.open,
                            self.high, 
                            self.low,
                            self.close,
                            #self.close_ind,
                            a_bull, 
                            a_bear, 
                            a_uncertain,
                            **kwargs)        

    def stratDiv(self,**kwargs):
        
        #optimal with fee 0,0005
        a=[0., 0., 0., 0., 0., 0., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
       0., 0., 0., 0., 0., 0., 0., 0., 1., 1., 0., 0., 0., 0., 0., 1., 1.,
       1., 0., 1., 0., 0., 0., 0., 1., 0., 0.]
        
        #optimal with fee 0,0001
       # a=[0., 0., 0., 0., 0., 0., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
       # 0., 0., 0., 0., 0., 0., 1., 0., 0., 1., 1., 0., 0., 0., 0., 0.,
        #1., 1., 1., 0., 0., 0., 0., 0., 0., 1., 0., 0.]

        self.entries, self.exits, self.entries_short, self.exits_short= \
        strat_wrapper_simple(
                            self.open,
                            self.high, 
                            self.low,
                            self.close,
                            #self.close_ind,
                            a)

        
    def stratTestSimple(self,**kwargs):
        a=[0., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
       0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 1., 0., 0., 0., 0., 0., 0.,
       0., 0., 0., 0., 0., 0., 0., 0., 0., 0.]


        self.entries, self.exits, self.entries_short, self.exits_short= \
        strat_wrapper_simple(
                            self.open,
                            self.high, 
                            self.low,
                            self.close,
                            #self.close_ind,
                            a)
#In long/both/both, on period 2007-2022, CAC40 return 5.26 (bench 2.26), DAX xy (2.66), NASDAQ xy (17.2)  


    def stratD(self,**kwargs):
        a_bull= [1., 0., 0., 0., 0., 1., 0., 0., 1., 0., 0., 0., 0., 1., 1., 0.,
        1., 0., 0., 1., 0., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
        0., 0., 0., 0., 1., 0., 0., 0., 0., 0., 0., 0.]
        a_bear= [0., 0., 0., 0., 0., 0., 1., 0., 1., 0., 0., 0., 0., 1., 1., 0.,
        0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 1., 0., 0., 0., 0.,
        0., 0., 0., 1., 0., 0., 0., 0., 0., 0., 1., 0.]
        a_uncertain= [0., 0., 1., 0., 0., 1., 0., 0., 1., 0., 0., 1., 0., 1., 0., 1.,
        1., 1., 1., 1., 0., 0., 0., 0., 1., 0., 0., 0., 0., 0., 0., 0.,
        0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.]
        
        self.entries, self.exits, self.entries_short, self.exits_short, \
        self.macro_trend, self.min_ind, self.max_ind=\
        strat_wrapper_macro(
                            self.open,
                            self.high, 
                            self.low,
                            self.close,
                            #self.close_ind,
                            a_bull, 
                            a_bear, 
                            a_uncertain,
                            **kwargs)
        
#In long/both/both, on period 2007-2022, CAC40 return 4.35 (bench 2.26), DAX xy (2.66), NASDAQ xy (17.2)      

    def stratE(self,**kwargs):
        a_bull=[0., 1., 0., 0., 0., 0., 0., 0., 1., 0., 0., 1., 0., 0., 0., 0.,
        1., 1., 1., 0., 0., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
        0., 0., 1., 0., 0., 0., 0., 0., 1., 0., 0., 0.]
        a_bear= [0., 0., 0., 0., 0., 0., 0., 0., 1., 1., 0., 0., 0., 0., 0., 0.,
         0., 0., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
         0., 0., 0., 1., 0., 0., 0., 0., 1., 0., 1., 0.]
        a_uncertain=  [1., 0., 0., 0., 0., 1., 0., 0., 1., 1., 0., 1., 1., 1., 0., 0.,
         0., 0., 0., 0., 0., 0., 0., 0., 1., 0., 0., 0., 0., 0., 0., 0.,
         0., 0., 1., 1., 0., 0., 1., 1., 0., 0., 0., 0.]
        
        self.entries, self.exits, self.entries_short, self.exits_short, \
        self.macro_trend, self.min_ind, self.max_ind=\
        strat_wrapper_macro(
                            self.open,
                            self.high, 
                            self.low,
                            self.close,
                            #self.close_ind,
                            a_bull, 
                            a_bear, 
                            a_uncertain,
                            **kwargs) 

    def stratF(self,**kwargs):
        a_bull=[0., 0., 0., 0., 0., 1., 1., 0., 0., 1., 0., 1., 1., 1., 0., 1.,
            1., 0., 0., 0., 1., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
            0., 0., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0.]
        a_bear= [0., 1., 0., 0., 0., 0., 0., 0., 0., 1., 0., 0., 0., 0., 0., 1.,
         0., 0., 0., 0., 0., 1., 0., 0., 0., 1., 1., 0., 0., 0., 0., 0.,
         1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.]
        a_uncertain=  [0., 1., 1., 0., 0., 0., 0., 0., 0., 1., 0., 0., 1., 0., 0., 0.,
         0., 0., 1., 0., 0., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
         0., 1., 0., 1., 0., 0., 0., 0., 0., 1., 0., 0.]
        
        self.entries, self.exits, self.entries_short, self.exits_short, \
        self.macro_trend, self.min_ind, self.max_ind=\
        strat_wrapper_macro(
                            self.open,
                            self.high, 
                            self.low,
                            self.close,
                            #self.close_ind,
                            a_bull, 
                            a_bear, 
                            a_uncertain,
                            **kwargs) 
    
    def stratIndex(self,**kwargs):
        a_bull=[1., 0., 0., 1., 0., 0., 1., 0., 0., 0., 0., 0., 1., 1., 0., 0., 1.,
       0., 0., 0., 0., 0., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
       0., 1., 0., 0., 0., 0., 0., 1., 0., 0.]
        a_bear=[1., 0., 0., 0., 0., 1., 0., 0., 0., 0., 0., 0., 1., 1., 0., 0., 0.,
       0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 1.,
       0., 0., 0., 0., 1., 0., 0., 0., 1., 0.]
        a_uncertain=[1., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 1., 0., 1., 0., 0.,
       0., 1., 0., 0., 0., 0., 0., 0., 1., 0., 0., 0., 0., 0., 0., 0., 1.,
       0., 0., 1., 0., 0., 0., 1., 0., 0., 0.]
        
        self.entries, self.exits, self.entries_short, self.exits_short, \
        self.macro_trend, self.min_ind, self.max_ind=\
        strat_wrapper_macro(
                            self.open,
                            self.high, 
                            self.low,
                            self.close,
                            #self.close_ind,
                            a_bull, 
                            a_bear, 
                            a_uncertain,
                            **kwargs)       
        
############## Strategies below are widely deprecated ##############

#### No trend at all

    #Use the kama extremum and the STOCH (20/80) to determine entries and exits
    def strat_kama_stoch(self,**kwargs): 
        s = STRATWRAPPER.run(self.open,
                             self.high, 
                             self.low,
                             self.close,
                             self.close_ind,
                             trend_lim=100,
                             macro_trend_bool=False,
                             macro_trend_uncertain=kwargs.get("macro_trend_uncertain","long"),
                             f_uncertain="VBTSTOCHKAMA",
                             )
        self.get_output(s)
        
    #Use candlelight pattern to determine entries and exits        
    def strat_pattern_light(self,**kwargs): 

        s = STRATWRAPPER.run(self.open,
                             self.high, 
                             self.low,
                             self.close,
                             self.close_ind,
                             trend_lim=100,
                             macro_trend_bool=False,
                             macro_trend_uncertain=kwargs.get("macro_trend_uncertain","long"),
                             f_uncertain="VBTPATTERN",
                             )
        self.get_output(s)
        
#### No macro trend ####
    # As strat_kama_stoch for bear and uncertain trend
    # Use MA for bull, so if the 5 days smoothed price crosses the 15 days smoothed price, a signal is created
    def strat_kama_stoch_matrend_bbands(self,**kwargs): #ex strat11
        s = STRATWRAPPER.run(self.open,
                             self.high, 
                             self.low,
                             self.close,
                             self.close_ind,
                             trend_lim=1.5,
                             macro_trend_bool=False,
                             macro_trend_uncertain=kwargs.get("macro_trend_uncertain","long"),
                             f_bull="VBTMA",
                             f_bear="VBTSTOCHKAMA",
                             f_uncertain="VBTSTOCHKAMA",
                             f_very_bull="VBTMA",
                             f_very_bear="VBTSTOCHKAMA",
                             trend_key="bbands")
        self.get_output(s)
       
    # As strat_kama_stoch_matrend_bbands, but in addition to MA use also supertrend when bull
    def strat_kama_stoch_super_bbands(self,**kwargs): 
        s = STRATWRAPPER.run(self.open,
                             self.high, 
                             self.low,
                             self.close,
                             self.close_ind,
                             trend_lim=1.5,
                             macro_trend_bool=False,
                             macro_trend_uncertain=kwargs.get("macro_trend_uncertain","long"),
                             f_bull="VBTSUPERTRENDMA",
                             f_bear="VBTSTOCHKAMA",
                             f_uncertain="VBTSTOCHKAMA",
                             f_very_bull="VBTSUPERTRENDMA",
                             f_very_bear="VBTSTOCHKAMA",                             
                             trend_key="bbands")
        self.get_output(s)
        
    #Same as strat_kama_stoch_matrend_bbands but with different trend calculation
    def strat_kama_stoch_matrend_macdbb(self,**kwargs): 
        s = STRATWRAPPER.run(self.open,
                             self.high, 
                             self.low,
                             self.close,
                             self.close_ind,
                             trend_lim=1.5,
                             macro_trend_bool=False,
                             macro_trend_uncertain=kwargs.get("macro_trend_uncertain","long"),
                             f_bull="VBTMA",
                             f_bear="VBTSTOCHKAMA",
                             f_uncertain="VBTSTOCHKAMA",
                             f_very_bull="VBTMA",
                             f_very_bear="VBTSTOCHKAMA",                             
                             trend_key="macdbb")
        self.get_output(s)
        
    #Same as strat_kama_stoch_super_bbands but with different trend calculation
    def strat_kama_stoch_super_macdbb(self,**kwargs): 
        s = STRATWRAPPER.run(self.open,
                             self.high, 
                             self.low,
                             self.close,
                             self.close_ind,
                             trend_lim=1.5,
                             macro_trend_bool=False,
                             macro_trend_uncertain=kwargs.get("macro_trend_uncertain","long"),
                             f_bull="VBTSUPERTRENDMA",
                             f_bear="VBTSTOCHKAMA",
                             f_uncertain="VBTSTOCHKAMA",
                             f_very_bull="VBTSUPERTRENDMA",
                             f_very_bear="VBTSTOCHKAMA",                              
                             trend_key="macdbb")
        self.get_output(s)
    
    #strat_pattern_light for bear and uncertain trends
    #MA for bull
    def strat_pattern_light_matrend_bbands(self,**kwargs): 
        s = STRATWRAPPER.run(self.open,
                             self.high, 
                             self.low,
                             self.close,
                             self.close_ind,
                             trend_lim=1.5,
                             macro_trend_bool=False,
                             macro_trend_uncertain=kwargs.get("macro_trend_uncertain","long"),
                             f_bull="VBTMA",
                             f_bear="VBTPATTERN",
                             f_uncertain="VBTPATTERN",
                             f_very_bull="VBTMA",
                             f_very_bear="VBTPATTERN",                             
                             trend_key="bbands")
        self.get_output(s)
        
    #strat_pattern_light for bear and uncertain trends
    #MA+Supertrend for bull        
    def strat_pattern_light_super_bbands(self,**kwargs): 
        s = STRATWRAPPER.run(self.open,
                             self.high, 
                             self.low,
                             self.close,
                             self.close_ind,
                             trend_lim=1.5,
                             macro_trend_bool=False,
                             macro_trend_uncertain=kwargs.get("macro_trend_uncertain","long"),
                             f_bull="VBTSUPERTRENDMA",
                             f_bear="VBTPATTERN",
                             f_uncertain="VBTPATTERN",
                             f_very_bull="VBTSUPERTRENDMA",
                             f_very_bear="VBTPATTERN",                             
                             trend_key="bbands")
        self.get_output(s)
        
    #strat_pattern_light for bear and uncertain trends
    #MA+Supertrend for bull
    #if the trend is extremely strong, no entries or respectively no exits take place
    def strat_careful_super_bbands(self,**kwargs): 
        s = STRATWRAPPER.run(self.open,
                             self.high, 
                             self.low,
                             self.close,
                             self.close_ind,
                             trend_lim=1.5,
                             macro_trend_bool=False,
                             macro_trend_uncertain=kwargs.get("macro_trend_uncertain","long"),
                             f_bull="VBTSUPERTRENDMA",
                             f_bear="VBTPATTERN",
                             f_uncertain="VBTPATTERN",
                             f_very_bull="VBTVERYBULL",
                             f_very_bear="VBTVERYBEAR",                             
                             trend_key="bbands")
        self.get_output(s)
     
    #As strat_pattern_light_matrend_bbands but with different trend calculation
    def strat_pattern_light_matrend_macdbb(self,**kwargs): 
        s = STRATWRAPPER.run(self.open,
                             self.high, 
                             self.low,
                             self.close,
                             self.close_ind,
                             trend_lim=1.5,
                             macro_trend_bool=False,
                             macro_trend_uncertain=kwargs.get("macro_trend_uncertain","long"),
                             f_bull="VBTMA",
                             f_bear="VBTPATTERN",
                             f_uncertain="VBTPATTERN",
                             f_very_bull="VBTMA",
                             f_very_bear="VBTPATTERN",
                             trend_key="macdbb")
        self.get_output(s)
    
    #As strat_pattern_light_super_bbands but with different trend calculation
    def strat_pattern_light_super_macdbb(self,**kwargs): 
        s = STRATWRAPPER.run(self.open,
                             self.high, 
                             self.low,
                             self.close,
                             self.close_ind,
                             trend_lim=1.5,
                             macro_trend_bool=False,
                             macro_trend_uncertain=kwargs.get("macro_trend_uncertain","long"),
                             f_bull="VBTSUPERTRENDMA",
                             f_bear="VBTPATTERN",
                             f_uncertain="VBTPATTERN",
                             f_very_bull="VBTSUPERTRENDMA",
                             f_very_bear="VBTPATTERN",
                             trend_key="macdbb")
        self.get_output(s)  
        
### With macro trend ###    

    #As strat_kama_stoch_matrend_bbands but the short/long is determined by macro trend
    def strat_kama_stoch_matrend_bbands_macro(self,**kwargs): 
        s = STRATWRAPPER.run(self.open,
                             self.high, 
                             self.low,
                             self.close,
                             self.close_ind,
                             trend_lim=1.5,
                             macro_trend_bool=True,
                             macro_trend_bull=kwargs.get("macro_trend_bull","long"), 
                             macro_trend_bear=kwargs.get("macro_trend_bear","short"),
                             macro_trend_uncertain=kwargs.get("macro_trend_uncertain","long"),
                             f_bull="VBTMA",
                             f_bear="VBTSTOCHKAMA",
                             f_uncertain="VBTSTOCHKAMA",
                             f_very_bull="VBTMA",
                             f_very_bear="VBTSTOCHKAMA",                             
                             trend_key="bbands",
                             macro_trend_index=kwargs.get("macro_trend_index",False))
        self.get_output(s)
        
    #As strat_kama_stoch_matrend_macdbb but the short/long is determined by macro trend
    def strat_kama_stoch_matrend_macdbb_macro(self,**kwargs): 
        s = STRATWRAPPER.run(self.open,
                             self.high, 
                             self.low,
                             self.close,
                             self.close_ind,
                             trend_lim=1.5,
                             macro_trend_bool=True,
                             macro_trend_bull=kwargs.get("macro_trend_bull","long"), 
                             macro_trend_bear=kwargs.get("macro_trend_bear","short"),
                             macro_trend_uncertain=kwargs.get("macro_trend_uncertain","long"),
                             f_bull="VBTMA",
                             f_bear="VBTSTOCHKAMA",
                             f_uncertain="VBTSTOCHKAMA",
                             f_very_bull="VBTMA",
                             f_very_bear="VBTSTOCHKAMA",                             
                             trend_key="macdbb",
                             macro_trend_index=kwargs.get("macro_trend_index",False))
        self.get_output(s)
        
    #As strat_kama_stoch but the short/long is determined by macro trend
    def strat_kama_stoch_macro(self,**kwargs):
        s = STRATWRAPPER.run(self.open,
                             self.high, 
                             self.low,
                             self.close,
                             self.close_ind,
                             trend_lim=100,
                             macro_trend_bool=True,
                             macro_trend_bull=kwargs.get("macro_trend_bull","long"), 
                             macro_trend_bear=kwargs.get("macro_trend_bear","short"),
                             macro_trend_uncertain=kwargs.get("macro_trend_uncertain","long"),
                             f_uncertain="VBTSTOCHKAMA",
                             macro_trend_index=kwargs.get("macro_trend_index",False)
                             )
        self.get_output(s)
    
    #As strat_pattern_light but the short/long is determined by macro trend
    def strat_pattern_light_macro(self,**kwargs):
        s = STRATWRAPPER.run(self.open,
                             self.high, 
                             self.low,
                             self.close,
                             self.close_ind,
                             trend_lim=100,
                             macro_trend_bool=True,
                             macro_trend_bull=kwargs.get("macro_trend_bull","long"), 
                             macro_trend_bear=kwargs.get("macro_trend_bear","short"),
                             macro_trend_uncertain=kwargs.get("macro_trend_uncertain","long"),
                             f_uncertain="VBTPATTERN",
                             macro_trend_index=kwargs.get("macro_trend_index",False)
                             )
        self.get_output(s)    
        
        
        

        
