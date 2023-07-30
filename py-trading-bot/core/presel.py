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

from core import strat, strat_legacy
from core.strat import StratHold
from core.macro import VBTMACROTREND, VBTMACROTRENDPRD
import core.indicators as ic
#from core.common import save_vbt_both
from core.constants import short_to_sign, short_to_str
from core.common import candidates_to_YF

from trading_bot.settings import _settings
import logging
logger = logging.getLogger(__name__)
logger_trade = logging.getLogger('trade')
"""
Strategies with preselection
a) It select one, two,... actions
b) (optional) It applies a "one action" strategy on it

Note that I don't weight the portfolio, like in https://nbviewer.org/github/polakowo/vectorbt/blob/master/examples/PortfolioOptimization.ipynb
I just select one, two,... actions and put all my orders on them

Those strategies are home made (even though quite similar to classic one). For classic ones look at presel_classic
"""
def name_to_ust_or_presel(
        ust_or_presel_name: str, 
        period: str,
        it_is_index:bool=False,
        st=None,
        **kwargs):
    '''
    Function to call class from strat or presel

    Arguments
    ----------
        ust_or_presel_name: Name of the underlying strategy or preselection strategy to be called
        period: period of time in year for which we shall retrieve the data
        it_is_index: is it indexes that are provided 
        st: strategy associated
    '''
    try:
        if ust_or_presel_name[:6]=="Presel" and not it_is_index: #Presel for index makes no sense
            if ust_or_presel_name[6:8].lower()=="wq":
                nb=int(ust_or_presel_name[8:])
                pr=PreselWQ(period,nb=nb,st=st,**kwargs)
            else:
                PR=getattr(sys.modules[__name__],ust_or_presel_name)
                pr=PR(period,st=st,**kwargs)
                
            pr.run()
            return pr
        elif ust_or_presel_name[:5]=="Strat":
            try:
                UST=getattr(strat,ust_or_presel_name)
            except:
                try:
                    UST=getattr(strat_legacy,ust_or_presel_name)
                except:
                    raise ValueError(ust_or_presel_name + " underlying strategy not found")
            ust=UST(period,st=st,it_is_index=it_is_index,**kwargs)
            ust.run()
            return ust
        else:
            print("Class " +ust_or_presel_name + " does not respect the convention of starting with Presel or Strat")
            return None
        
    except Exception as e:
          _, e_, exc_tb = sys.exc_info()
          print(e)
          print("line " + str(exc_tb.tb_lineno))
              
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
            st=None,
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
            st: strategy associated
        """
        self.suffix=suffix
        if self.suffix!="":
            self.suffix="_" + self.suffix
            
        for k in ["prd","symbol_index","period","vol","actions","symbols","macd_tot","macro_trend_ind","macro_trend_ind_mod",
                  "macro_trend_select", "dur", "divergence", "grow","exchange","st"]:
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

        self.symbols_simple=self.close.columns.values
        
        self.candidates={
            "long":[[] for ii in range(len(self.close))],
            "short":[[] for ii in range(len(self.close))]
            }
        
        self.excluded=[]
        self.hold_dur=0#{}
        
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
            }
        for k in ["entries","exits","exits_short","entries_short"]:
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
                self.hold_dur=0
            for symbol_simple in self.pf["short"]:
                if symbol_simple in self.excluded:
                    self.exits_short[symbol_simple].iloc[ii]=True
                    self.capital+=self.order_size
                    self.pf["short"].remove(symbol_simple)
                    self.hold_dur=0
        else:
            for symbol_simple in self.pf["short"]:
                self.exits_short[symbol_simple].iloc[ii]=True
                self.capital+=self.order_size
                self.pf["short"].remove(symbol_simple)
                self.hold_dur=0
            for symbol_simple in self.pf["long"]:
                if symbol_simple in self.excluded:
                    self.exits[symbol_simple].iloc[ii]=True  
                    self.capital+=self.order_size
                    self.pf["long"].remove(symbol_simple)
                    self.hold_dur=0
                    
        #perform orders
        #exit
        for symbol_simple in self.pf[short_to_str[short]]:
            symbol_complex=self.symbols_simple_to_complex(symbol_simple,"ex")

            if ((not self.no_ust and not short and self.ust.exits[symbol_complex].values[ii]) or  #not short and 
               (not self.no_ust and short and self.ust.exits_short[symbol_complex].values[ii]) or
                (self.no_ust and symbol_simple not in self.candidates[short_to_str[short]][ii])):
   
                self.pf[short_to_str[short]].remove(symbol_simple)
                self.capital+=self.order_size
                
                if short:
                    self.exits_short[symbol_simple].iloc[ii]=True 
                else:
                    self.exits[symbol_simple].iloc[ii]=True

                self.hold_dur=0 
            else:
                self.hold_dur+=1

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
        self.underlying_creator("StratG") 
        
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
        try:
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
            
        except Exception as e:
              import sys
              _, e_, exc_tb = sys.exc_info()
              print(e)
              print("line " + str(exc_tb.tb_lineno))
              
    def perform_cand_entry(self,r):
        candidates, _=self.get_candidates()
        r.ss_m.cand_to_quantity_entry(candidates_to_YF(self.ust.symbols_to_YF,candidates), self.st.name, False)
    
  
    def get_order(self,symbol: str, strategy:str):
        from django.db.models import Q
        from orders.models import Action, Strategy, Order
        """
        Search for an open order for an action
        
        Arguments
        ----------
        buy: should the order buy or sell the stock
        """
        action=Action.objects.get(symbol=symbol)
        c1 = Q(action=action)
        c2 = Q(active=True)
        st=Strategy.objects.get(name=strategy)
        c3 = Q(st)
        orders=Order.objects.filter(c1 & c2 & c3)

        if len(orders)>1:
            print("several active orders have been found for: "+symbol+" , check the database")
            
        if len(orders)==0:
            print("no order found for: "+symbol+" , check the database")
        else:
            return orders[0]
        #entering_date
        
    def get_last_exit(self, entering_date, symbol_complex_ent: str, symbol_complex_ex: str, short:bool=False):
        ii=len(self.entries[symbol_complex_ent].values)-1
        
        #look for an exit between the entry time and now
        while entering_date<self.entries.index[ii] and ii>0:
            if short:
                if (self.entries[symbol_complex_ent].values[-ii] or self.exits_short[symbol_complex_ent].values[-ii]) and not\
                (self.exits[symbol_complex_ex].values[-ii] or self.entries_short[symbol_complex_ex].values[-ii]):
                    return 0
            else:
                if (self.exits[symbol_complex_ex].values[-ii] or self.entries_short[symbol_complex_ex].values[-ii]) and not\
                    (self.entries[symbol_complex_ent].values[-ii] or self.exits_short[symbol_complex_ent].values[-ii]):
                    return 0
            ii-=1
            
        if short:
            return -1
        else:
            return 1
    
    def perform_only_exit(self,r):
        from orders.models import get_pf
 
        if not r.it_is_index and self.ust.exchange is not None: #index
            #even if the strategy is not anymore used, we should be able to exit
            for short in [True, False]:
                pf=get_pf(self.st.name,self.ust.exchange,short)

                ##only_exit_substrat
                if len(pf)>0:
                    r.concat("symbols in "+self.st.name+" strategy: " +str(pf) + " direction: "+ str(short))
                    for symbol in self.ust.symbols:
                        o=self.get_order(symbol, self.st.name)
                        symbol_complex_ex=self.ust.symbols_simple_to_complex(symbol,"ex")  
                        symbol_complex_ent=self.ust.symbols_simple_to_complex(symbol,"ent")  
                        
                        if self.ust.symbols_to_YF[symbol] in pf: 
                            target_order=self.get_last_exit(o.entering_date, symbol_complex_ent, symbol_complex_ex, short)
                            if target_order==0: #exit
                                r.ss_m.add_target_quantity(symbol,self.st.name, target_order)        
        
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
    
    def perform(self, r):
        candidates, candidates_short=self.get_candidates()
        
        if len(candidates)==0:
            short=True
            cand=candidates_short
        else:
            short=False
            cand=candidates

        for symbol in cand:
            symbol_complex= self.ust.symbols_simple_to_complex(symbol,"ent")
            if short:
                r.ss_m.ex_ent_to_target(
                    False,
                    False,
                    self.ust.exits[symbol_complex].values[-1],
                    self.ust.entries[symbol_complex].values[-1],
                    self.ust.symbols_to_YF[symbol], 
                    self.st.name
                    )
            else:
                r.ss_m.ex_ent_to_target(
                    self.ust.entries[symbol_complex].values[-1],
                    self.ust.exits[symbol_complex].values[-1],
                    False,
                    False,
                    self.ust.symbols_to_YF[symbol], 
                    self.st.name
                    )

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
                if self.hold_dur > _settings["RETARD_MAX_HOLD_DURATION"]:
                    self.excluded.append(s)
     
    def perform(self, r):
        candidates, candidates_short=self.get_candidates()
        
        if self.last_short:
            direction="short"
            candidates=candidates_short
        else:
            direction="long"

        r.concat("Retard, " + "direction " + direction + ", stockex: " + self.ust.exchange +\
                    ", action duration: " +str(self.out))
  
        r.ss_m.order_nosubstrat(candidates_to_YF(self.ust.symbols_to_YF,candidates), self.ust.exchange, "retard", self.last_short)
              
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

class PreselRetardKeep(Presel):
    '''
    Only the "keep" part of the strategy, so inheritence from PreselRetard
    '''
    def underlying(self):
        self.underlying_creator("StratG")    
    
    def run(self,**kwargs):
        '''
        No preselection and no sorting needed for RetardKeep
        '''
        self.underlying()
    
    def perform(self,r):
        #entry is handled by retard
        self.perform_only_exit(r)
        

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
        
        
    def perform(self, r):
        self.perform_only_exit(r)
        self.perform_cand_entry(r)

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
                
    def perform_entry(self,r):
        from orders.models import get_candidates #from the DB not this calculation
        
        if not r.it_is_index and self.ust.exchange is not None: 
            cand=get_candidates(self.st.name,self.ust.exchange).retrieve()

            for s in cand:
                if s in self.ust.symbols:
                    symbol_complex_ent=self.ust.symbols_simple_to_complex(s,"ent") 
                    r.ss_m.ex_ent_to_target(
                        self.ust.entries[symbol_complex_ent].values[-1],
                        self.ust.exits[symbol_complex_ent].values[-1],
                        False, #both strategy use only long
                        False,
                        self.ust.symbols_to_YF[s], 
                        self.st.name,
                        )    
                                    
    def perform(self, r):
        self.perform_only_exit(r)
        self.perform_entry(r)
        
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
        '''
        Actualize the candidates, so the stocks that can be trade by the underlying strats
        '''
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
        '''
        Actualize the candidates, so the stocks that can be trade by the underlying strats
        '''
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
        
        
class PreselWQ(Presel):
    '''
    WQ uses the prebuild 101 Formulaic Alphas
    No underlying strategy is necessary
    
    wq "1" is not supported
    '''
    def __init__(
            self,
            period: str,
            nb:int,
            **kwargs
            ):
        super().__init__(period,**kwargs)
        self.nb=nb
        #preliminary calculation
        self.wb_out = vbt.wqa101(self.nb).run(
            open=self.ust.open, 
            high=self.ust.high,
            low=self.ust.low, 
            close=self.ust.close,
            volume=self.ust.volume
            ).out
        self.no_ust=True
        
    def sub(
            self, 
            ii:int,
            ) -> list:
        '''
        Function called at every step of the calculation, handle the filling of candidates array
        '''
        if not np.isnan(self.wb_out.iloc[ii].values).all():
            ind_max=np.nanargmax(self.wb_out.iloc[ii].values)
            self.candidates["long"][ii]=[self.wb_out.columns[ind_max]]

    def underlying(self):
        pass
    
    def perform(self, r):
        '''
        Preselected actions strategy, using 101 Formulaic Alphas
        
        Arguments
       	----------
           ust: underlying strategy 
           exchange: name of the stock exchange
        '''
        from orders.models import Strategy, StockEx
        stock_ex=StockEx.objects.get(name=self.ust.exchange)

        strategy="wq"+str(self.nb)
        strats=Strategy.objects.filter(name=strategy) #normally there should be only one
        if len(strats)>0 and strats[0] in stock_ex.strategies_in_use.all():
            self.run()
            candidates=self.candidates["long"][-1]
            
            r.ss_m.order_nosubstrat(
                candidates_to_YF(self.ust.symbols_to_YF,candidates), 
                self.ust.exchange, 
                strategy,
                False,
                )

