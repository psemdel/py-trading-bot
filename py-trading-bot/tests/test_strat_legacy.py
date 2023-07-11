#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 24 19:45:34 2022

@author: maxime
"""

import unittest
from core import strat_legacy
import vectorbtpro as vbt

class TestStrat(unittest.TestCase):
    @classmethod
    def setUpClass(self):  
        self.period="2007_2022_08"
        self.symbol_index="CAC40"
        
    def test_strat_kama_stoch(self):
        self.ust=strat_legacy.StratKamaStoch(self.period, symbol_index=self.symbol_index)
        self.ust.run()
        
        pf=vbt.Portfolio.from_signals(self.ust.close, self.ust.entries,self.ust.exits,
                                      short_entries=self.ust.entries_short,
                                      short_exits  =self.ust.exits_short)  

        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[0]],2),1.04)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[1]],2),1.35)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[2]],2),4.62)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[6]],2),4.73)
        
    def test_strat_pattern_light(self):   
        self.ust=strat_legacy.StratPatternLight(self.period, symbol_index=self.symbol_index)
        self.ust.run()
        
        pf=vbt.Portfolio.from_signals(self.ust.close, self.ust.entries,self.ust.exits,
                                      short_entries=self.ust.entries_short,
                                      short_exits  =self.ust.exits_short)     
        
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[0]],2),0.61)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[1]],2),2.42)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[2]],2),1.17)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[6]],2),0.20)
     
    def test_strat_kama_stoch_super_bbands(self):   
        self.ust=strat_legacy.StratKamaStochSuperBbands(self.period, symbol_index=self.symbol_index)
        self.ust.run()
        
        pf=vbt.Portfolio.from_signals(self.ust.close, self.ust.entries,self.ust.exits,
                                      short_entries=self.ust.entries_short,
                                      short_exits  =self.ust.exits_short)              

        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[0]],2),2.47)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[1]],2),1.19)        
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[2]],2),5.70)  
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[6]],2),2.21)  

    def test_strat_kama_stoch_matrend_macdbb(self):   
        self.ust=strat_legacy.StratKamaStochMatrendMacdbb(self.period, symbol_index=self.symbol_index)
        self.ust.run()
        
        pf=vbt.Portfolio.from_signals(self.ust.close, self.ust.entries,self.ust.exits,
                                      short_entries=self.ust.entries_short,
                                      short_exits  =self.ust.exits_short)   
            
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[0]],2),1.83)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[1]],2),0.45)        
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[2]],2),5.10)  
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[6]],2),2.84)  

    def test_strat_kama_stoch_super_macdbb(self):
        self.ust=strat_legacy.StratKamaStochSuperMacdbb(self.period, symbol_index=self.symbol_index)
        self.ust.run()
        
        pf=vbt.Portfolio.from_signals(self.ust.close, self.ust.entries,self.ust.exits,
                                      short_entries=self.ust.entries_short,
                                      short_exits  =self.ust.exits_short)               

        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[0]],2),1.78)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[1]],2),0.64)        
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[2]],2),3.96)  
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[6]],2),3.84)  

    def test_strat_pattern_light_matrend_bbands(self):   
        self.ust=strat_legacy.StratPatternLightMatrendBbands(self.period, symbol_index=self.symbol_index)
        self.ust.run()
        
        pf=vbt.Portfolio.from_signals(self.ust.close, self.ust.entries,self.ust.exits,
                                      short_entries=self.ust.entries_short,
                                      short_exits  =self.ust.exits_short)               

        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[0]],2),0.54)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[1]],2),2.24)        
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[2]],2),1.94)  
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[6]],2),-0.26)  

    def test_strat_pattern_light_super_bbands(self): 
        self.ust=strat_legacy.StratPatternLightSuperBbands(self.period, symbol_index=self.symbol_index)
        self.ust.run()
        
        pf=vbt.Portfolio.from_signals(self.ust.close, self.ust.entries,self.ust.exits,
                                      short_entries=self.ust.entries_short,
                                      short_exits  =self.ust.exits_short)              

        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[0]],2),0.4)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[1]],2),2.44)        
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[2]],2),1.61)  
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[6]],2),0.37)  

    def test_strat_pattern_light_matrend_macdbb(self): 
        self.ust=strat_legacy.StratPatternLightMatrendMacdbb(self.period, symbol_index=self.symbol_index)
        self.ust.run()
        
        pf=vbt.Portfolio.from_signals(self.ust.close, self.ust.entries,self.ust.exits,
                                      short_entries=self.ust.entries_short,
                                      short_exits  =self.ust.exits_short)             

        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[0]],2),0.16)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[1]],2),0.52)        
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[2]],2),2.05)  
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[6]],2),-0.64)  

    def test_strat_pattern_light_super_macdbb(self): 
        self.ust=strat_legacy.StratPatternLightSuperMacdbb(self.period, symbol_index=self.symbol_index)
        self.ust.run()
        
        pf=vbt.Portfolio.from_signals(self.ust.close, self.ust.entries,self.ust.exits,
                                      short_entries=self.ust.entries_short,
                                      short_exits  =self.ust.exits_short)              

        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[0]],2),0.12) 
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[1]],2),0.95)        
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[2]],2),1.29)  
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[6]],2),-0.52)  

    def test_strat_careful_super_bbands(self):
        self.ust=strat_legacy.StratCarefulSuperBbands(self.period, symbol_index=self.symbol_index)
        self.ust.run()
        
        pf=vbt.Portfolio.from_signals(self.ust.close, self.ust.entries,self.ust.exits,
                                      short_entries=self.ust.entries_short,
                                      short_exits  =self.ust.exits_short)              

        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[0]],2),-0.48)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[1]],2),0.77)        
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[2]],2),-0.16)  
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[6]],2),0.03)  

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

        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[0]],2),0.94)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[1]],2),1.35)        
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[2]],2),0.60)  
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[6]],2),1.36)  

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
        
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[0]],2),1.93)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[1]],2),0.08)        
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[2]],2),0.74)  
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
    
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[0]],2),0.02)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[1]],2),1.03)        
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[2]],2),1.14)  
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[6]],2),9.73)  
    
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
    
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[0]],2),0.96)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[1]],2),2.33)        
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[2]],2),0.55)  
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[6]],2),-0.13)          
if __name__ == '__main__':
    unittest.main()        
        
