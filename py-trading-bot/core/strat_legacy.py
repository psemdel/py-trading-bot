#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jan 28 21:48:08 2023

@author: maxime
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat May 14 22:36:16 2022

@author: maxime
"""
import vectorbtpro as vbt
import numpy as np


import core.indicators as ic
from core.macro import VBTMACROFILTER, VBTMACROMODE, VBTMACROTREND, VBTMACROTRENDPRD
from core.constants import BEAR_PATTERNS, BULL_PATTERNS
from core.strat import Strat, STRATWRAPPER
import logging
logger = logging.getLogger(__name__)
### Strategies on one action, no preselection ###
#These functions are either not anymore actual or there for comparison purpose between optimisation and production application



#Convert a binary array intro entries and exits
#Long but better for optimisation as you calculate everything once and then you stop calculating
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
    except Exception as e:
        logger.error(e, stack_info=True, exc_info=True)
        
def defi(close,all_t,ent_or_ex, calc_arrs,macro_trend):
    len_ent=7+len(BULL_PATTERNS)
    len_ex=7+len(BEAR_PATTERNS)
    #ents_raw=None 
    
    for nb_macro_mode in range(3): #bull, bear, uncertain
        ents_raw=None   #if missing it is a mistake, but the strategy have been elaborated without!!
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
       

#not called from a IF, because it cannot interpret correctly the input arrays
#for optimization only
def strat_wrapper_macro_legacy(open_,high, low, close, a_bull, a_bear, a_uncertain,
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
    
        #put both/long/short
        t=VBTMACROMODE.run(ent,ex, macro_trend,\
                           macro_trend_bull=macro_trend_bull,
                           macro_trend_bear=macro_trend_bear,
                           macro_trend_uncertain=macro_trend_uncertain)
    
        return t.entries, t.exits, t.entries_short, t.exits_short, macro_trend, min_ind, max_ind  
    except Exception as e:
        logger.error(e, stack_info=True, exc_info=True) 

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
def strat_wrapper_simple_legacy(open_,high, low, close, arr,
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



### For backtesting ###
class StratLegacy(Strat):
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
        
        
        

        
