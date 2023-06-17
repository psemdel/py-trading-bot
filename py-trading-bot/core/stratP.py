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
from orders.ib import retrieve_data
import core.indicators as ic

from core.strat import Strat
from orders.models import Action
import logging
logger = logging.getLogger(__name__)

# Like strat but for production
class StratPRD(Strat):
    def __init__(self,use_IB,**kwargs):
        try:
            actions=kwargs.get("actions1")
            self.symbols=[]
            self.symbols_to_YF={}
            
            if actions is None:
                if kwargs.get("symbols1") is None:
                    raise ValueError("StratPRD, no symbols provided")
                else:
                    symbols=kwargs.get("symbols1")
                    actions=[]
                    
                    for symbol in symbols:
                        actions.append(Action.objects.get(symbol=symbol))
            
            if kwargs.get("close") is not None:
                for l in ["close","high","low","volume","data"]:
                    setattr(self,l,kwargs.get(l))
                    if kwargs.get(l) is None:
                        raise ValueError(l+" no value found in StratPRD")
                    setattr(self,l+"_ind",kwargs.get(l+"_ind"))
                    if kwargs.get(l+"_ind") is None:
                        raise ValueError(l+"_ind no value found in StratPRD")
                setattr(self,"open",kwargs.get("open_")) 
                setattr(self,"open_ind",kwargs.get("open_ind"))
                
                for a in actions:
                    if use_IB:
                        s=a.ib_ticker()
                    else:
                        s=a.symbol
                    self.symbols.append(s)
                    self.symbols_to_YF[s]=a.symbol
            else:
                period=kwargs.get("period1")
                if period is None:
                    raise ValueError("StratPRD, no period provided")
                
                use_IB, self.symbols_undef=retrieve_data(self,actions,period,use_IB,index=kwargs.get("index"))
                
                self.symbols=self.symbols_undef #the symbols as output are then the YF symbols
                for s in self.symbols:
                    self.symbols_to_YF[s]=s
    
            self.vol=ic.VBTNATR.run(self.high,self.low,self.close).natr
            self.use_IB=use_IB
            self.actions=actions
                
        except ValueError as e:
            print(e)
            logger.error(e, stack_info=True, exc_info=True)
            
    def call_strat(self,name,**kwargs):
        getattr(self,name)(prd=True,**kwargs)
        
    def get_last_decision(self, symbol_complex_ent, symbol_complex_ex):
        for ii in range(1,len(self.entries[symbol_complex_ent].values)-1):
            if (self.entries[symbol_complex_ent].values[-ii] or self.exits_short[symbol_complex_ent].values[-ii]) and not\
            (self.exits[symbol_complex_ex].values[-ii] or self.entries_short[symbol_complex_ex].values[-ii]):
                return -1
            elif (self.exits[symbol_complex_ex].values[-ii] or self.entries_short[symbol_complex_ex].values[-ii]) and not\
                (self.entries[symbol_complex_ent].values[-ii] or self.exits_short[symbol_complex_ent].values[-ii]):
                return 1
        return 0
    
    def grow_past(self,distance, ma):
        res=ic.VBTGROW.run(self.close,distance=distance, ma=ma).out
        self.symbols_complex_yn=res.columns.values
        
        return res

    def symbols_simple_to_complex_yn(self,symbol_simple):
        for ii, e in enumerate(self.symbols_complex_yn):
            if e[-1]==symbol_simple: #9
                return e     
        
    def date(self):
        return self.close.index[-1]
        
        
        

        