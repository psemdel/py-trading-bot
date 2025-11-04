#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Mar 26 12:35:55 2023

@author: maxime
"""

import vectorbtpro as vbt
import numpy as np

from core.common import remove_multi
from core.presel import Presel
from core.caller import name_to_ust_or_presel
from numba import njit

import logging
logger = logging.getLogger(__name__)
"""
Classic portfolio optimization

This file explore the possibility to use classic portfolio optimizations to preselect the 
actions (like in presel.py) and them apply on them some "one action" strategy on some "slow" (once a month
or once a year) and periodic strategies. For strategies that are already "fast" like OLMAR, no
"one action" strategy is implemented.

This file is for backtesting.

As those strategies are very slow, there is no automatic implementation. I would recommend to perform the calculation once and set the 
actions in StratCandidates / normal (in the admin panel)
"""
@njit
def signal_to_size(entries,exits, entries_short, exits_short, idx_arr):
    idx=0
    bought=np.full(entries.shape, 0)
    sold=np.full(entries.shape, 0)
    
    for ii in range(np.shape(entries)[0]):
        #end of a windows
        if ii>0:
            bought[ii]=bought[ii-1]
            sold[ii]=sold[ii-1]
        if idx<(len(idx_arr)):
                if ii>=idx_arr[idx]:
                    idx+=1 
                    bought[ii]=0
                    sold[ii]=0
        
        if entries[ii] and not exits[ii]:
            bought[ii]=1
        elif exits[ii] and not entries[ii]:
            bought[ii]=0
        if entries_short[ii] and not exits_short[ii]:
            sold[ii]=1
        elif exits_short[ii] and not entries_short[ii]:
            sold[ii]=0         

    return bought, sold

SIGNALTOSIZE = vbt.IF(
      class_name='SignalToSize',
      short_name='signal_to_size',
      input_names=['entries','exits','entries_short', 'exits_short'],
      output_names=["bought","sold"],
      param_names=["idx_arr"]
 ).with_apply_func(
      signal_to_size, 
      takes_1d=True,  
 )       

class PreselClassic(Presel):
    def __init__(self,period,**kwargs):
        super().__init__(period,**kwargs)
        self.pf_opt=None 
        self.cands={}
    
    #still slow
    def expand_alloc(self,idx_arr, allocations):
        expanded_allocations = self.pf_opt.wrapper.fill(0.0, group_by=False)
        idx=0
    
        for ii in range(np.shape(expanded_allocations)[0]):
            if idx<(len(idx_arr)):
                if ii>=idx_arr[idx]:
                    idx+=1
                
            if ii>=idx_arr[0]: #before it is only NaN
                expanded_allocations.iloc[ii]=allocations[idx-1]
        
        return expanded_allocations 

    #needs sum over a line, so vbt is not a solution
    #increase the allocation to minimize cash available
    #no excess of 1 of allocation in long or short direction
    def max_alloc(self):
        self.new_alloc=self.pf_opt.wrapper.fill(0, group_by=False)
        empt=np.empty(np.shape(self.used_allocations)[1])
        empt[:]=np.nan
        row_last_filled=None

        for ii in range(len(self.used_allocations)):
            pos_sum=sum(self.used_allocations.iloc[ii][self.used_allocations.iloc[ii]>=0])
            neg_sum=abs(sum(self.used_allocations.iloc[ii][self.used_allocations.iloc[ii]<0]))
            s=max(pos_sum,neg_sum) #neg must not be over -1

            if s!=0:
                self.new_alloc.iloc[ii]=self.used_allocations.iloc[ii]/s
            else:
                self.new_alloc.iloc[ii]=self.used_allocations.iloc[ii]
            
            #nullify row without change to avoid rebalancing all the time, which is not realistic
            if ii>0:
                if np.all(self.new_alloc.iloc[ii]==row_last_filled):
                    self.new_alloc.iloc[ii]=empt
                else:
                    row_last_filled=self.new_alloc.iloc[ii]

    def fill_allocations_underlying(self):
        idx_arr = self.pf_opt.alloc_records.get_field_arr("idx")

        #transform the entries and exits in 1 and 0
        t=SIGNALTOSIZE.run(
            self.ust_classic.entries,
            self.ust_classic.exits,
            self.ust_classic.entries_short,
            self.ust_classic.exits_short,
            idx_arr=[idx_arr]
            )

        self.expanded_allocations= self.expand_alloc(idx_arr, self.pf_opt._allocations) #add the weight
        self.used_allocations=remove_multi(t.bought-t.sold)*remove_multi(self.expanded_allocations)
        self.max_alloc()
        self.size=self.new_alloc

    def apply_underlying_strat(self, strat_name):
        if "ust" in self.__dir__(): #for handle "live" strategy
            self.ust_classic=name_to_ust_or_presel(strat_name,None,self.period, input_ust=self.ust)
        else:
            self.ust_classic=name_to_ust_or_presel(strat_name,None,self.period, symbol_index=self.symbol_index)

        self.fill_allocations_underlying()
        
        #as function from_optimizer
        pf=vbt.Portfolio.from_orders( 
            self.close, 
            size_type="targetpercent", 
            size=self.size,                              
            freq="1d", 
            call_seq = "auto",
            cash_sharing=True 
            )
        return pf
    
    def apply_no_underlying_strat(self):
        pf=self.pf_opt.simulate(self.close,freq="1d")
        return pf
        
    def max_sharpeY(self):
        self.pf_opt = vbt.PortfolioOptimizer.from_pypfopt(
            prices=self.close,
            every="Y",
            target="max_sharpe", 
        )
        
    def hrpY(self):
        self.pf_opt = vbt.PortfolioOptimizer.from_pypfopt(
            prices=self.close,
            every="Y",
            target="optimize",
            optimizer="hrp",
        )
        
    #require universal-portfolio, pip install universal-portfolios, be careful it downgrades plotly. Reupgrade afterwards, as vectorbt requires higher version. 
    def Universal(self, key): #OLMAR, Anticor, WMAMR
        self.pf_opt = vbt.PortfolioOptimizer.from_universal_algo(  
            key,
            self.close,
        )
