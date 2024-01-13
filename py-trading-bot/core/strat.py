#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat May 14 22:36:16 2022

@author: maxime
"""
import vectorbtpro as vbt
import numpy as np
import numbers

from core.common import save_vbt_both, remove_multi, intersection
import core.indicators as ic
from core.macro import VBTMACROFILTER, VBTMACROMODE, VBTMACROTREND, VBTMACROTRENDPRD, major_int
from core.constants import BEAR_PATTERNS, BULL_PATTERNS
from core.data_manager import retrieve_data_offline #don't load here retrieve_data_online, otherwise backtesting with Django off won't work
import inspect
import pandas as pd
from trading_bot.settings import _settings

import logging
logger = logging.getLogger(__name__)

"""
Strategies on one action, no preselection

So it determines entries and exits for one action to optimize the return

Some of the strategies have been optimized to work with a preselection (see presel.py), for instance StratDiv.
"""
def defi_i_fast_sub(
        all_t: list,
        t_ent: pd.core.frame.DataFrame, 
        t_ex: pd.core.frame.DataFrame, 
        strat_arr_h: dict,
        key: str,
        ) -> list:
    """
    Multiply the entries or exits by the array (0 or 1)

    Arguments
    ----------
        all_t: entries or exits for all strategies before
        t_ent: entries for the strategy to be added
        t_ex: exits for the strategy to be added
        strat_arr: dict of the strategy combination
        key: key of the strategy to be added in calc_arrs
    """ 
    for ent_or_ex in ['ent','ex']:
        if ent_or_ex == 'ent':
            t=t_ent
        else:
            t=t_ex
        
        if t is not None:
            for k, v in strat_arr_h.items(): #3,
                if key in v[ent_or_ex]:
                    all_t[ent_or_ex][k]+=remove_multi(t)

    return all_t 

   
def filter_macro(all_t_ent: list,
                 macro_trend: pd.core.frame.DataFrame,
                 ) -> pd.core.frame.DataFrame:
    """
    For each trend set the correct entries and exits

    Arguments
    ----------
        all_t: entries or exits for all strategies before
        macro_trend: trend for each symbols and moment in time
    """   
    ent=None
    dic={'bull':-1, 'bear':1, 'uncertain':0}  
    
    for k, v in all_t_ent.items():
        ents_raw=VBTMACROFILTER.run(v,macro_trend,dic[k]).out #
        if ent is None:
            ent=ents_raw
        else:
            ent=ic.VBTOR.run(ent, ents_raw).out
    return ent

def defi_i_fast( 
        open_: pd.core.frame.DataFrame,
        high: pd.core.frame.DataFrame, 
        low: pd.core.frame.DataFrame, 
        close: pd.core.frame.DataFrame,
        volume: pd.core.frame.DataFrame,
        strat_arr_h: dict,
        macro_trend: pd.core.frame.DataFrame=None,
        ) -> (dict):
    """
    Calculate the entries and exits for each strategy of the array separately
    Fast determine directly if an entry or exit is required. There is no intermediate result

    Note: the "rev" proved to be less interesting than the normal signals

    Arguments
    ----------
        open_: opening prices
        close: close prices
        high: high prices
        low: low prices
        volume: volumes        
        strat_arr_h: dict of the strategy combination, written in a human readable way
        macro_trend: trend for each symbols and moment in time
    """ 
    all_t={'ent':{}, 'ex':{}}
    out_t={}

    for k in strat_arr_h:
        all_t['ent'][k]=np.full(np.shape(close),0.0)
        all_t['ex'][k]=np.full(np.shape(close),0.0)
        out_t['ent']=np.full(np.shape(close),0.0)
        out_t['ex']=np.full(np.shape(close),0.0)
    
    item_to_calc=[]
    for k, v in strat_arr_h.items():
        for kk, vv in v.items():
            item_to_calc+=vv
    item_to_calc=list(set(item_to_calc))   
    
    if 'MA' in item_to_calc:
        t=ic.VBTMA.run(close)
        all_t=defi_i_fast_sub(all_t,t.entries,t.exits, strat_arr_h, 'MA')
        
    if ('STOCH' in item_to_calc) or ('STOCH_rev' in item_to_calc):
        t=vbt.STOCH.run(high,low,close)
        if 'STOCH' in item_to_calc:
            all_t=defi_i_fast_sub(all_t,t.slow_k_crossed_below(20),t.slow_k_crossed_above(80), strat_arr_h, 'STOCH')
        if 'STOCH_rev' in item_to_calc:
            all_t=defi_i_fast_sub(all_t,t.slow_k_crossed_above(20),t.slow_k_crossed_below(80), strat_arr_h, 'STOCH_rev')
            
    if 'KAMA' in item_to_calc:
        t=ic.VBTSTOCHKAMA.run(high,low,close)
        all_t=defi_i_fast_sub(all_t,t.entries_kama,t.exits_kama, strat_arr_h, 'KAMA')        
        
    if 'SUPERTREND' in item_to_calc:
        t=ic.VBTSUPERTREND.run(high,low,close)
        all_t=defi_i_fast_sub(all_t,t.entries,t.exits, strat_arr_h, 'SUPERTREND')
        
    if 'BBANDS' in item_to_calc:
        t=vbt.BBANDS.run(close)
        all_t=defi_i_fast_sub(all_t,t.lower_above(close),t.upper_below(close), strat_arr_h, 'BBANDS')
       
    if ('RSI20' in item_to_calc) or ('RSI30' in item_to_calc) or\
       ('RSI20_rev' in item_to_calc) or ('RSI30_rev' in item_to_calc):
        t=vbt.RSI.run(close,wtype='simple')
        if 'RSI20' in item_to_calc:
            all_t=defi_i_fast_sub(all_t,t.rsi_crossed_below(20),t.rsi_crossed_above(80), strat_arr_h, 'RSI20')
        if 'RSI20_rev' in item_to_calc:
            all_t=defi_i_fast_sub(all_t,t.rsi_crossed_above(20),t.rsi_crossed_below(80), strat_arr_h, 'RSI20_rev')            
        if 'RSI30' in item_to_calc:
            all_t=defi_i_fast_sub(all_t,t.rsi_crossed_below(30),t.rsi_crossed_above(70), strat_arr_h, 'RSI30')
        if 'RSI30_rev' in item_to_calc:
            all_t=defi_i_fast_sub(all_t,t.rsi_crossed_above(30),t.rsi_crossed_below(70), strat_arr_h, 'RSI30_rev')
            
    if ('MFI' in item_to_calc) or ('MFI_rev' in item_to_calc):
        t=vbt.talib("MFI").run(high, low, close,volume)
        if 'MFI' in item_to_calc:
            all_t=defi_i_fast_sub(all_t,t.real_crossed_below(20),t.real_crossed_above(80), strat_arr_h, 'MFI')
        if 'MFI_rev' in item_to_calc:
            all_t=defi_i_fast_sub(all_t,t.real_crossed_above(20),t.real_crossed_below(80), strat_arr_h, 'MFI_rev')        

    if ('WILLR' in item_to_calc) or ('WILLR_rev' in item_to_calc):
        t=vbt.talib("WILLR").run(high, low, close)
        if 'WILLR' in item_to_calc:
            all_t=defi_i_fast_sub(all_t,t.real_crossed_below(-90),t.real_crossed_above(-10), strat_arr_h, 'WILLR')
        if 'WILLR_rev' in item_to_calc:
            all_t=defi_i_fast_sub(all_t,t.real_crossed_above(-90),t.real_crossed_below(-10), strat_arr_h, 'WILLR_rev')        

    if ('ULTOSC20' in item_to_calc) or ('ULTOSC25' in item_to_calc) or\
       ('ULTOSC20_rev' in item_to_calc) or ('ULTOSC25_rev' in item_to_calc): 
        t=vbt.talib("ULTOSC").run(high, low, close)
        if 'ULTOSC20' in item_to_calc:
            all_t=defi_i_fast_sub(all_t,t.real_crossed_below(20),t.real_crossed_above(80), strat_arr_h, 'ULTOSC20')
        if 'ULTOSC20_rev' in item_to_calc:
            all_t=defi_i_fast_sub(all_t,t.real_crossed_above(20),t.real_crossed_below(80), strat_arr_h, 'ULTOSC20_rev')            
        if 'ULTOSC25' in item_to_calc:
            all_t=defi_i_fast_sub(all_t,t.real_crossed_below(25),t.real_crossed_above(75), strat_arr_h, 'ULTOSC25')
        if 'ULTOSC25_rev' in item_to_calc:
            all_t=defi_i_fast_sub(all_t,t.real_crossed_above(25),t.real_crossed_below(75), strat_arr_h, 'ULTOSC25_rev')
            
    for ii, f_name in enumerate(BULL_PATTERNS):
        if f_name in item_to_calc:
            t=ic.VBTPATTERNONE.run(open_,high,low,close,f_name, "ent")
            all_t=defi_i_fast_sub(all_t,t.out,None, strat_arr_h, f_name)
        
    for ii, f_name in enumerate(BEAR_PATTERNS):
        if f_name in item_to_calc:
            t=ic.VBTPATTERNONE.run(open_,high,low,close,f_name, "ex")
            all_t=defi_i_fast_sub(all_t,None,t.out, strat_arr_h, f_name)

    for ent_or_ex in ['ent','ex']:
        for k in strat_arr_h:    
            all_t[ent_or_ex][k]=(all_t[ent_or_ex][k]>=1)
    #agregate the signals for different macro trends
    if macro_trend is not None:
        for ent_or_ex in ['ent','ex']:
            out_t[ent_or_ex]=filter_macro(all_t[ent_or_ex], macro_trend)    
    else:
        for ent_or_ex in ['ent','ex']:
            out_t[ent_or_ex]=all_t[ent_or_ex]['simple']

    return out_t

def defi_nomacro(
        close: pd.core.frame.DataFrame,
        all_t: list,
        ent_or_ex: str, 
        strat_arr: dict
        )-> (pd.core.frame.DataFrame, pd.core.frame.DataFrame):
    """
    transform the array of strategy into entries and exits

    Arguments
    ----------
        close: close prices
        all_t: entries and exits for one strategy or the array
        ent_or_ex: do we want to return the entries or exits?
        strat_arr: dict of the strategy combination
    """
    ent=None
    if 'simple' not in strat_arr:
        raise ValueError("simple column not present in strat_arr")
    arr=strat_arr['simple'][ent_or_ex]

    for ii in range(len(arr)):
        if arr[ii]:
            t=all_t[ii]
                    
            if ent is None:
                ent=t
            else:
                ent=ic.VBTOR.run(ent,t).out
                
    default=ic.VBTAND.run(ent, np.full(all_t[0].shape, False)).out #trick to keep the right shape
    return ent, default

def strat_wrapper_simple(
        open_: pd.core.frame.DataFrame,
        high: pd.core.frame.DataFrame, 
        low: pd.core.frame.DataFrame, 
        close: pd.core.frame.DataFrame, 
        volume: pd.core.frame.DataFrame, 
        strat_arr: dict,
        dir_simple:str="long",
        ) -> (pd.core.frame.DataFrame, pd.core.frame.DataFrame, pd.core.frame.DataFrame, pd.core.frame.DataFrame):
    """
    wrapper for the different strategy functions

    No trend split

    Each strategy is defined by the arrays a_simple

    Arguments
    ----------
        open_: open prices
        high: high prices
        low: low prices
        close: close prices
        strat_arr: dict of the strategy combination
        dir_simple: direction to use during bull trend
    """
    t=defi_i_fast( open_,high, low, close,volume, strat_arr)
    default=ic.VBTAND.run(t['ent'], np.full(t['ent'].shape, False)).out #trick to keep the right shape
    
    if dir_simple in ["long","both"]:
        entries=t['ent']
        exits=t['ex']
    else:
        entries=default
        exits=default
        
    if dir_simple in ["both","short"]:
        entries_short=t['ex']
        exits_short=t['ent']
    else:
        entries_short=default
        exits_short=default

    return entries, exits, entries_short, exits_short

def strat_wrapper_macro(open_: np.array,
                        high: np.array, 
                        low: np.array, 
                        close: np.array, 
                        volume: np.array,
                        strat_arr: dict, 
                        dir_bull: str="long", 
                        dir_bear: str="both",
                        dir_uncertain: str="both",
                        prd:bool=False,
                        ):
    """
    wrapper for the different strategy functions

    split the trend in 3 parts: bear, uncertain, bull
    set a strategy for each of them

    Each strategy is defined by the arrays a_bull, a_bear, a_uncertain

    Arguments
    ----------
        open_: open prices
        high: high prices
        low: low prices
        close: close prices
        strat_arr: dict of the strategy combination
        dir_bull: direction to use during bull trend
        dir_bear: direction to use during bear trend
        dir_uncertain: direction to use during uncertain trend
    """
    if prd:
        t=VBTMACROTRENDPRD.run(close)
    else:
        t=VBTMACROTREND.run(close)

    #combine for the given array the signals and patterns
    tt=defi_i_fast( open_,
                       high,
                       low, 
                       close,
                       volume,
                       strat_arr,
                       macro_trend=t.macro_trend
                       )
    
    #put both/long/short
    t2=VBTMACROMODE.run(tt['ent'],tt['ex'], t.macro_trend,\
                       dir_bull=dir_bull,
                       dir_bear=dir_bear,
                       dir_uncertain=dir_uncertain)

    return t2.entries, t2.exits, t2.entries_short, t2.exits_short, t.macro_trend, t.min_ind, t.max_ind  

class UnderlyingStrat(): 
    def __init__(self,
                 period: numbers.Number,
                 symbol_index: str=None,
                 prd: bool=False,
                 it_is_index: bool=False,
                 suffix: str="",
                 actions: list=None,
                 symbols: list=None,
                 input_ust=None, #itself a strat
                 strat_arr: dict=None,
                 exchange:str=None,
                 st=None,
                 ):
        """
        Strategies on one action, no preselection. For production and non production, to make the strats as child of the main one.

        So it determines entries and exits for one action to optimize the return.
        
        It is also used in the code as an object to save at one place attributes like close, open, exchange,...

        Arguments
        ----------
            symbol_index: main index to be retrieved
            period: period of time for which we shall retrieve the data
            prd: for production or backtesting
            it_is_index: is it indexes that are provided
            suffix: suffix for files
            actions: list of actions
            symbols: list of YF tickers
            input_ust: input underlying strategy with already all data downloaded, avoid downloading the same several times
            strat_arr: dict of the strategy combination to use
            exchange: stock exchange, only for saving
            st: strategy associated
        """
        self.suffix=suffix
        if self.suffix!="":
            self.suffix="_" + self.suffix
        for k in ["prd","period","symbol_index", "actions","symbols","exchange","st"]:
            if locals()[k] is None and input_ust is not None:
                setattr(self,k, getattr(input_ust,k))
            else:
                setattr(self,k,locals()[k])
        
        self.symbols_to_YF={}
        self.strat_arr=strat_arr
        
        if input_ust is not None:
            for l in ["close","open","high","low","volume","data"]:
                setattr(self,l,getattr(input_ust,l))
                if getattr(input_ust,l) is None:
                    raise ValueError(l+" no value found in StratPRD")
                setattr(self,l+"_ind",getattr(input_ust,l+"_ind"))
                if getattr(input_ust,l+"_ind") is None:
                    raise ValueError(l+"_ind no value found in StratPRD")
        else:
            if not self.prd:
                if self.symbol_index is None:
                    raise ValueError("symbol_index is none for ust")
                    
                retrieve_data_offline(self,self.symbol_index,self.period)
        
                if it_is_index:
                    for k in ["data","close","open","low","high"]:
                        setattr(self,k,getattr(self,k+"_ind"))
                else:
                    self.symbols_simple=self.close.columns.values
            else:
                from orders.models import Action
                from core.data_manager_online import retrieve_data_online
                if self.actions is None:
                    if self.symbols is None:
                        raise ValueError("StratPRD, no symbols provided")
                    self.actions=[Action.objects.get(symbol=symbol) for symbol in self.symbols]
                self.symbols=retrieve_data_online(self,self.actions,period,it_is_index=it_is_index, used_api_key="reporting")  #the symbols as output are then the YF symbols
                for s in self.symbols:
                    self.symbols_to_YF[s]=s
                
        if input_ust is not None and self.prd: 
            self.symbols=[]
            for a in self.actions:
                if _settings["USED_API"]["reporting"]=="IB":
                    s=a.ib_ticker()
                else:
                    s=a.symbol
                self.symbols.append(s)
                self.symbols_to_YF[s]=a.symbol
 
        self.vol=vbt.talib("NATR").run(self.high,self.low,self.close).real
        self.actions=actions
        
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
  
    def symbols_simple_to_complex(
            self,
            symbol_simple: str,
            ent_or_ex: str):
        '''
        dataframes like close, open... use simple YF ticker as column. For instance "AMZN"
        
        However underlying strategy have because of vbt a multiindex, for instance ("pattern", "RSI", "AMZN")
        This function makes the conversion
        
        Arguments
        ----------
            symbol_simple: YF ticker
            ent_or_ex: entry or exit
        '''
        if pd.isnull(symbol_simple):
            raise ValueError("simple symbol is nan")
        
        if ent_or_ex=="ent":
            self.symbols_complex=self.entries.columns.values
        else:
            self.symbols_complex=self.exits.columns.values
        
        for ii, e in enumerate(self.symbols_complex):
            if type(e)==tuple:
                if e[-1]==symbol_simple: #9
                    return e
            elif type(e)==str:
                if e==symbol_simple: #9
                    return e     
        raise ValueError("symbols_simple_to_complex not found for symbol: "+str(symbol_simple) +\
                         " columns available: "+str(self.symbols_complex))
    
    def save(self):
        '''
        Save close, entries... to a file
        '''
        save_vbt_both(self.close, 
                 self.entries, 
                 self.exits, 
                 self.entries_short,
                 self.exits_short,                  
                 suffix=self.suffix
                 )

    def get_return(self):
        '''
        Give the return for a strategy
        '''
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
                
    def perform_StratCandidates(self, r, st_name):
        '''
        Perform during the report an underlying strategy on the candidates belonging to StratCandidates

        Arguments
        ----------
            r: report
            st_name: name of the strategy
        '''
        from orders.models import StratCandidates #needs to be loaded here, as it will work only if Django is loaded
        st_actions, _=StratCandidates.objects.get_or_create(strategy=self.st)  #.id
        st_symbols=st_actions.retrieve()
        
        for symbol in intersection(self.symbols,st_symbols):
            if np.isnan(self.vol[symbol].values[-1]):
                self.concat("symbol " + symbol + " no data")
            else:
                symbol_complex_ent_normal=self.symbols_simple_to_complex(symbol,"ent")
                symbol_complex_ex_normal=self.symbols_simple_to_complex(symbol,"ex")
                target_order=self.get_last_decision(symbol_complex_ent_normal,symbol_complex_ex_normal)
                r.display_last_decision(symbol,target_order, st_name)      
                
                r.ss_m.add_target_quantity(symbol, st_name, target_order)
    
    def perform(self, r, st_name:str=None): #default
        '''
        See perform_StratCandidates
        '''
        if st_name is None:
            raise ValueError("perform for underlying strategy should have an argument st_name")
        self.perform_StratCandidates(r, st_name) 
        
###production functions        
    def get_last_decision(self, symbol_complex_ent: str, symbol_complex_ex: str) -> int:
        '''
        Look for the last entry/exit for a stock, goes back in time. Target_order size is returned
        
        Arguments
        ----------
            symbol_complex_ent: multiindex column for the symbol, for instance (True, 5, 'AC') in the entry dataframe
            symbol_complex_ex: multiindex column for the symbol, for instance (True, 5, 'AC') in the exit dataframe
        
        '''
        for ii in range(1,len(self.entries[symbol_complex_ent].values)-1):
            if (self.entries[symbol_complex_ent].values[-ii] or self.exits_short[symbol_complex_ent].values[-ii]) and not\
            (self.exits[symbol_complex_ex].values[-ii] or self.entries_short[symbol_complex_ex].values[-ii]):
                return 1 #buy, target size is 1
            elif (self.exits[symbol_complex_ex].values[-ii] or self.entries_short[symbol_complex_ex].values[-ii]) and not\
                (self.entries[symbol_complex_ent].values[-ii] or self.exits_short[symbol_complex_ent].values[-ii]):
                return -1 #sell, target size is -1
        return 0
    
    def grow_past(self,
                  distance: numbers.Number, 
                  ma: bool
                  ) -> np.array:
        res=ic.VBTGROW.run(self.close,distance=distance, ma=ma).out
        self.symbols_complex_yn=res.columns.values
        
        return res

    def symbols_simple_to_complex_yn(self, symbol_simple: str):
        for ii, e in enumerate(self.symbols_complex_yn):
            if e[-1]==symbol_simple: #9
                return e     
 
    def run_simple(self):
        '''
        Calculate the entries and exits for underlying strategy which don't depend on the trend
        '''
        self.entries, self.exits, self.entries_short, self.exits_short= \
        strat_wrapper_simple(
                            self.open,
                            self.high, 
                            self.low,
                            self.close,
                            self.volume,
                            self.strat_arr,
                            )   
    
    def run_macro(self):
        '''
        Calculate the entries and exits for underlying strategy which depend on the trend
        '''
        self.entries, self.exits, self.entries_short, self.exits_short, \
        self.macro_trend, self.min_ind, self.max_ind=\
        strat_wrapper_macro(
                            self.open,
                            self.high, 
                            self.low,
                            self.close,
                            self.volume,
                            self.strat_arr, 
                            )  

    def run(self):
        if "bull" in self.strat_arr:
            self.run_macro()
        else:
            self.run_simple()        
########## Strats ##############
# Example of simple strategy for pedagogic purposes
class StratHold(UnderlyingStrat):
    '''
    Simply hold
    '''
    def run(self):
        t=ic.VBTVERYBULL.run(self.close)
        self.entries=t.entries
        self.exits=t.exits
        self.entries_short=t.exits
        self.exits_short=t.exits
        
class StratRSI(UnderlyingStrat):  
    '''
    Very basic RSI strategy
    '''
    def run(self):      
        t=vbt.RSI.run(self.close,wtype='simple')
        self.entries=t.rsi_crossed_below(20)
        self.exits=t.rsi_crossed_above(80)
        t2=ic.VBTFALSE.run(self.close).out
        self.entries_short=t2
        self.exits_short=t2
        
class StratRSIeq(UnderlyingStrat):   
    '''
    Same a stratRSI but realized with a strategy array
    '''
    def __init__(self,
                 period: numbers.Number,
                 **kwargs):
        
        a={"simple":
           {"ent":['RSI20'],
            "ex": ['RSI20']
           }
          }

        super().__init__(period,strat_arr=a,**kwargs )
        
class StratDiv(UnderlyingStrat):    
    '''
    Underlying strategy for divergence preselection
    '''
    def __init__(self,
                 period: numbers.Number,
                 **kwargs):
        a={'simple': 
         {'ent': ['RSI20'],
          'ex':  ['KAMA','SUPERTREND','BBANDS',"CDLBELTHOLD","CDLHIKKAKE","CDLRISEFALL3METHODS","CDLBREAKAWAY",
                  "CDL3BLACKCROWS"]
          }}

        super().__init__(period,strat_arr=a,**kwargs )

class StratTestSimple(UnderlyingStrat):    
    def __init__(self,
                 period: numbers.Number,
                 **kwargs):
        
        a={"simple":
           {"ent":['STOCH'],
            "ex": ['RSI20']
           }
          }        
        super().__init__(period,strat_arr=a,**kwargs )
        
class StratReal(UnderlyingStrat):    
    '''
    Underlying strategy for realmadrid preselection
    '''    
    def __init__(self,
                 period: numbers.Number,
                 **kwargs):

        a={'bull': {'ent': ['MA', 'STOCH',"CDLLONGLINE", "CDLDRAGONFLYDOJI", "CDLMORNINGSTAR"],
                    'ex':['MA',"CDLRISEFALL3METHODS"]},
           'bear': {'ent': ['MA', 'STOCH', 'RSI20',"CDLLONGLINE", "CDLDRAGONFLYDOJI", "CDLMORNINGSTAR"],
                    'ex': ['MA',"CDLRISEFALL3METHODS","CDLSEPARATINGLINES"]},
           'uncertain': {'ent':['MA', 'STOCH'],
                         'ex': ["CDLHIKKAKE","CDLRISEFALL3METHODS","CDLSEPARATINGLINES","CDL3BLACKCROWS","CDLDARKCLOUDCOVER"]
                         }
          }            

        super().__init__(
            period,
            strat_arr=a,
            **kwargs )
        
class StratKeep(UnderlyingStrat):    
    '''
    Strategy optimized for retard_keep preselection
    
    ent has no impact at all here
    '''
    def __init__(self,
                 period: numbers.Number,
                 **kwargs):

        a={'bull': {'ent': ['RSI20'],
                    'ex':['SUPERTREND',"CDLENGULFING", "CDLSEPARATINGLINES","CDLEVENINGDOJISTAR","CDLDARKCLOUDCOVER"]},
           'bear': {'ent': ['RSI20'],
                    'ex': ["CDL3LINESTRIKE","CDLSEPARATINGLINES","CDLEVENINGDOJISTAR"]},
           'uncertain': {'ent': ['RSI20'],
                         'ex': ['RSI20',"CDLEVENINGDOJISTAR"]}
          }

        super().__init__(
            period,
            strat_arr=a,
            **kwargs )  

class StratE(UnderlyingStrat):    
    '''
    Strategy optimized to have the best yield used alone on stocks
    '''
    def __init__(self,
                 period: numbers.Number,
                 **kwargs):

        a={'bull': {'ent': ["STOCH","CDLKICKING","CDL3WHITESOLDIERS","CDLMORNINGDOJISTAR","CDLMORNINGSTAR", "CDLHANGINGMAN", "CDLKICKING_INV"],
                    'ex': [  "CDLRISEFALL3METHODS", "CDLEVENINGDOJISTAR"]},
           'bear': {'ent':['STOCH' ,  "CDLKICKING", "CDLMARUBOZU", "CDL3WHITESOLDIERS","CDLMORNINGDOJISTAR", "CDLMORNINGSTAR",  "CDLHANGINGMAN", "CDLKICKING_INV"],
                    'ex': [ "CDLRISEFALL3METHODS","CDL3LINESTRIKE", "CDLEVENINGDOJISTAR","CDLDARKCLOUDCOVER"]},
           'uncertain': {'ent':['MA','RSI20',"CDLKICKING", "CDLMARUBOZU","CDL3WHITESOLDIERS","CDLLONGLINE","CDLENGULFING"],
                         'ex':["KAMA", "CDLRISEFALL3METHODS", "CDL3LINESTRIKE","CDLEVENINGSTAR","CDLSEPARATINGLINES"]}} 
        
        super().__init__(
            period,
            strat_arr=a,
            **kwargs )  

class StratF(UnderlyingStrat):    
    '''
    Strategy optimized to have the best yield used alone on stocks
    '''
    def __init__(self,
                 period: numbers.Number,
                 **kwargs):

        a={'bull': {'ent': ["RSI20","RSI30","CDLMARUBOZU","CDL3WHITESOLDIERS","CDLLONGLINE","CDLENGULFING","CDLTAKURI","CDLMORNINGDOJISTAR","CDLKICKINGBYLENGTH_INV", "CDLKICKING_INV"],
                    'ex': [ "CDLRISEFALL3METHODS"]},
           'bear': {'ent': ['STOCH','RSI20','RSI30', "CDLMARUBOZU","CDL3WHITESOLDIERS","CDLLONGLINE", "CDLENGULFING",
                            "CDLTAKURI","CDLMORNINGDOJISTAR","CDLKICKINGBYLENGTH_INV", "CDLKICKING_INV"],
                    'ex': ['SUPERTREND','BBANDS', "CDLBELTHOLD","CDLRISEFALL3METHODS"]},
           'uncertain': {'ent': ['STOCH','KAMA',"CDLMARUBOZU","CDLLONGLINE","CDLHANGINGMAN","CDLKICKING_INV"],
                         'ex':[ "CDLHIKKAKE",  "CDL3LINESTRIKE", "CDL3BLACKCROWS"]}} 
        
        super().__init__(
            period,
            strat_arr=a,
            **kwargs )  

class StratG(UnderlyingStrat):    
    '''
    Strategy optimized to have the best yield used alone on stocks
    
    In long/both/both, Optimized on 2007-2023, CAC40 7.58 (3.13 bench), DAX 2.31 (1.68), NASDAQ 19.88 (12.1), IT 15.69 (8.44)
    '''
    def __init__(self,
                 period: numbers.Number,
                 **kwargs):

        a={'bull': {'ent': ['KAMA','RSI20','RSI30','CDLMARUBOZU',"CDL3WHITESOLDIERS","CDLENGULFING","CDLTAKURI","CDLMORNINGDOJISTAR","CDLMORNINGSTAR","CDLKICKING_INV"],
                    'ex': ["CDLRISEFALL3METHODS","CDLABANDONEDBABY"]},
           'bear': {'ent': ['STOCH','RSI20','RSI30',"CDLMARUBOZU","CDL3WHITESOLDIERS","CDLLONGLINE","CDLENGULFING","CDLTAKURI",
                            "CDLMORNINGDOJISTAR","CDLHANGINGMAN","CDLKICKINGBYLENGTH_INV"],
                    'ex': ['SUPERTREND','BBANDS',"CDLBELTHOLD"]},
           'uncertain': {'ent': ['STOCH','KAMA','RSI20','RSI30',"CDLMARUBOZU","CDLCLOSINGMARUBOZU","CDL3WHITESOLDIERS","CDLLONGLINE","CDLENGULFING",
                                 "CDLMORNINGDOJISTAR","CDLHANGINGMAN","CDLKICKINGBYLENGTH_INV","CDLKICKING_INV"],
                         'ex': ["CDLHIKKAKE","CDL3LINESTRIKE","CDLBREAKAWAY"]}} 
        
        super().__init__(
            period,
            strat_arr=a,
            **kwargs )  
        
class StratH(UnderlyingStrat):    
    '''
    Strategy optimized to have the best yield used alone on stocks
    
    In long/both/both, Optimized on 2007-2023, CAC40 7.58 (3.13 bench), DAX 2.31 (1.68), NASDAQ 19.88 (12.1), IT 15.69 (8.44)
    '''
    def __init__(self,
                 period: numbers.Number,
                 **kwargs):
        
        a={'bull': {'ent': ['BBANDS','RSI20','RSI30','ULTOSC20','CDLENGULFING','CDLMORNINGSTAR','CDLKICKING_INV','CDLINVERTEDHAMMER',
   'CDLDARKCLOUDCOVER'],
                    'ex': ['CDLRISEFALL3METHODS', 'CDL3LINESTRIKE','CDLDARKCLOUDCOVER','CDLHIKKAKEMOD', 'CDLMORNINGDOJISTAR']},
 'bear': {'ent': ['STOCH', 'RSI20','ULTOSC25','CDLMARUBOZU','CDL3WHITESOLDIERS','CDLLONGLINE','CDLTAKURI','CDLMORNINGDOJISTAR',
   'CDLMORNINGSTAR','CDLHANGINGMAN','CDLKICKINGBYLENGTH_INV','CDLPIERCING','CDLHIKKAKEMOD','CDLTRISTAR','CDLDARKCLOUDCOVER',
   'CDLINNECK'],
  'ex': ['BBANDS','ULTOSC20','CDLRISEFALL3METHODS', 'CDL3LINESTRIKE', 'CDLABANDONEDBABY', 'CDL3BLACKCROWS','CDLUNIQUE3RIVER',
   'CDLMORNINGDOJISTAR']},
 'uncertain': {'ent': ['RSI20','RSI30','CDLMARUBOZU','CDLCLOSINGMARUBOZU','CDL3WHITESOLDIERS','CDLLONGLINE','CDLENGULFING',
   'CDLDRAGONFLYDOJI','CDLMORNINGDOJISTAR','CDLMORNINGSTAR','CDLHANGINGMAN','CDL3INSIDE','CDLKICKINGBYLENGTH_INV',
   'CDLKICKING_INV','CDLINVERTEDHAMMER','CDLSTICKSANDWICH','CDL3LINESTRIKE','CDL3BLACKCROWS'],
  'ex': ['ULTOSC20','CDLRISEFALL3METHODS','CDL3LINESTRIKE','CDLBREAKAWAY','CDLHIKKAKEMOD']}}
        
        super().__init__(
            period,
            strat_arr=a,
            **kwargs )         
       
class StratDivSecond(UnderlyingStrat):    
    '''
    Strategy optimized to have the best yield with divergence preselection
    '''
    def __init__(self,
                 period: numbers.Number,
                 **kwargs):
        
        a={'bull': {'ent': ['CDLINNECK', 'CDL3BLACKCROWS'],
                    'ex': ['WILLR','SUPERTREND','BBANDS','CDLBELTHOLD','CDLRISEFALL3METHODS','CDLEVENINGDOJISTAR',
                           'CDLUNIQUE3RIVER','CDLCOUNTERATTACK','CDLMORNINGDOJISTAR']},
            'bear': {'ent': ['CDL3BLACKCROWS'],
             'ex': ['STOCH','SUPERTREND','ULTOSC20','CDLCLOSINGMARUBOZU','CDLRISEFALL3METHODS','CDLUNIQUE3RIVER',
              'CDLCOUNTERATTACK']},
            'uncertain': {'ent': ['CDL3BLACKCROWS'],
             'ex': ['SUPERTREND','RSI20','ULTOSC20','ULTOSC25','CDLRISEFALL3METHODS','CDLABANDONEDBABY',
              'CDLHIKKAKEMOD','CDLUNIQUE3RIVER']}}
        
        super().__init__(
            period,
            strat_arr=a,
            **kwargs ) 


class StratIndex(UnderlyingStrat):    
    '''
    Strategy optimized to have the best yield used alone on index
    '''   
    def __init__(self,
                 period: numbers.Number,
        **kwargs):
        
        a={'bull': 
           {'ent':['MA','SUPERTREND','RSI30', "CDLLONGLINE","CDLENGULFING","CDLMORNINGDOJISTAR"],
            'ex': ['MA', "CDL3LINESTRIKE","CDL3BLACKCROWS"]
            },
           'bear': 
            {'ent':['MA','SUPERTREND','RSI20','RSI30',"CDLLONGLINE","CDLENGULFING","CDLMORNINGDOJISTAR"],
             'ex': ['MA', "CDLEVENINGSTAR","CDLBREAKAWAY","CDL3BLACKCROWS","CDLDARKCLOUDCOVER"] 
             },
            'uncertain': 
            {'ent': ['MA','STOCH',"CDLLONGLINE","CDLDRAGONFLYDOJI","CDLHANGINGMAN"],
             'ex':['SUPERTREND',  "CDLHIKKAKE","CDLBREAKAWAY", "CDLEVENINGDOJISTAR"]}
            }
  
        super().__init__(
            period,
            strat_arr=a,
            **kwargs )  

class StratIndexB(UnderlyingStrat):    
    '''
    Strategy optimized to have the best yield used alone on index
    '''   
    def __init__(self,
                 period: numbers.Number,
        **kwargs):
        
        a={'bull': 
           {'ent': ['KAMA',"CDLDRAGONFLYDOJI","CDL3INSIDE"],
            'ex': ["CDLBREAKAWAY","CDLABANDONEDBABY","CDLEVENINGSTAR"]
            },
           'bear': 
            {'ent':['KAMA','SUPERTREND','RSI30', "CDLMORNINGSTAR"],
             'ex': ['MA',"CDLABANDONEDBABY", "CDLEVENINGSTAR", "CDLSEPARATINGLINES","CDLDARKCLOUDCOVER"]
             },
            'uncertain': 
            {'ent': ['KAMA',"CDL3WHITESOLDIERS"],
             'ex': ['SUPERTREND',"CDLABANDONEDBABY", "CDLEVENINGSTAR", "CDLSEPARATINGLINES"]}
            }
        
        super().__init__(
            period,
            strat_arr=a,
            **kwargs )     
   

class StratKamaStochMatrendBbands(UnderlyingStrat):  
    '''
    As STOCHKAMA for bear and uncertain trend
    Use MA for bull, so if the 5 days smoothed price crosses the 15 days smoothed price, a signal is created
    
    Note: this strategy needs long time to be calculated
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
                             trend_key="bbands")
        self.get_output(s)  

class StratKamaStochMatrendMacdbbMacro(UnderlyingStrat):
    '''
    As StratKamaStochMatrendBbands but take care of the trend for the order direction
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

def function_to_res(
        f_name: str, 
        open_: np.array, 
        high: np.array, 
        low: np.array, 
        close: np.array,
        light: bool=None
        ) -> (np.array, np.array):
    '''
    Wrapper to call function from indicators based on their name

    Arguments
    ----------
        f_name: name of the function in indicators
        open_: open prices
        high: high prices
        low: low prices
        close: close prices
        light: for pattern, choose pattern normal or light
    '''
    f_callable=getattr(ic,f_name)
    dic={}

    for k in ["open_","close","high","low","light"]:
        if k in inspect.getfullargspec(f_callable.run).args:
            dic[k]=locals()[k]

    res = f_callable.run(**dic)
    return res.entries, res.exits

def strat_wrapper(
        open_: np.array,
        high: np.array, 
        low: np.array, 
        close: np.array, 
        close_ind: np.array,
        f_bull:str="VBTSTOCHKAMA", 
        f_bear:str="VBTSTOCHKAMA", 
        f_uncertain:str="VBTSTOCHKAMA",
        f_very_bull:str="VBTSTOCHKAMA", 
        f_very_bear:str="VBTSTOCHKAMA",
        trend_lim: numbers.Number=1.5, 
        trend_lim2: numbers.Number=10, 
        macro_trend_bool:bool=False,
        dir_bull:str="long", 
        dir_bear:str="short",
        dir_uncertain:str="both",
        trend_key:str="bbands",
        macro_trend_index:bool=False,
        light:bool=True):
    '''
    wrapper for the different strategy functions

    split the trend in 5 parts: very bear, bear, uncertain, bull and very bull
    set a strategy for each of them

    Arguments
    ----------
        open_: open prices
        high: high prices
        low: low prices
        close: close prices
        close_ind: close prices of the corresponding main index
        f_bull: strategy function to use during bull trend
        f_bear: strategy function to use during bear trend
        f_uncertain: strategy function to use during uncertain trend
        f_very_bull: strategy function to use during very bull trend
        f_very_bear: strategy function to use during very bear trend
        trend_lim: score of the trend between uncertain and bear/bull
        trend_lim2: score of the trend between bear/bull and very bear/very bull
        macro_trend_bool: differentiate the direction depending on the macro trend
        dir_bull: direction to use during bull trend
        dir_bear: direction to use during bear trend
        dir_uncertain: direction to use during uncertain trend
        trend_key: which trend function is to be used
        macro_trend_index: base the macro trend calculation on the main index only, or not
        light: for pattern, choose pattern normal or light
    '''
    
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
              if t.trend[ii]<=-trend_lim2:
                  temp_ent[ii] = ent_very_bull[ii]
                  temp_ex[ii] = ex_very_bull[ii] 
              elif t.trend[ii]>=trend_lim2:
                  temp_ent[ii] = ent_very_bear[ii]
                  temp_ex[ii] = ex_very_bear[ii]                   
              elif t.trend[ii]<-trend_lim:
                  temp_ent[ii] = ent_bull[ii]
                  temp_ex[ii] = ex_bull[ii] 
              elif t.trend[ii]>trend_lim:
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
                  if (temp!=0 and dir_bull not in ["both", "short"]):
                      exits_short[ii] = True
                  if (temp!=0 and dir_bull not in ["both", "long"]):
                      exits[ii] = True

                  if dir_bull in ["both", "short"]:
                      entries_short[ii] = temp_ex[ii]
                      exits_short[ii] = temp_ent[ii] 
                      
                  if dir_bull in ["both", "long"]:
                      entries[ii] = temp_ent[ii]
                      exits[ii] = temp_ex[ii]

                  temp=0
                  
              elif macro_trend[ii]==1:
                  if (temp!=1 and dir_bear not in ["both", "short"]):
                      exits_short[ii] = True
                  if (temp!=1 and dir_bear not in ["both", "long"]):
                      exits[ii] = True

                  if dir_bear in ["both", "short"]:
                      entries_short[ii] = temp_ex[ii]
                      exits_short[ii] = temp_ent[ii] 
                      
                  if dir_bear in ["both", "long"]:
                      entries[ii] = temp_ent[ii]
                      exits[ii] = temp_ex[ii]

                  temp=1
              else:
                  if (temp!=2 and dir_uncertain not in ["both", "short"]):
                      exits_short[ii] = True
                  if (temp!=2 and dir_uncertain not in ["both", "long"]):
                      exits[ii] = True
                  
                  if dir_uncertain in ["both", "short"]:
                      entries_short[ii] = temp_ex[ii]
                      exits_short[ii] = temp_ent[ii] 
                      
                  if dir_uncertain in ["both", "long"]:
                      entries[ii] = temp_ent[ii]
                      exits[ii] = temp_ex[ii]                  

                  temp=2
          else: #no macro trend
              if dir_uncertain in ["both", "short"]:
                  entries_short[ii] = temp_ex[ii]
                  exits_short[ii] = temp_ent[ii] 
                
              if dir_uncertain in ["both", "long"]:
                  entries[ii] = temp_ent[ii]
                  exits[ii] = temp_ex[ii]    
     
    return entries, exits, entries_short, exits_short, t.trend, macro_trend, t.kama, t.bb_bw, min_ind, max_ind  
  
STRATWRAPPER = vbt.IF(
     class_name='StratWrapper',
     short_name='st_wrapper',
     input_names=['high', 'low', 'close','open_','close_ind'],
     param_names=['f_bull', 'f_bear', 'f_uncertain','f_very_bull', 'f_very_bear','trend_lim', 
                  'trend_lim2', 
                  'macro_trend_bool','dir_bull',
                  'dir_bear','dir_uncertain','trend_key','macro_trend_index'],
     output_names=['entries', 'exits', 'entries_short', 'exits_short','trend','macro_trend',
                   'kama','bb_bw','min_ind', 'max_ind'] 
).with_apply_func(
     strat_wrapper, 
     takes_1d=True, 
     trend_lim=1.5,
     trend_lim2=10,
     macro_trend_bool=False,
     dir_bull="long", 
     dir_bear="short",
     dir_uncertain="both",
     f_bull="VBTSTOCHKAMA", 
     f_bear="VBTSTOCHKAMA", 
     f_uncertain="VBTSTOCHKAMA",
     f_very_bull="VBTSTOCHKAMA", 
     f_very_bear="VBTSTOCHKAMA", 
     trend_key="bbands",
     macro_trend_index=False,
     light=True
)         


