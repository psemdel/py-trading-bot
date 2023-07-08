#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jun  4 13:05:41 2022

@author: maxime
"""
import vectorbtpro as vbt
import core.indicators as ic
import numbers

from core.strat import UnderlyingStrat
from core.presel import Presel, WQ
from core import common, constants
from core.common import copy_attr
from core.data_manager import retrieve_data_live

import pandas as pd

class StratLIVE(UnderlyingStrat):
    def __init__(
            self,
            symbols: list,
            period: str,
            symbol_index: str,
            it_is_index: bool=False
            ):
        """
        Function to back stage recent data
        Called outside of Django!!!
        As strat but adapted to download every time the data
        
        Arguments
        ----------
            symbols: list of YF tickers
            period: period of time in year for which we shall retrieve the data
            symbol_index: main index to be retrieved
        """
        for k in ["period","symbols","symbol_index", "it_is_index"]:
            setattr(self,k,locals()[k])
        retrieve_data_live(self, symbols, symbol_index, period, it_is_index=it_is_index )

def scan(
        strategy: str,
        res: dict={},
        ust=None, #underlying strat
        strat_l: list=None,
        presel_l: list=None,
        fees: numbers.Number=0,
        restriction:int=None,
        **kwargs)-> dict:
    '''
    Calculate the performance of an underlying strategy in recent time
    
    Note: set your period to be significantly longer than the restriction to avoid calculation errors
    
    Arguments
    ----------
        strategy: name of strategy
        res: result dictionary, progressively filed
        ust: underlying strategy
        strat_l: list containing the strategy to be tested
        presel_l: list containing the preselection strategy to be tested
        fees: fees to be applyed during trades
        restriction : limit the range for the calculation of the return to x market days, 
    '''
    res[strategy]={}
    
    if presel_l is not None:
        l=presel_l
    else:
        l=strat_l
        bti=ust

    for p in l:
        if presel_l is not None:
            bti=PreselLIVE(ust=ust) #has to be recalculated everytime, otherwise it caches
            if type(p)==int:
                bti=WQLIVE(p,ust=ust)
                bti.def_cand()
                bti.calculate(nostrat11=True)
            else:
                getattr(bti,"preselect_"+p)()
        else:
            getattr(bti,p)()
            
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
        
    res[strategy][p]=pf.get_total_return()
    return res        

def scan_presel_all(
        period,
        **kwargs):
    """
    Allow you to evaluate how performed preselection strategies on past period finishing today, so in a close past
    
    Arguments
    ----------
        period: period of time in year for which we shall retrieve the data
    """    
    
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
    presel_l=["vol","realmadrid","retard","retard_macro","divergence","divergence_blocked",7,31,53,54]
    res={}
    
    for k, v in d.items():
        symbols=common.filter_intro_symbol(v["symbols"],period)
        ust=StratLIVE(symbols,str(period)+"y",v["index"])
        res=scan( k,presel_dic=presel_l, res=res,ust=ust,**kwargs)
        
    return res

#Same as bt but for recent data
#Only import with strat supported
class PreselLIVE(Presel):
    def __init__(
            self,
            ust
            ):
        '''
        Calculate the performance of a preselection strategy in recent time

        Arguments
        ----------
            ust: underlying strategy
        '''
        self.ust=ust
        copy_attr(self,ust)
        
        self.symbols=self.close.columns.values
    
        self.start_capital=10000
        self.order_size=self.start_capital
        self.capital=self.start_capital
        
        for k in ["entries","exits","exits_short","entries_short"]:
            setattr(self,k, pd.DataFrame.vbt.empty_like(self.close, fill_value=False))
     
        self.pf=[]
        self.pf_short=[]
        
        ust.strat_kama_stoch_matrend_bbands()
        
        self.ent11=ust.entries
        self.ex11=ust.exits
 
        self.vol=ic.VBTNATR.run(self.high,self.low,self.close).natr
    
        self.excluded=[]
        self.hold_dur=0
         
        self.candidates=[[] for ii in range(len(self.close))]
        self.candidates_short=[[] for ii in range(len(self.close))]
         
        self.symbols_simple=self.close.columns.values
        self.symbols_complex=self.ent11.columns.values
         
        self.last_order_dir="long" 
        
class WQLIVE(WQ):
    def __init__(
            self, 
            nb:int,
            ust=None, 
            ):
        '''
        Calculate the performance of a wq strategy in recent time

        Arguments
        ----------
            ust: underlying strategy
        '''
        copy_attr(self,ust)

        self.candidates=[[] for ii in range(len(self.close))]
        self.pf=[]
        
        for k in ["entries","exits","exits_short","entries_short"]: #actually only long are used in those strategy
            setattr(self,k, pd.DataFrame.vbt.empty_like(self.close, fill_value=False))

        self.start_capital=10000
        self.order_size=self.start_capital
        self.capital=self.start_capital
        
        self.symbols_simple=self.close.columns.values
        
        self.nb=nb
        self.out = vbt.wqa101(self.nb).run(
            open=self.open, 
            high=self.high,
            low=self.low, 
            close=self.close,
            volume=self.volume
            ).out   

        
    