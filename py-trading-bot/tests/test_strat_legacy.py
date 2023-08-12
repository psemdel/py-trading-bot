#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 24 19:45:34 2022

@author: maxime
"""

from django.test import TestCase
from core import strat_legacy
import vectorbtpro as vbt

class TestStrat(TestCase):
    @classmethod
    def setUpClass(self):  
        super().setUpClass()
        self.period="2007_2022_08"
        self.symbol_index="CAC40"
        
    def test_strat_kama_stoch(self):
        self.ust=strat_legacy.StratKamaStoch(self.period, symbol_index=self.symbol_index)
        self.ust.run()
        
        pf=vbt.Portfolio.from_signals(self.ust.close, self.ust.entries,self.ust.exits,
                                      short_entries=self.ust.entries_short,
                                      short_exits  =self.ust.exits_short)  

        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[0]],2),1.04)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[1]],2),1.4)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[2]],2),4.78)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[6]],2),4.72)
        
    def test_strat_pattern_light(self):   
        self.ust=strat_legacy.StratPatternLight(self.period, symbol_index=self.symbol_index)
        self.ust.run()
        
        pf=vbt.Portfolio.from_signals(self.ust.close, self.ust.entries,self.ust.exits,
                                      short_entries=self.ust.entries_short,
                                      short_exits  =self.ust.exits_short)     
        
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[0]],2),0.63)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[1]],2),2.73)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[2]],2),1.11)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[6]],2),0.28)
     
    def test_strat_kama_stoch_super_bbands(self):   
        self.ust=strat_legacy.StratKamaStochSuperBbands(self.period, symbol_index=self.symbol_index)
        self.ust.run()
        
        pf=vbt.Portfolio.from_signals(self.ust.close, self.ust.entries,self.ust.exits,
                                      short_entries=self.ust.entries_short,
                                      short_exits  =self.ust.exits_short)              

        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[0]],2),2.46)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[1]],2),1.23)        
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[2]],2),5.89)  
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[6]],2),2.21)  

    def test_strat_kama_stoch_matrend_macdbb(self):   
        self.ust=strat_legacy.StratKamaStochMatrendMacdbb(self.period, symbol_index=self.symbol_index)
        self.ust.run()
        
        pf=vbt.Portfolio.from_signals(self.ust.close, self.ust.entries,self.ust.exits,
                                      short_entries=self.ust.entries_short,
                                      short_exits  =self.ust.exits_short)   
            
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[0]],2),1.82)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[1]],2),0.5)        
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[2]],2),5.51)  
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[6]],2),2.84)  

    def test_strat_kama_stoch_super_macdbb(self):
        self.ust=strat_legacy.StratKamaStochSuperMacdbb(self.period, symbol_index=self.symbol_index)
        self.ust.run()
        
        pf=vbt.Portfolio.from_signals(self.ust.close, self.ust.entries,self.ust.exits,
                                      short_entries=self.ust.entries_short,
                                      short_exits  =self.ust.exits_short)               

        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[0]],2),1.77)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[1]],2),0.7)        
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[2]],2),4.29)  
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[6]],2),3.83)  

    def test_strat_pattern_light_matrend_bbands(self):   
        self.ust=strat_legacy.StratPatternLightMatrendBbands(self.period, symbol_index=self.symbol_index)
        self.ust.run()
        
        pf=vbt.Portfolio.from_signals(self.ust.close, self.ust.entries,self.ust.exits,
                                      short_entries=self.ust.entries_short,
                                      short_exits  =self.ust.exits_short)               

        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[0]],2),0.56)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[1]],2),2.34)        
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[2]],2),1.85)  
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[6]],2),-0.22)  

    def test_strat_pattern_light_super_bbands(self): 
        self.ust=strat_legacy.StratPatternLightSuperBbands(self.period, symbol_index=self.symbol_index)
        self.ust.run()
        
        pf=vbt.Portfolio.from_signals(self.ust.close, self.ust.entries,self.ust.exits,
                                      short_entries=self.ust.entries_short,
                                      short_exits  =self.ust.exits_short)              

        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[0]],2),0.41)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[1]],2),2.55)        
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[2]],2),1.53)  
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[6]],2),0.46)  

    def test_strat_pattern_light_matrend_macdbb(self): 
        self.ust=strat_legacy.StratPatternLightMatrendMacdbb(self.period, symbol_index=self.symbol_index)
        self.ust.run()
        
        pf=vbt.Portfolio.from_signals(self.ust.close, self.ust.entries,self.ust.exits,
                                      short_entries=self.ust.entries_short,
                                      short_exits  =self.ust.exits_short)             

        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[0]],2),0.14)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[1]],2),0.52)        
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[2]],2),2.19)  
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[6]],2),-0.61)  

    def test_strat_pattern_light_super_macdbb(self): 
        self.ust=strat_legacy.StratPatternLightSuperMacdbb(self.period, symbol_index=self.symbol_index)
        self.ust.run()
        
        pf=vbt.Portfolio.from_signals(self.ust.close, self.ust.entries,self.ust.exits,
                                      short_entries=self.ust.entries_short,
                                      short_exits  =self.ust.exits_short)              

        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[0]],2),0.13) 
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[1]],2),0.93)        
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[2]],2),1.40)  
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[6]],2),-0.48)  

    def test_strat_careful_super_bbands(self):
        self.ust=strat_legacy.StratCarefulSuperBbands(self.period, symbol_index=self.symbol_index)
        self.ust.run()
        
        pf=vbt.Portfolio.from_signals(self.ust.close, self.ust.entries,self.ust.exits,
                                      short_entries=self.ust.entries_short,
                                      short_exits  =self.ust.exits_short)              

        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[0]],2),-0.48)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[1]],2),0.79)        
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[2]],2),-0.17)  
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[6]],2),0.06)  

    def test_strat_kama_stoch_matrend_bbands_macro(self):
        self.ust=strat_legacy.StratKamaStochMatrendBbandsMacro(
            self.period, 
            symbol_index=self.symbol_index,
            dir_bull="long",
            dir_uncertain="long",
            dir_bear="both")
        self.ust.run()
        
        pf=vbt.Portfolio.from_signals(self.ust.close, self.ust.entries,self.ust.exits,
                                      short_entries=self.ust.entries_short,
                                      short_exits  =self.ust.exits_short)              

        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[0]],2),0.93)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[1]],2),1.39)        
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[2]],2),0.64)  
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[6]],2),1.35)  

        self.ust=strat_legacy.StratKamaStochMatrendBbandsMacro(
            self.period, 
            symbol_index=self.symbol_index,
            dir_bull="long",
            dir_uncertain="both",
            dir_bear="both")
        self.ust.run()
        
        pf=vbt.Portfolio.from_signals(self.ust.close, self.ust.entries,self.ust.exits,
                                      short_entries=self.ust.entries_short,
                                      short_exits  =self.ust.exits_short)   
        
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[0]],2),1.92)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[1]],2),0.1)        
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[2]],2),0.79)  
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[6]],2),1.73) 

    def test_strat_kama_stoch_macro(self): 
        self.ust=strat_legacy.StratKamaStochMacro(
            self.period, 
            symbol_index=self.symbol_index,
            dir_bull="long",
            dir_uncertain="long",
            dir_bear="both")
        self.ust.run()
        
        pf=vbt.Portfolio.from_signals(self.ust.close, self.ust.entries,self.ust.exits,
                                      short_entries=self.ust.entries_short,
                                      short_exits  =self.ust.exits_short)   
    
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[0]],2),0.01)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[1]],2),1.07)        
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[2]],2),1.2)  
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[6]],2),9.71)  
    
    def test_strat_pattern_light_macro(self): 
        self.ust=strat_legacy.StratPatternLightMacro(
            self.period, 
            symbol_index=self.symbol_index,
            dir_bull="long",
            dir_uncertain="long",
            dir_bear="both")
        self.ust.run()
        
        pf=vbt.Portfolio.from_signals(self.ust.close, self.ust.entries,self.ust.exits,
                                      short_entries=self.ust.entries_short,
                                      short_exits  =self.ust.exits_short)    
    
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[0]],2),0.98)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[1]],2),2.62)        
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[2]],2),0.51)  
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[6]],2),-0.07)          

