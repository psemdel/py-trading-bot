#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Nov 16 13:09:48 2025

@author: maxime
"""
import vectorbtpro as vbt
from core.strat import UnderlyingStrat
from orders.models import get_exchange_actions
from core.caller import name_to_ust_or_presel
from trading_bot.settings import _settings
import numbers
from orders.models import StockEx

class SingleScanner(UnderlyingStrat):    
    def __init__(
            self,
            exchange:str,
            sec: str=None,
            period: str="3y",
            strategies_to_scan:list=_settings["STRATEGIES_TO_SCAN"],
            restriction:int=None,
            fees: numbers.Number=0,
            ):

        """
        To scan strategies for a given stock exchange
        

        Arguments
        ----------
            exchange: name of the stock exchange
            sec: sector of the stocks for which we write the report
            period: period of time for which we shall retrieve the data
            strategies_to_scan: strategies that will be considered in the scan
            restriction : limit the range for the calculation of the return to x market days, 
            fees: fees to be applyed during trades
        """
        actions=get_exchange_actions(exchange,sec=sec) 
        super().__init__(
            period=period,
            prd=True,
            actions=actions,
            )  

        for k in ["strategies_to_scan","period","restriction","fees","exchange","sec"]:
            setattr(self,k,locals()[k])

    def scan(
            self,
            res: dict={},
            **kwargs)-> dict:
        '''
        Calculate the performance of an underlying strategy in recent time
        
        Note: set your period to be significantly longer than the restriction to avoid calculation errors
        
        Arguments
        ----------
            res: result dictionary, progressively filed
        '''
        if self.sec is not None:
            res[self.sec]={}
        else:
            res[self.exchange]={}
    
        for p in self.strategies_to_scan:
            bti=name_to_ust_or_presel(p, None, self.period,input_ust=self)
    
            if self.restriction is not None and type(self.restriction)==int:
                pf=vbt.Portfolio.from_signals(bti.close[-self.restriction:], 
                                              bti.entries[-self.restriction:],
                                              bti.exits[-self.restriction:],
                                              short_entries=bti.entries_short[-self.restriction:],
                                              short_exits  =bti.exits_short[-self.restriction:],
                                              freq="1d",
                                              call_seq='auto',
                                              cash_sharing=True,
                                              fees=self.fees
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
                                              fees=self.fees
                                     )
            
            if self.sec is not None:
                res[self.sec][p]=float(round(pf.get_total_return(),2))
            else:
                res[self.exchange][p]=float(round(pf.get_total_return(),2))
        return res        
            
class Scanner():
    def __init__(
            self,
            list_of_exchanges:list=["XETRA","Nasdaq","NYSE"],  
            list_of_sector:list=["it"],
            strategies_to_scan:list=_settings["STRATEGIES_TO_SCAN"],
            period: str="3y",
            restriction:int=None,
            fees: numbers.Number=0,
            ):
        
        """
        To scan several strategies for sveral stock exchanges
        

        Arguments
        ----------
            list_of_exchanges: list of names of the stock exchange
            sec: sector of the stocks for which we write the report
            period: period of time for which we shall retrieve the data
            strategies_to_scan: strategies that will be considered in the scan
            restriction : limit the range for the calculation of the return to x market days, 
            fees: fees to be applyed during trades
        """        

        for k in ["list_of_exchanges","list_of_sector","strategies_to_scan","period","restriction","fees"]:
            setattr(self,k,locals()[k])

    def scan_all(self):
        res={}
        
        for exchange in self.list_of_exchanges:
            s_ex=StockEx.objects.get(name=exchange)
            
            if s_ex.presel_at_sector_level:
                for sec in self.list_of_sector:
                    single_scanner=SingleScanner(
                        exchange,
                        sec=sec,
                        period=self.period,
                        strategies_to_scan=self.strategies_to_scan,
                        restriction=self.restriction,
                        fees=self.fees
                        )
            else:
                single_scanner=SingleScanner(
                    exchange,
                    None,
                    period=self.period,
                    strategies_to_scan=self.strategies_to_scan,
                    restriction=self.restriction,
                    fees=self.fees
                    )
                
            res=single_scanner.scan(res)
        return res
            