#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jun  4 13:05:41 2022

@author: maxime
"""
import vectorbtpro as vbt
import numbers

from core.strat import UnderlyingStrat
from core import common, constants, strat, presel
from core.data_manager import retrieve_data_live

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
        
        self.symbols_to_YF={}
        for s in self.symbols:
            self.symbols_to_YF[s]=s
            
        for k in ["actions","exchange","st"]:
            setattr(self,k,None)

def scan(
        strategy: str,
        ust, #underlying strat
        res: dict={},
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

    for p in l:
        bti=presel.name_to_ust_or_presel(p, ust.period,input_ust=ust)

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
    presel_l=["PreselVol","PreselRealMadrid","PreselRetard","PreselRetardMacro","PreselDivergence",
              "PreselDivergenceBlocked","PreselWQ7","PreselWQ31","PreselWQ53","PreselWQ54"]
    res={}
    
    for k, v in d.items():
        symbols=common.filter_intro_symbol(v["symbols"],period)
        ust=StratLIVE(symbols,str(period)+"y",v["index"])
        ust=strat.StratHold(str(period)+"y",input_ust=ust) #to populate methods
        res=scan( k,ust, res=res,presel_l=presel_l,**kwargs)
        
    return res



        
    