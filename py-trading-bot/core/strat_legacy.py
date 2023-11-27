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
import numbers
from core.strat import UnderlyingStrat, STRATWRAPPER
import logging
logger = logging.getLogger(__name__)
"""
Strategies on one action, no preselection

Complement to Strat
"""
class StratKamaStoch(UnderlyingStrat):  
    '''
    Use the kama extremum and the STOCH (20/80) to determine entries and exits
    '''
    def __init__(self,
                 period: numbers.Number,
                 dir_uncertain: str="long",
                 **kwargs):
        super().__init__(period,**kwargs)
        for k in ["dir_uncertain"]:
            setattr(self,k,locals()[k])
    
    def run(self):
        s = STRATWRAPPER.run(self.open,
                             self.high, 
                             self.low,
                             self.close,
                             self.close_ind,
                             trend_lim=100,
                             macro_trend_bool=False,
                             dir_uncertain=self.dir_uncertain,
                             f_uncertain="VBTSTOCHKAMA",
                             )
        self.get_output(s)  

       
#### No macro trend ####
class StratKamaStochSuperBbands(UnderlyingStrat):  
    '''
    As strat_kama_stoch_matrend_bbands, but in addition to MA use also supertrend when bull
    '''
    def __init__(self,
                 period: numbers.Number,
                 dir_uncertain: str="long",
                 **kwargs):
        super().__init__(period,**kwargs)
        for k in ["dir_uncertain"]:
            setattr(self,k,locals()[k])
    
    def run(self):
        s = STRATWRAPPER.run(self.open,
                             self.high, 
                             self.low,
                             self.close,
                             self.close_ind,
                             trend_lim=1.5,
                             macro_trend_bool=False,
                             dir_uncertain=self.dir_uncertain,
                             f_bull="VBTSUPERTRENDMA",
                             f_bear="VBTSTOCHKAMA",
                             f_uncertain="VBTSTOCHKAMA",
                             f_very_bull="VBTSUPERTRENDMA",
                             f_very_bear="VBTSTOCHKAMA",                             
                             trend_key="bbands")
        self.get_output(s) 

class StratKamaStochMatrendMacdbb(UnderlyingStrat):  
    '''
    Same as strat_kama_stoch_matrend_bbands but with different trend calculation
    '''
    def __init__(self,
                 period: numbers.Number,
                 dir_uncertain: str="long",
                 **kwargs):
        super().__init__(period,**kwargs)
        for k in ["dir_uncertain"]:
            setattr(self,k,locals()[k])
    
    def run(self):
        s = STRATWRAPPER.run(self.open,
                             self.high, 
                             self.low,
                             self.close,
                             self.close_ind,
                             trend_lim=1.5,
                             macro_trend_bool=False,
                             dir_uncertain=self.dir_uncertain,
                             f_bull="VBTMA",
                             f_bear="VBTSTOCHKAMA",
                             f_uncertain="VBTSTOCHKAMA",
                             f_very_bull="VBTMA",
                             f_very_bear="VBTSTOCHKAMA",                             
                             trend_key="macdbb")
        self.get_output(s)   

class StratKamaStochSuperMacdbb(UnderlyingStrat):  
    '''
    Same as strat_kama_stoch_matrend_bbands but with different trend calculation
    '''
    def __init__(self,
                 period: numbers.Number,
                 dir_uncertain: str="long",
                 **kwargs):
        super().__init__(period,**kwargs)
        for k in ["dir_uncertain"]:
            setattr(self,k,locals()[k])
    
    def run(self):
        s = STRATWRAPPER.run(self.open,
                             self.high, 
                             self.low,
                             self.close,
                             self.close_ind,
                             trend_lim=1.5,
                             macro_trend_bool=False,
                             dir_uncertain=self.dir_uncertain,
                             f_bull="VBTSUPERTRENDMA",
                             f_bear="VBTSTOCHKAMA",
                             f_uncertain="VBTSTOCHKAMA",
                             f_very_bull="VBTSUPERTRENDMA",
                             f_very_bear="VBTSTOCHKAMA",                              
                             trend_key="macdbb")
        self.get_output(s)   

### With macro trend ###    
class StratKamaStochMatrendBbandsMacro(UnderlyingStrat):  
    '''
    As strat_kama_stoch_matrend_bbands but the short/long is determined by macro trend
    '''
    def __init__(self,
                 period: numbers.Number,
                 dir_bull: str="long",
                 dir_bear: str="short",
                 dir_uncertain: str="long",
                 macro_trend_index: bool=False,
                 **kwargs):
        super().__init__(period,**kwargs)
        for k in ["dir_bull","dir_bear","dir_uncertain", "macro_trend_index"]:
            setattr(self,k,locals()[k])
    
    def run(self):
        s = STRATWRAPPER.run(self.open,
                             self.high, 
                             self.low,
                             self.close,
                             self.close_ind,
                             trend_lim=1.5,
                             macro_trend_bool=True,
                             dir_bull=self.dir_bull, 
                             dir_bear=self.dir_bear,
                             dir_uncertain=self.dir_uncertain,
                             f_bull="VBTMA",
                             f_bear="VBTSTOCHKAMA",
                             f_uncertain="VBTSTOCHKAMA",
                             f_very_bull="VBTMA",
                             f_very_bear="VBTSTOCHKAMA",                             
                             trend_key="bbands",
                             macro_trend_index=self.macro_trend_index)
        self.get_output(s)

class StratKamaStochMatrendMacdbbMacro(UnderlyingStrat):  
    '''
    As strat_kama_stoch_matrend_macdbb but the short/long is determined by macro trend
    '''
    def __init__(self,
                 period: numbers.Number,
                 dir_bull: str="long",
                 dir_bear: str="short",
                 dir_uncertain: str="long",
                 macro_trend_index: bool=False,
                 **kwargs):
        super().__init__(period,**kwargs)
        for k in ["dir_bull","dir_bear","dir_uncertain", "macro_trend_index"]:
            setattr(self,k,locals()[k])
    
    def run(self):
        s = STRATWRAPPER.run(self.open,
                             self.high, 
                             self.low,
                             self.close,
                             self.close_ind,
                             trend_lim=1.5,
                             macro_trend_bool=True,
                             dir_bull=self.dir_bull, 
                             dir_bear=self.dir_bear,
                             dir_uncertain=self.dir_uncertain,
                             f_bull="VBTMA",
                             f_bear="VBTSTOCHKAMA",
                             f_uncertain="VBTSTOCHKAMA",
                             f_very_bull="VBTMA",
                             f_very_bear="VBTSTOCHKAMA",                             
                             trend_key="macdbb",
                             macro_trend_index=self.macro_trend_index)
        self.get_output(s)
        
class StratKamaStochMacro(UnderlyingStrat):  
    '''
    As strat_kama_stoch but the short/long is determined by macro trend
    '''
    def __init__(self,
                 period: numbers.Number,
                 dir_bull: str="long",
                 dir_bear: str="short",
                 dir_uncertain: str="long",
                 macro_trend_index: bool=False,
                 **kwargs):
        super().__init__(period,**kwargs)
        for k in ["dir_bull","dir_bear","dir_uncertain", "macro_trend_index"]:
            setattr(self,k,locals()[k])
    
    def run(self):
        s = STRATWRAPPER.run(self.open,
                             self.high, 
                             self.low,
                             self.close,
                             self.close_ind,
                             trend_lim=100,
                             macro_trend_bool=True,
                             dir_bull=self.dir_bull, 
                             dir_bear=self.dir_bear,
                             dir_uncertain=self.dir_uncertain,
                             f_uncertain="VBTSTOCHKAMA",
                             macro_trend_index=self.macro_trend_index)
        self.get_output(s)

 
        
        
        

        
