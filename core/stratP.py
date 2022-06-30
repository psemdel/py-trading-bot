#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 31 20:23:44 2022

@author: maxime
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat May 14 22:36:16 2022

@author: maxime
"""
from orders.models import retrieve_data
import core.indicators as ic

from core.strat import Strat

# Like strat but for production
class StratPRD(Strat):
    def __init__(self,symbols,period,**kwargs):
        self.symbols=symbols
        self.period=period
        
        if kwargs.get("close",False):
            self.high=kwargs.get("high")
            self.low=kwargs.get("low")
            self.close=kwargs.get("close")
            self.open=kwargs.get("open")
            self.high_ind=kwargs.get("high_ind")
            self.low_ind=kwargs.get("low_ind")
            self.close_ind=kwargs.get("close_ind")
            self.open_ind=kwargs.get("open_ind")
        else:
            self.high, self.low, self.close, self.open,self.volume,\
            self.high_ind, self.low_ind, self.close_ind, self.open_ind, self.volume_ind\
            =retrieve_data(symbols,period,**kwargs)

        self.vol=ic.VBTNATR.run(self.high,self.low,self.close).natr
    
    def call_strat(self,name,**kwargs):
        meth=getattr(self,name)
        meth(**kwargs)
        
    def grow_past(self,distance, ma):
        res=ic.VBTGROW.run(self.close,distance=distance, ma=ma).res 
        self.symbols_complex_yn=res.columns.values
        
        return res

    def symbols_simple_to_complex_yn(self,symbol_simple):
        for ii, e in enumerate(self.symbols_complex_yn):
            if e[-1]==symbol_simple: #9
                return e     
        
    def date(self):
        return self.close.index[-1]
        
        
        

        