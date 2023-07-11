#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 24 19:45:34 2022

@author: maxime
"""

import unittest
from core import strat, macro
import vectorbtpro as vbt

class TestStrat(unittest.TestCase):
    @classmethod
    def setUpClass(self):  
        self.period="2007_2022_08"
        self.symbol_index="CAC40"
        
    def test_symbols_simple_to_complex(self):
        self.ust=strat.StratDiv(self.period, symbol_index=self.symbol_index)
        self.ust.run()
        symbol_complex1=self.ust.symbols_simple_to_complex('AI',"ent")
        self.assertEqual(symbol_complex1,"AI")
        symbol_complex2=self.ust.symbols_simple_to_complex('AI',"ex")
        self.assertEqual(symbol_complex2,"AI")
        
        self.ust=strat.StratG(self.period, symbol_index=self.symbol_index)
        self.ust.run()
        symbol_complex1=self.ust.symbols_simple_to_complex('AI',"ent")
        self.assertFalse(symbol_complex1=="AI")
        self.assertTrue(type(symbol_complex1)==tuple)        
        symbol_complex2=self.ust.symbols_simple_to_complex('AI',"ex")
        self.assertFalse(symbol_complex2=="AI")
        self.assertTrue(type(symbol_complex2)==tuple)       

    def test_strat_kama_stoch_matrend_macdbb_macro(self): 
        self.ust=strat.StratKamaStochMatrendMacdbbMacro(
            self.period, 
            symbol_index=self.symbol_index, 
            dir_bull="long",
            dir_uncertain="long",
            dir_bear="both")
        self.ust.run()

        pf=vbt.Portfolio.from_signals(self.ust.close, self.ust.entries,self.ust.exits,
                                      short_entries=self.ust.entries_short,
                                      short_exits  =self.ust.exits_short)    
          
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[0]],2),1.22)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[1]],2),0.16)        
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[2]],2),2.89)  
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[6]],2),4.07)  

        self.ust=strat.StratKamaStochMatrendMacdbbMacro(
            self.period, 
            symbol_index=self.symbol_index, 
            dir_bull="long",
            dir_uncertain="both",
            dir_bear="both")
        self.ust.run()
        
        pf=vbt.Portfolio.from_signals(self.ust.close, self.ust.entries,self.ust.exits,
                                      short_entries=self.ust.entries_short,
                                      short_exits  =self.ust.exits_short)   
        

        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[0]],2),2.05)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[1]],2),-0.50)        
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[2]],2),3.64)  
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[6]],2),2.66) 
        
    def test_strat_kama_stoch_matrend_bbands(self): 
        self.ust=strat.StratKamaStochMatrendBbands(
            self.period, 
            symbol_index=self.symbol_index)
        self.ust.run()
        
        pf=vbt.Portfolio.from_signals(self.ust.close, self.ust.entries,self.ust.exits,
                                      short_entries=self.ust.entries_short,
                                      short_exits  =self.ust.exits_short)    
          
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[0]],2),2.38)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[1]],2),1.39)   
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[2]],2),2.78)  
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[6]],2),2.02)  
        
    def test_stratF(self):
        self.ust=strat.StratF(self.period, symbol_index=self.symbol_index)
        self.ust.run()
        
        pf=vbt.Portfolio.from_signals(self.ust.close, self.ust.entries,self.ust.exits,
                                      short_entries=self.ust.entries_short,
                                      short_exits  =self.ust.exits_short)   
        
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[0]],2),-0.6) 
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[1]],2),0.19) 
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[2]],2),7.47) 
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[3]],2),-0.22) 
        
    def test_stratIndex(self):
        self.ust=strat.StratIndex(self.period, symbol_index=self.symbol_index)
        self.ust.run()
 
        pf=vbt.Portfolio.from_signals(self.ust.close, self.ust.entries,self.ust.exits,
                                      short_entries=self.ust.entries_short,
                                      short_exits  =self.ust.exits_short)  
        
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[0]],2),1.7) 
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[1]],2),-0.53) 
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[2]],2),1.41) 
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[3]],2),-0.74) 
        
        self.ust=strat.StratIndex(self.period, symbol_index=self.symbol_index,it_is_index=True)
        self.ust.run()
        pf=vbt.Portfolio.from_signals(self.ust.close, self.ust.entries,self.ust.exits,
                                      short_entries=self.ust.entries_short,
                                      short_exits  =self.ust.exits_short)         
        
        self.assertEqual(round(pf.get_total_return(),2),5.72) 
        
    def test_stratReal(self):
        self.ust=strat.StratReal(self.period, symbol_index=self.symbol_index)
        self.ust.run()
        
        pf=vbt.Portfolio.from_signals(self.ust.close, self.ust.entries,self.ust.exits,
                                      short_entries=self.ust.entries_short,
                                      short_exits  =self.ust.exits_short)
        
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[0]],2),-0.44) 
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[1]],2),-0.19) 
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[2]],2),3.72) 
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[3]],2),-0.12) 

    def test_stratDiv(self):
        self.ust=strat.StratDiv(self.period, symbol_index=self.symbol_index)
        self.ust.run()
        
        pf=vbt.Portfolio.from_signals(self.ust.close, self.ust.entries,self.ust.exits,
                                      short_entries=self.ust.entries_short,
                                      short_exits  =self.ust.exits_short)  
        
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[0]],2),0.01)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[1]],2),0.07)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[2]],2),1.09)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[3]],2),-0.53) 
        
if __name__ == '__main__':
    unittest.main()        
        
