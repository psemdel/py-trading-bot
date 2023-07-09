#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat May 14 22:36:16 2022

@author: maxime
"""
import vectorbtpro as vbt
import pandas as pd
import numpy as np
import sys

from core import strat
from core.strat import StratHold
from core.macro import VBTMACROTREND, VBTMACROTRENDPRD
import core.indicators as ic
#from core.common import save_vbt_both
from core.constants import short_to_sign, short_to_str

from trading_bot.settings import _settings
import logging
logger = logging.getLogger(__name__)
"""
Strategies with preselection
a) It select one, two,... actions
b) (optional) It applies a "one action" strategy on it

Note that I don't weight the portfolio, like in https://nbviewer.org/github/polakowo/vectorbt/blob/master/examples/PortfolioOptimization.ipynb
I just select one, two,... actions and put all my orders on them

Those strategies are home made (even though quite similar to classic one). For classic ones look at presel_classic
"""
def name_to_presel(
        pr_name: str, 
        period: str,
        **kwargs):
    
    PR=getattr(sys.modules[__name__],pr_name)
    pr=PR(period,**kwargs)
    pr.run()
    return pr

class Presel():
    def __init__(
            self,
            period: str,
            symbol_index=None,
            prd: bool=False,
            suffix: str="",
            actions: list=None,
            symbols: list=None,
            input_ust=None,
            vol=None,
            macd_tot=None,
            macro_trend_ind=None,
            macro_trend_select:str=None,
            macro_trend=None,
            macro_trend_ind_mod=None,
            dur=None,
            divergence=None,
            grow=None,
            exchange:str=None,
            ):
        """
        Strategies on one action, no preselection. For production and non production, to make the strats as child of the main one.

        So it determines entries and exits for one action to optimize the return

        Arguments
        ----------
            symbol_index: main index to be retrieved
            period: period of time in year for which we shall retrieve the data
            prd: for production or backtesting
            suffix: suffix for files
            actions: list of actions
            symbols: list of YF tickers
            input_st: input underlying strategy with already all data downloaded, avoid downloading the same several times
            vol: volatility signal
            macd_tot: macd signal
            macro_trend_ind: trend of the main index
            macro_trend_ind_mod: trend of the main index with modified threshold
            macro_trend_select: selection of the mod to use
            
            dur: duration in a KAMA direction
            divergence: divergence signal
            exchange: stock exchange name
        """
        self.suffix=suffix
        if self.suffix!="":
            self.suffix="_" + self.suffix
            
        for k in ["prd","symbol_index","period","vol","actions","symbols","macd_tot","macro_trend_ind","macro_trend_ind_mod",
                  "macro_trend_select", "dur", "divergence", "grow","exchange"]:
            setattr(self,k,locals()[k])

        if input_ust is not None:
            self.ust=input_ust
        else:
            if not self.prd:
                self.ust=StratHold(
                    self.period,
                    symbol_index=symbol_index,
                    suffix=suffix,
                    )
            else:
                self.ust=StratHold(
                    self.period,
                    actions=actions,
                    symbols=symbols,
                    prd=True,
                    suffix=suffix,
                   )

        for k, v in self.ust.__dict__.items():
            if k not in self.__dict__ or getattr(self, k) is None:
                setattr(self,k,v)

        self.init_sub()
        
    def init_sub(self):
        '''
        init some variables
        '''
        self.symbols_simple=self.close.columns.values
        
        self.candidates={
            "long":[[] for ii in range(len(self.close))],
            "short":[[] for ii in range(len(self.close))]
            }
        
        self.excluded=[]
        self.hold_dur={}
        
        self.start_capital=10000
        self.order_size=self.start_capital

        self.only_exit_ust=False
        self.no_ust=False
        self.calc_all=False #Normally on production, we rely on the state evaluate in the bot, 
                            #and not on a state recalculated, however for retard it proved to be 
                            #more secure to recalculate every time, to have less discrepancy between 
                            #backtesting and evaluation live. 
        self.blocked=False     #when the trend becomes short, no more candidate is added, but the stocks presently owned are sold by exit signal
        self.blocked_im=False  #when the trend becomes short, no more candidate is added, but the stocks presently owned are sold immediately
        self.reinit()
    
    def reinit(self):
        self.capital=self.start_capital        
        self.pf={
            "long":[],
            "short":[],
            "long_keep":[],
            "short_keep":[],
            }
        for k in ["entries","exits","exits_short","entries_short","entries2","exits2","exits_short2","entries_short2"]:
            setattr(self,k,pd.DataFrame.vbt.empty_like(self.close, fill_value=False))   
        
    def get_candidates(self):
        return self.candidates["long"][-1], self.candidates["short"][-1]   
        
    def symbols_simple_to_complex(self,symbol_simple,ent_or_ex):
        if "entries" not in self.ust.__dir__():
            self.ust.run()

        return self.ust.symbols_simple_to_complex(symbol_simple,ent_or_ex)
        #UnderlyingStrat
            
    def calculate(
            self,
            ii,
            short:bool=False,
            ): #day basis
        '''
        create buy/sell from candidates and underlying strategy
        
        no_ust means that the buy/sell will only depends on the candidates. So if a stock is in the candidates, it is entered. 
        If it is not anymore in candidates, it is exited.
        
        only_exit_ust consider only the candidates for the entry, but the underlying strategy for the exit.
        
        Arguments
        ----------
            ii: index
            short: order direction
        '''
        #all presel strat are monodirectionel
        #So if the trends reverse, the opposite direction should be empty
        #clean at the same time the excluded
        if short:
            for symbol_simple in self.pf["long"]:
                self.exits[symbol_simple].iloc[ii]=True
                self.capital+=self.order_size
                self.pf["long"].remove(symbol_simple)
            for symbol_simple in self.pf["short"]:
                if symbol_simple in self.excluded:
                    self.exits_short[symbol_simple].iloc[ii]=True
                    self.capital+=self.order_size
                    self.pf["short"].remove(symbol_simple)
        else:
            for symbol_simple in self.pf["short"]:
                self.exits_short[symbol_simple].iloc[ii]=True
                self.capital+=self.order_size
                self.pf["short"].remove(symbol_simple)
            for symbol_simple in self.pf["long"]:
                if symbol_simple in self.excluded:
                    self.exits[symbol_simple].iloc[ii]=True  
                    self.capital+=self.order_size
                    self.pf["long"].remove(symbol_simple)
                    
        #perform orders
        #exit
        for symbol_simple in self.pf[short_to_str[short]]:
            symbol_complex=self.symbols_simple_to_complex(symbol_simple,"ex")

            if ((self.ust.exits[symbol_complex].values[ii]) or  #not short and 
               (short and self.ust.exits_short[symbol_complex].values[ii]) or
                (self.no_ust and symbol_simple not in self.candidates[short_to_str[short]][ii])):
   
                self.pf[short_to_str[short]].remove(symbol_simple)
                self.capital+=self.order_size
                
                if short:
                    self.exits_short[symbol_simple].iloc[ii]=True 
                else:
                    self.exits[symbol_simple].iloc[ii]=True
                self.hold_dur[symbol_simple]=0
            else:
                self.hold_dur[symbol_simple]+=1 #for retard

        #entry
        for symbol_simple in self.candidates[short_to_str[short]][ii]:
            symbol_complex=self.symbols_simple_to_complex(symbol_simple,"ent")

            if (self.capital>=self.order_size and
                ((self.no_ust or self.only_exit_ust) or
                (not short and self.ust.entries[symbol_complex].values[ii]) or
                (short and self.ust.entries_short[symbol_complex].values[ii])) and
                symbol_simple not in self.excluded):

                self.pf[short_to_str[short]].append(symbol_simple)
                self.capital-=self.order_size
                
                if short:
                    self.entries_short[symbol_simple].iloc[ii]=True
                else:
                    self.entries[symbol_simple].iloc[ii]=True
      
                self.hold_dur[symbol_simple]=0
                            
    def presub(self,ii:int):
        '''
        Used in run to add a function there if needed
        '''
        pass
    
    def sorting(self, ii:int, **kwargs):
        print("sorting function is not defined at parent level")
        pass
    
    def supplementary_criterium(self,symbol_simple: str,ii: int,v,**kwargs)-> bool:
        '''
        Add a supplementary test to be checked before adding a candidate
        '''
        return True
    
    def underlying(self):
        '''
        Change the underlying strategy
        '''
        pass 
    
    def underlying_creator(self,f_name: str):
        '''
        Wrapper around underlying
        '''
        f=getattr(strat,f_name)
        if self.prd:
            self.ust=f(self.period,prd=True,input_ust=self.ust)
        else:
            self.ust=f(self.period,input_ust=self.ust)
        self.ust.run()

    def sub(
            self, 
            ii:int,
            short=False
            ) -> list:
        '''
        Function called at every step of the calculation, handle the filling of candidates array
        '''
        self.candidates[short_to_str[short]][ii]=[]
        self.sorting(ii, short=short)

        for e in self.sorted:
            symbol_simple=e[0]
   
            if (len(self.candidates[short_to_str[short]][ii])<self.max_candidates_nb and
               symbol_simple not in self.excluded and
               self.supplementary_criterium(symbol_simple, ii, e[1], short=short)
               ) :
               if ((not self.blocked and not self.blocked_im) or 
                   ((self.blocked or self.blocked_im) and not short)):

                   self.candidates[short_to_str[short]][ii].append(symbol_simple)

        return self.sorted #for display
    
    def run(self,**kwargs):
        '''
        Main function for presel
        '''
        self.underlying()
        if self.prd and not self.calc_all:
            ii=len(self.close)-1
            self.presub(ii)
            self.out=self.sub(ii,**kwargs)
        else:
            for ii in range(len(self.close.index)):
                self.presub(ii)
                self.out=self.sub(ii,**kwargs)
                self.calculate(ii,**kwargs)
        #save_vbt_both(self.close, self.entries, self.exits, self.entries_short, self.exits_short, suffix="hist6")

class PreselMacro(Presel):
    '''
    Parent class for preselection relying on trends
    '''
    def preliminary(self):
        if self.macro_trend_select=="ind_mod" and self.macro_trend_ind_mod is None:
            self.macro_trend_ind_mod=VBTMACROTREND.run(self.close_ind,threshold=0.03).macro_trend #theshold 3% is clearly better in this case than 4%
        if self.macro_trend_select=="ind" and self.macro_trend_ind is None:
            self.macro_trend_ind=VBTMACROTRENDPRD.run(self.close_ind).macro_trend
            
    def run(self,**kwargs):
        self.underlying()
        
        if self.prd and not self.calc_all:
            ii=len(self.close)-1
            
            if self.macro_trend_select=="ind_mod":
                short=(self.macro_trend_ind_mod.values[ii]==1)
            else:
                short=(self.macro_trend_ind.values[ii]==1)
                
            self.presub(ii)
            self.out=self.sub(ii,short=short,**kwargs)
        for ii in range(len(self.close.index)):
            if self.macro_trend_select=="ind_mod":
                short=(self.macro_trend_ind_mod.values[ii]==1)
            else:
                short=(self.macro_trend_ind.values[ii]==1)
            
            self.presub(ii)
            self.out=self.sub(ii,short=short,**kwargs)
            
            if self.blocked:
                self.calculate(ii,short=False,**kwargs)
            else: #self.blocked_im
                self.calculate(ii,short=short,**kwargs)
        return short #to be removed later

class PreselVol(Presel):
    '''
    Preselect stocks based on the volatility. The highest volatility is chosen.  
    '''
    def __init__(self,period: str,**kwargs):
        super().__init__(period,**kwargs)
        if self.vol is None:
            self.vol=ic.VBTNATR.run(self.high,self.low,self.close).natr
        self.max_candidates_nb=_settings["VOL_MAX_CANDIDATES_NB"]
    
    def underlying(self):
        self.underlying_creator("StratKamaStochMatrendBbands")
        
    def sorting(self,ii: int,**kwargs):
        v={}
        for symbol in self.close.columns.values:
            v[symbol]=self.vol[symbol].values[ii]
        self.sorted=sorted(v.items(), key=lambda tup: tup[1], reverse=True)

class PreselMacdVol(PreselVol):
    '''
    Preselect stocks based on the volatility. The highest volatility is chosen.  
    As supplementary criterium, the MACD must be positive for the long variant.
    '''
    def __init__(self,period: str,**kwargs):
        super().__init__(period,**kwargs)
        if self.macd_tot is None:
            self.macd_tot=vbt.MACD.run(self.close, macd_wtype='simple',signal_wtype='simple')
        self.max_candidates_nb=_settings["MACD_VOL_MAX_CANDIDATES_NB"]
        
    def supplementary_criterium(self,symbol_simple, ii,v, short=False):
        return self.macd_tot.macd[('simple','simple',symbol_simple)].values[ii]*short_to_sign[short]>0 

class PreselHistVol(PreselMacdVol):
    '''
    Preselect stocks based on the volatility. The highest volatility is chosen.  
    As supplementary criterium, the MACD must be positive for the long variant.
    '''
    def __init__(self,period: str,**kwargs):
        super().__init__(period,**kwargs)
        self.max_candidates_nb=_settings["HIST_VOL_MAX_CANDIDATES_NB"]
        
    def underlying(self):
        self.underlying_creator("StratF")           
    
    def supplementary_criterium(self,symbol_simple, ii,v, short=False):
        return self.macd_tot.hist[('simple','simple',symbol_simple)].values[ii]*short_to_sign[short]>0

class PreselMacdVolMacro(PreselMacdVol):
    def __init__(self,period: str,**kwargs):
        super().__init__(period,**kwargs)
        if self.macro_trend_select is None:
            self.macro_trend_select="ind"
        PreselMacro.preliminary(self)
    
    def run(self,**kwargs):
        PreselMacro.run(self,**kwargs)    

class PreselRetard(Presel):
    '''
    Calculate the number of day in a row when the smoother price of an action has been decreasing
    The action the longest duration is bought
    (Follow the loser) similar to RMR
    '''
    def __init__(self,period: str,**kwargs):
        super().__init__(period,**kwargs)
        if self.dur is None:
            self.dur=ic.VBTKAMATREND.run(self.close).duration
        self.max_candidates_nb=1
        self.no_ust=True
        self.calc_all=True
        self.last_short=False

    def sorting(
            self,
            ii: int, 
            short: bool=False,
            **kwargs
            ):
        
        v={}   
        for symbol in self.close.columns.values:
            v[symbol]=self.dur[symbol].values[ii]
            if symbol in self.excluded: #if exclude take the next
                if v[symbol]==0: #trend change
                    self.excluded.remove(symbol)
   
        self.sorted=sorted(v.items(), key=lambda tup: tup[1], reverse=not short)
        
    def presub(self,ii:int):
        for key in ["long","short"]:
            for s in self.pf[key]:
                if self.hold_dur[s] > _settings["RETARD_MAX_HOLD_DURATION"]:
                    self.excluded.append(s)

class PreselRetardMacro(PreselRetard):
    '''
    Like retard, but the long/short is decided in function of the macro trend
    '''
    def __init__(self,period: str,**kwargs):
        super().__init__(period,**kwargs)
        if self.macro_trend_select is None:
            self.macro_trend_select="ind_mod"
        PreselMacro.preliminary(self)
    
    def run(self,**kwargs):
        self.last_short=PreselMacro.run(self,**kwargs)

class PreselDivergence(Presel):
    '''
    This strategy measures the difference between the variation of each action smoothed price and 
    the variation of the corresponding smoothed price
    When the difference is negative, the action is bought. So the action which evolves lower than 
    the index is bought
    (Follow the loser)
    
    The buying criteria is the divergence, an underlying strategy determines the exit
    '''
    def __init__(self,period: str,**kwargs):
        super().__init__(period,**kwargs)
        self.only_exit_ust=True
        if self.divergence is None:
            self.divergence=ic.VBTDIVERGENCE.run(self.close,self.close_ind).out
        self.threshold=_settings["DIVERGENCE_THRESHOLD"]
        self.max_candidates_nb=1
        
    def underlying(self):
        self.underlying_creator("StratDiv")
        
    def sorting(
            self,
            ii: int, 
            short: bool=False,
            **kwargs
            ):
        
        v={}   
        for symbol in self.close.columns.values:
            v[symbol]=self.divergence[symbol].values[ii]
   
        self.sorted=sorted(v.items(), key=lambda tup: tup[1], reverse=short)
        
    def supplementary_criterium(self,symbol_simple, ii, v, short=False):
        if short:
            return v> self.threshold
        else:
            return v< -self.threshold
        
    def calc(self,**kwargs):
        #only exit
        self.calculate(only_exit_ust=True,**kwargs)

class PreselDivergenceBlocked(PreselDivergence):
    '''
    Like preselect_divergence, but the mechanism is blocked when macro_trend is bear
    Reverting the mechanism did not prove to be very rewarding for this strategy
    '''
    def __init__(self,period,**kwargs):
        super().__init__(period,**kwargs)
        if self.macro_trend_select is None:
            self.macro_trend_select="ind"
        PreselMacro.preliminary(self)
        self.blocked=True
            
    def run(self,**kwargs):
        PreselMacro.run(self,**kwargs)

class PreselDivergenceBlockedIm(PreselDivergenceBlocked):
    def __init__(self,period,**kwargs):
        super().__init__(period,**kwargs)   
        self.blocked=False
        self.blocked_im=True
### Slow ###
'''
Not called for production

Slow strategy re-actualise the candidates on a given frequency, typically every 10 days
The issue with strategy that reactualize the candidates every day is that the entry mechanism replace the one
from the underlying strategy.
'''

class PreselSlow(Presel):
    def __init__(self,period: str,**kwargs):
        super().__init__(period,**kwargs)

    def actualize(self, strategy):
        from orders.models import  get_candidates
        
        if self.exchange is None:
            raise ValueError("exchange not defined in actualize hist vol")
        cand=get_candidates(strategy,self.exchange) #
        cand.reset()
        return cand
        
    def run(
        self,
        short=False,
        **kwargs):
        
        self.underlying()
        if not self.prd:
            for ii in range(len(self.close.index)):
                if ii%self.frequency==0: #every 10 days
                    self.sorting(ii)
                    
                    if self.blocked:
                        if self.macro_trend_select=="ind_mod":
                            short=(self.macro_trend_ind_mod.values[ii]==1)
                        else:
                            short=(self.macro_trend_ind.values[ii]==1)

                    for e in self.sorted:
                        symbol_simple=e[0]
                        
                        if (len(self.candidates[short_to_str[short]][ii])<self.max_candidates_nb and
                           self.supplementary_criterium(symbol_simple, ii, e[1], short=short)
                           ):
                            if not self.blocked or (self.blocked and not short):
                                self.candidates[short_to_str[short]][ii].append(symbol_simple)
                else:
                    if not self.blocked or (self.blocked and not short):
                        self.candidates[short_to_str[short]][ii]=self.candidates[short_to_str[short]][ii-1]
                self.calculate(ii,**kwargs)   
      
class PreselVolSlow(PreselSlow):
    def __init__(self,period: str,**kwargs):
        super().__init__(period,**kwargs) 
        if self.vol is None:
            self.vol=ic.VBTNATR.run(self.high,self.low,self.close).natr
        self.frequency=_settings["VOL_SLOW_FREQUENCY"]
        self.max_candidates_nb=_settings["VOL_SLOW_MAX_CANDIDATES_NB"]
        
    def underlying(self):
        self.underlying_creator("StratF")
        
    def sorting(self,ii: int,**kwargs):
        PreselVol.sorting(self,ii)
    
class PreselMacdVolSlow(PreselVolSlow):
    def __init__(self,period,**kwargs):
        super().__init__(period,**kwargs)   
        if self.macd_tot is None:
            self.macd_tot=vbt.MACD.run(self.close, macd_wtype='simple',signal_wtype='simple')
        self.frequency=_settings["MACD_VOL_SLOW_FREQUENCY"]
        self.max_candidates_nb=_settings["MACD_VOL_SLOW_MAX_CANDIDATES_NB"]

    def underlying(self):
        self.underlying_creator("StratKamaStochMatrendBbands")
        
    def supplementary_criterium(self,symbol_simple, ii,v, short=False):
        return self.macd_tot.macd[('simple','simple',symbol_simple)].values[ii]*short_to_sign[short]>0 
        
class PreselHistVolSlow(PreselMacdVolSlow):
    def __init__(self,period,**kwargs):
        super().__init__(period,**kwargs)   
        self.frequency=_settings["HIST_VOL_SLOW_FREQUENCY"]  
        self.max_candidates_nb=_settings["HIST_VOL_SLOW_MAX_CANDIDATES_NB"]

    def underlying(self):
        self.underlying_creator("StratE")
         
    def supplementary_criterium(self,symbol_simple, ii,v, short=False):
        return self.macd_tot.hist[('simple','simple',symbol_simple)].values[ii]*short_to_sign[short]>0 
    
    def actualize(self):
        cand=super().actualize("hist_slow")
        short=False
        ii=-1
        
        self.sorting(ii)
        for e in self.sorted:
            symbol_simple=e[0]
            if (len(cand.retrieve())<self.max_candidates_nb and
               self.macd_tot.hist[('simple','simple',symbol_simple)].values[ii]*short_to_sign[short]>0):
                    cand.append(symbol_simple)   

class PreselRealMadrid(PreselSlow):
    '''
    Strategy that bet on the actions that growed the most in the past (Follow the winner)
    Bet on the one that usually win  
    '''
    def __init__(self,period,**kwargs):
        super().__init__(period,**kwargs) 
        self.distance=_settings["REALMADRID_DISTANCE"]
        if self.grow is None:
            self.grow=ic.VBTGROW.run(self.close,distance=self.distance,ma=True).out
        self.frequency=_settings["REALMADRID_FREQUENCY"]
        self.max_candidates_nb=_settings["REALMADRID_MAX_CANDIDATES_NB"]

    def underlying(self):
        self.underlying_creator("StratReal")

    def sorting(
            self,
            ii: int, 
            short: bool=False,
            **kwargs
            ):
        
        v={}   
        for symbol in self.close.columns.values:
            v[symbol]=self.grow[(self.distance,True,symbol)].values[ii]
   
        self.sorted=sorted(v.items(), key=lambda tup: tup[1], reverse=True)   
        
    def actualize(self):
        from orders.models import Excluded
        
        cand=super().actualize("realmadrid")
        try:
            self.excluded=Excluded.objects.get(name="realmadrid").retrieve()
        except:
            self.excluded=[]
            
        ii=-1
        
        self.sorting(ii)    
        for e in self.sorted:
            symbol_simple=e[0]
            if (len(cand.retrieve())<self.max_candidates_nb and
                symbol_simple not in self.excluded):
                cand.append(symbol_simple)   

class PreselRealMadridBlocked(PreselRealMadrid):
    def __init__(self,period,**kwargs):
        super().__init__(period,**kwargs) 
        if self.macro_trend_select is None:
            self.macro_trend_select="ind"
        PreselMacro.preliminary(self)
        self.blocked=True

class WQ(Presel):
    def __init__(
            self,
            period,
            **kwargs
            ):
        '''
        WQ uses the prebuild 101 Formulaic Alphas
        No underlying strategy is necessary
        '''
        super().__init__(period, **kwargs)
        
    def call_wqa(
            self, 
            nb: int):
        
        self.nb=nb
        self.out = vbt.wqa101(nb).run(
            open=self.open, 
            high=self.high,
            low=self.low, 
            close=self.close,
            volume=self.volume
            ).out

    ##create buy/sell from candidates
    def calculate(self): #day basis
        for ii in range(len(self.close.index)): #for each day
            if ii!=0:
                #sell
                for symbol_simple in self.pf:
                    if symbol_simple not in self.candidates["long"][ii]:
                        self.pf.remove(symbol_simple)
                        self.capital+=self.order_size
                        self.exits[symbol_simple].iloc[ii]=True
            
                #buy
                for symbol_simple in self.candidates["long"][ii]:
                    if self.capital>=self.order_size:
                        self.pf.append(symbol_simple)
                        self.capital-=self.order_size
                        self.entries[symbol_simple].iloc[ii]=True

    def def_cand(self):
        self.candidates={
            "long":[[] for ii in range(len(self.close))]
            }

        if self.nb in [1]:
            threshold= np.sum(self.out.iloc[0].values)/len(self.out.iloc[0].values)*1.1

        for ii in range(len(self.out)):
            try:
                ind_max=np.nanargmax(self.out.iloc[ii].values)
                if self.nb in [1]:
                    if self.out.iloc[ii,ind_max]>threshold:
                        symbol=self.out.columns[ind_max]
                        self.candidates["long"][ii].append(symbol)
                else:
                    symbol=self.out.columns[ind_max]
                    self.candidates["long"][ii].append(symbol) 
            except:
                pass
            
    def get_candidates(self):
        return self.candidates["long"][-1]



