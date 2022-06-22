#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat May 14 22:36:16 2022

@author: maxime
"""
import vectorbtpro as vbt
import numpy as np
import math

import inspect
import talib

from core.common import VBTfunc, save_vbt_both
import core.indicators as ic

### Strategies on one action, no preselection ###
#So it determines entries and exits for one action to optimize the return

## only 1d
def ext_major(close):
    kama=talib.KAMA(close,timeperiod=30)
    
    threshold=0.03
    ll=1-threshold
    lu=1+threshold
    window=150
    deadband=0.1

    macro_trend= np.full(kama.shape, 0)
    macro_trend_raw= np.full(kama.shape, 0)
    max_ind= np.full(kama.shape, 0)
    min_ind= np.full(kama.shape, 0)
    
    ext=[]
    ext_bot=[]
    max_arr=[]
    min_arr=[]
    
    for ii in range(2,len(kama)):
        win_start=max(0,ii-window)
        win_end=ii  #min(len(self.res),ii)
        change=0

        if not math.isnan(kama[win_start]) and not math.isnan(kama[win_end]):
            maximum=np.max(kama[win_start:win_end+1])
            ind=win_start+np.argmax(kama[win_start:win_end+1])
            
            if ind==win_start:
                local_min=kama[win_start]
            else:
                local_min=np.min(kama[win_start:ind])
           
            minimum=np.min(kama[win_start:win_end+1])
            ind_bot=win_start+np.argmin(kama[win_start:win_end+1]) 

            if ind_bot==win_start:
                local_max=kama[win_start]
            else:
                local_max=np.max(kama[win_start:ind_bot])

            if local_min<ll*maximum and kama[win_end]<ll*maximum:
                if ind not in ext:
                    ext.append(ind)
                    max_arr.append(maximum)
                    change=1
                    macro_trend_raw[ii]=1
                    if ii > len(kama)-2: #for alerting
                        max_ind[-1]=ind
            
            if local_max>lu*minimum and kama[win_end]>lu*minimum:
                if ind_bot not in ext_bot:
                    ext_bot.append(ind_bot)  
                    min_arr.append(minimum)
                    change=1
                    macro_trend_raw[ii]=-1
                    if ii > len(kama)-2: #for alerting
                        min_ind[-1]=ind
   
        if change==0:
            macro_trend_raw[ii]=macro_trend_raw[ii-1]
        macro_trend[ii]=macro_trend_raw[ii]
            
        if deadband!=0:
            #the max or min were exceeded, correction of the direction
            if macro_trend[ii]==1 and kama[ii]>max_arr[-1]:
                macro_trend[ii]=-1
            elif macro_trend[ii]==-1 and kama[ii]<min_arr[-1]:
                macro_trend[ii]=1
            #uncertain, as in a small band around the min/max
            elif macro_trend[ii]==1 and kama[ii]/max_arr[-1]>(1-deadband):
                macro_trend[ii]=0
            elif macro_trend[ii]==-1 and kama[ii]/min_arr[-1]<(1+deadband):
                macro_trend[ii]=0
            
    return macro_trend, min_ind, max_ind

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

def strat_wrapper(high, low, close, open_, close_ind,
                f_bull="VBTSTOCHKAMA", f_bear="VBTSTOCHKAMA", f_uncertain="VBTSTOCHKAMA",
                f_very_bull="VBTSTOCHKAMA", f_very_bear="VBTSTOCHKAMA",
                trend_lim=1.5, trend_lim2=10, macro_trend_bool=False,macro_trend_bull="long", macro_trend_bear="short",
                macro_trend_uncertain="both",trend_key="bbands",macro_trend_index=False,light=True):
    
    macro_trend=np.full(close.shape, 0)  
    min_ind=np.full(close.shape, 0)   
    max_ind=np.full(close.shape, 0)   
    
    if macro_trend_bool:
        if macro_trend_index:
            macro_trend,min_ind, max_ind=ext_major(close_ind)
        else:   
            macro_trend,min_ind, max_ind=ext_major(close)
        
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
    
VBTMACROTREND = vbt.IF(
     class_name='MacroTrend',
     short_name='macro_trend',
     input_names=[ 'close'],
     output_names=['macro_trend','min_ind', 'max_ind']
).with_apply_func(
     ext_major, 
     takes_1d=True, 
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
        self.macro_trend=s.macro_trend
        self.kama=s.kama
        self.bb_bw=s.bb_bw
        self.max_ind=s.max_ind
        self.min_ind=s.min_ind

    def symbols_simple_to_complex(self,symbol_simple):
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
#### No trend at all
    def strat_kama_stoch(self,**kwargs): 
        s = STRATWRAPPER.run(self.high, 
                             self.low,
                             self.close,
                             self.open,
                             self.close_ind,
                             trend_lim=100,
                             macro_trend_bool=False,
                             macro_trend_uncertain=kwargs.get("macro_trend_uncertain","long"),
                             f_uncertain="VBTSTOCHKAMA",
                             )
        self.get_output(s)
        
    def strat_pattern_light(self,**kwargs): 

        s = STRATWRAPPER.run(self.high, 
                             self.low,
                             self.close,
                             self.open,
                             self.close_ind,
                             trend_lim=100,
                             macro_trend_bool=False,
                             macro_trend_uncertain=kwargs.get("macro_trend_uncertain","long"),
                             f_uncertain="VBTPATTERN",
                             )
        self.get_output(s)
        
#### No macro trend ####
    def strat_kama_stoch_matrend_bbands(self,**kwargs): #ex strat11
        s = STRATWRAPPER.run(self.high, 
                             self.low,
                             self.close,
                             self.open,
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
        
    def strat_kama_stoch_super_bbands(self,**kwargs): 
        s = STRATWRAPPER.run(self.high, 
                             self.low,
                             self.close,
                             self.open,
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
        
    def strat_kama_stoch_matrend_macdbb(self,**kwargs): 
        s = STRATWRAPPER.run(self.high, 
                             self.low,
                             self.close,
                             self.open,
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
        
    def strat_kama_stoch_super_macdbb(self,**kwargs): 
        s = STRATWRAPPER.run(self.high, 
                             self.low,
                             self.close,
                             self.open,
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
        
    def strat_pattern_light_matrend_bbands(self,**kwargs): 
        s = STRATWRAPPER.run(self.high, 
                             self.low,
                             self.close,
                             self.open,
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
        
    def strat_pattern_light_super_bbands(self,**kwargs): 
        s = STRATWRAPPER.run(self.high, 
                             self.low,
                             self.close,
                             self.open,
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
        
    def strat_careful_super_bbands(self,**kwargs): 
        s = STRATWRAPPER.run(self.high, 
                             self.low,
                             self.close,
                             self.open,
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
        
    def strat_pattern_light_matrend_macdbb(self,**kwargs): 
        s = STRATWRAPPER.run(self.high, 
                             self.low,
                             self.close,
                             self.open,
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
        
    def strat_pattern_light_super_macdbb(self,**kwargs): 
        s = STRATWRAPPER.run(self.high, 
                             self.low,
                             self.close,
                             self.open,
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
    def strat_kama_stoch_matrend_bbands_macro(self,**kwargs): 
        s = STRATWRAPPER.run(self.high, 
                             self.low,
                             self.close,
                             self.open,
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
        
    def strat_kama_stoch_matrend_macdbb_macro(self,**kwargs): 
        s = STRATWRAPPER.run(self.high, 
                             self.low,
                             self.close,
                             self.open,
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
    def strat_kama_stoch_macro(self,**kwargs):
        s = STRATWRAPPER.run(self.high, 
                             self.low,
                             self.close,
                             self.open,
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
        
    def strat_pattern_light_macro(self,**kwargs):
        s = STRATWRAPPER.run(self.high, 
                             self.low,
                             self.close,
                             self.open,
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
        
        
        

        