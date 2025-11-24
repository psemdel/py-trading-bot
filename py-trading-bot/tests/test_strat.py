#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 24 19:45:34 2022

@author: maxime
"""

import unittest
from core import strat
import vectorbtpro as vbt

class TestStrat(unittest.TestCase):
    @classmethod
    def setUpClass(self):  
        self.period="2007_2022_08"
        self.symbol_index="CAC40"
        
    def test_symbols_simple_to_complex(self):
        self.ust=strat.StratDiv2(self.period, symbol_index=self.symbol_index)
        self.ust.run()
        symbol_complex1=self.ust.symbols_simple_to_complex('AI.PA',"ent")
        self.assertEqual(symbol_complex1,"AI.PA")
        symbol_complex2=self.ust.symbols_simple_to_complex('AI.PA',"ex")
        self.assertEqual(symbol_complex2,"AI.PA")
        
        self.ust=strat.StratG(self.period, symbol_index=self.symbol_index)
        self.ust.run()
        symbol_complex1=self.ust.symbols_simple_to_complex('AI.PA',"ent")
        self.assertFalse(symbol_complex1=="AI.PA")
        self.assertTrue(type(symbol_complex1)==tuple)        
        symbol_complex2=self.ust.symbols_simple_to_complex('AI.PA',"ex")
        self.assertFalse(symbol_complex2=="AI.PA")
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
          
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[0]],2),1.01)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[1]],2),0.2)        
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[2]],2),2.65)  
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[6]],2),4.82)  

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
        

        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[0]],2),1.36)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[1]],2),-0.47)        
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[2]],2),3.23)  
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[6]],2),4.09) 
        
    def test_strat_kama_stoch_matrend_bbands(self): 
        self.ust=strat.StratKamaStochMatrendBbands(
            self.period, 
            symbol_index=self.symbol_index)
        self.ust.run()
        
        pf=vbt.Portfolio.from_signals(self.ust.close, self.ust.entries,self.ust.exits,
                                      short_entries=self.ust.entries_short,
                                      short_exits  =self.ust.exits_short)    
          
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[0]],2),2.33)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[1]],2),1.52)   
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[2]],2),4.26)  
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[6]],2),2.21)  


        
    def test_stratIndex(self):
        self.ust=strat.StratIndex(self.period, symbol_index=self.symbol_index)
        self.ust.run()
 
        pf=vbt.Portfolio.from_signals(self.ust.close, self.ust.entries,self.ust.exits,
                                      short_entries=self.ust.entries_short,
                                      short_exits  =self.ust.exits_short)  
        
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[0]],2),1.3)  
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[1]],2),-0.44) 
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[2]],2),3.21)  
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[3]],2),-0.37) 
        
        self.ust=strat.StratIndex(self.period, symbol_index=self.symbol_index,it_is_index=True)
        self.ust.run()
        pf=vbt.Portfolio.from_signals(self.ust.close, self.ust.entries,self.ust.exits,
                                      short_entries=self.ust.entries_short,
                                      short_exits  =self.ust.exits_short)         
        
        self.assertEqual(round(pf.get_total_return(),2),5.79) 
        
    def test_stratReal(self):
        self.ust=strat.StratReal(self.period, symbol_index=self.symbol_index)
        self.ust.run()
        
        pf=vbt.Portfolio.from_signals(self.ust.close, self.ust.entries,self.ust.exits,
                                      short_entries=self.ust.entries_short,
                                      short_exits  =self.ust.exits_short)
        
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[0]],2),-0.43)  
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[1]],2),0.11) 
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[2]],2),4.08) 
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[3]],2),-0.36) 

    def test_stratDiv2(self):
        self.ust=strat.StratDiv2(self.period, symbol_index=self.symbol_index)
        self.ust.run()
        
        pf=vbt.Portfolio.from_signals(self.ust.close, self.ust.entries,self.ust.exits,
                                      short_entries=self.ust.entries_short,
                                      short_exits  =self.ust.exits_short)  
        
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[0]],2),0.12) 
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[1]],2),0.16) 
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[2]],2),0.37) 
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[3]],2),-0.6) 
        
    def test_stratDiv(self):
        self.ust=strat.StratDiv(self.period, symbol_index=self.symbol_index)
        self.ust.run()
        
        pf=vbt.Portfolio.from_signals(self.ust.close, self.ust.entries,self.ust.exits,
                                      short_entries=self.ust.entries_short,
                                      short_exits  =self.ust.exits_short)  
        
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[0]],2),-0.57) 
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[1]],2),-0.19) 
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[2]],2),-0.22) 
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[3]],2),-0.85)         
if __name__ == '__main__':
    unittest.main()        
        
