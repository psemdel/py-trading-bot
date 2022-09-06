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
    def setUp(self):
        self.st=strat.Strat("CAC40","2007_2022","test")  
        
    def test_ext_major(self):
        t=macro.VBTMACROTREND.run(self.st.close)
        
        self.assertEqual(t.macro_trend['AC'].values[-1],1)
        self.assertEqual(t.macro_trend['AI'].values[-1],-1)
        self.assertEqual(t.macro_trend['ORA'].values[-1],0)  
        
    def test_strat_kama_stoch(self):
        self.st.strat_kama_stoch()
        
        pf=vbt.Portfolio.from_signals(self.st.close, self.st.entries,self.st.exits,
                                      short_entries=self.st.entries_short,
                                      short_exits  =self.st.exits_short)
        
        self.assertEqual(round(pf.get_total_return()[('VBTSTOCHKAMA',100,False,'long','AC')],2),0.90)
        self.assertEqual(round(pf.get_total_return()[('VBTSTOCHKAMA',100,False,'long','AI')],2),1.16)
        self.assertEqual(round(pf.get_total_return()[('VBTSTOCHKAMA',100,False,'long','AIR')],2),5.27)
        self.assertEqual(round(pf.get_total_return()[('VBTSTOCHKAMA',100,False,'long','BNP')],2),4.18)
        
    def test_strat_pattern_light(self):   
        self.st.strat_pattern_light()
        
        pf=vbt.Portfolio.from_signals(self.st.close, self.st.entries,self.st.exits,
                                      short_entries=self.st.entries_short,
                                      short_exits  =self.st.exits_short)       
        
        
        self.assertEqual(round(pf.get_total_return()[('VBTPATTERN',100,False,'long','AC')],2),-0.33)
        self.assertEqual(round(pf.get_total_return()[('VBTPATTERN',100,False,'long','AI')],2),-0.16)
        self.assertEqual(round(pf.get_total_return()[('VBTPATTERN',100,False,'long','AIR')],2),1.62)
        self.assertEqual(round(pf.get_total_return()[('VBTPATTERN',100,False,'long','BNP')],2),3.10)
     
    def test_strat_kama_stoch_matrend_bbands(self):   
        self.st.strat_kama_stoch_matrend_bbands()
        
        pf=vbt.Portfolio.from_signals(self.st.close, self.st.entries,self.st.exits,
                                      short_entries=self.st.entries_short,
                                      short_exits  =self.st.exits_short)              


        self.assertEqual(round(pf.get_total_return()[('VBTMA', 'VBTSTOCHKAMA', 'VBTSTOCHKAMA', 'VBTMA', 'VBTSTOCHKAMA', 1.5, False, 'long', 'bbands', 'AC')],2),1.97)
        self.assertEqual(round(pf.get_total_return()[('VBTMA', 'VBTSTOCHKAMA', 'VBTSTOCHKAMA', 'VBTMA', 'VBTSTOCHKAMA', 1.5, False, 'long', 'bbands', 'AI')],2),1.20)        
        self.assertEqual(round(pf.get_total_return()[('VBTMA', 'VBTSTOCHKAMA', 'VBTSTOCHKAMA', 'VBTMA', 'VBTSTOCHKAMA', 1.5, False, 'long', 'bbands', 'AIR')],2),3.51)  
        self.assertEqual(round(pf.get_total_return()[('VBTMA', 'VBTSTOCHKAMA', 'VBTSTOCHKAMA', 'VBTMA', 'VBTSTOCHKAMA', 1.5, False, 'long', 'bbands', 'BNP')],2),2.22)  

    def test_strat_kama_stoch_super_bbands(self):   
        self.st.strat_kama_stoch_super_bbands()
        
        pf=vbt.Portfolio.from_signals(self.st.close, self.st.entries,self.st.exits,
                                      short_entries=self.st.entries_short,
                                      short_exits  =self.st.exits_short)              


        self.assertEqual(round(pf.get_total_return()[('VBTSUPERTRENDMA', 'VBTSTOCHKAMA', 'VBTSTOCHKAMA', 'VBTSUPERTRENDMA', 'VBTSTOCHKAMA', 1.5, False, 'long', 'bbands', 'AC')],2),2.23)
        self.assertEqual(round(pf.get_total_return()[('VBTSUPERTRENDMA', 'VBTSTOCHKAMA', 'VBTSTOCHKAMA', 'VBTSUPERTRENDMA', 'VBTSTOCHKAMA', 1.5, False, 'long', 'bbands', 'AI')],2),1.16)        
        self.assertEqual(round(pf.get_total_return()[('VBTSUPERTRENDMA', 'VBTSTOCHKAMA', 'VBTSTOCHKAMA', 'VBTSUPERTRENDMA', 'VBTSTOCHKAMA', 1.5, False, 'long', 'bbands', 'AIR')],2),6.50)  
        self.assertEqual(round(pf.get_total_return()[('VBTSUPERTRENDMA', 'VBTSTOCHKAMA', 'VBTSTOCHKAMA', 'VBTSUPERTRENDMA', 'VBTSTOCHKAMA', 1.5, False, 'long', 'bbands', 'BNP')],2),2.26)  

    def test_strat_kama_stoch_matrend_macdbb(self):   
        self.st.strat_kama_stoch_matrend_macdbb()
        
        pf=vbt.Portfolio.from_signals(self.st.close, self.st.entries,self.st.exits,
                                      short_entries=self.st.entries_short,
                                      short_exits  =self.st.exits_short)              

        self.assertEqual(round(pf.get_total_return()[('VBTMA', 'VBTSTOCHKAMA', 'VBTSTOCHKAMA', 'VBTMA', 'VBTSTOCHKAMA', 1.5, False, 'long', 'macdbb', 'AC')],2),2.60)
        self.assertEqual(round(pf.get_total_return()[('VBTMA', 'VBTSTOCHKAMA', 'VBTSTOCHKAMA', 'VBTMA', 'VBTSTOCHKAMA', 1.5, False, 'long', 'macdbb', 'AI')],2),0.40)        
        self.assertEqual(round(pf.get_total_return()[('VBTMA', 'VBTSTOCHKAMA', 'VBTSTOCHKAMA', 'VBTMA', 'VBTSTOCHKAMA', 1.5, False, 'long', 'macdbb', 'AIR')],2),6.66)  
        self.assertEqual(round(pf.get_total_return()[('VBTMA', 'VBTSTOCHKAMA', 'VBTSTOCHKAMA', 'VBTMA', 'VBTSTOCHKAMA', 1.5, False, 'long', 'macdbb', 'BNP')],2),3.07)  

    def test_strat_kama_stoch_super_macdbb(self):   
        self.st.strat_kama_stoch_super_macdbb()
        
        pf=vbt.Portfolio.from_signals(self.st.close, self.st.entries,self.st.exits,
                                      short_entries=self.st.entries_short,
                                      short_exits  =self.st.exits_short)              

        self.assertEqual(round(pf.get_total_return()[('VBTSUPERTRENDMA', 'VBTSTOCHKAMA', 'VBTSTOCHKAMA', 'VBTSUPERTRENDMA', 'VBTSTOCHKAMA', 1.5, False, 'long', 'macdbb', 'AC')],2),2.74)
        self.assertEqual(round(pf.get_total_return()[('VBTSUPERTRENDMA', 'VBTSTOCHKAMA', 'VBTSTOCHKAMA', 'VBTSUPERTRENDMA', 'VBTSTOCHKAMA', 1.5, False, 'long', 'macdbb', 'AI')],2),0.53)        
        self.assertEqual(round(pf.get_total_return()[('VBTSUPERTRENDMA', 'VBTSTOCHKAMA', 'VBTSTOCHKAMA', 'VBTSUPERTRENDMA', 'VBTSTOCHKAMA', 1.5, False, 'long', 'macdbb', 'AIR')],2),4.70)  
        self.assertEqual(round(pf.get_total_return()[('VBTSUPERTRENDMA', 'VBTSTOCHKAMA', 'VBTSTOCHKAMA', 'VBTSUPERTRENDMA', 'VBTSTOCHKAMA', 1.5, False, 'long', 'macdbb', 'BNP')],2),3.12)  

    def test_strat_pattern_light_matrend_bbands(self):   
        self.st.strat_pattern_light_matrend_bbands()
        
        pf=vbt.Portfolio.from_signals(self.st.close, self.st.entries,self.st.exits,
                                      short_entries=self.st.entries_short,
                                      short_exits  =self.st.exits_short)              

        self.assertEqual(round(pf.get_total_return()[('VBTMA', 'VBTPATTERN', 'VBTPATTERN', 'VBTMA', 'VBTPATTERN', 1.5, False, 'long', 'bbands', 'AC')],2),-0.44)
        self.assertEqual(round(pf.get_total_return()[('VBTMA', 'VBTPATTERN', 'VBTPATTERN', 'VBTMA', 'VBTPATTERN', 1.5, False, 'long', 'bbands', 'AI')],2),-0.05)        
        self.assertEqual(round(pf.get_total_return()[('VBTMA', 'VBTPATTERN', 'VBTPATTERN', 'VBTMA', 'VBTPATTERN', 1.5, False, 'long', 'bbands', 'AIR')],2),2.10)  
        self.assertEqual(round(pf.get_total_return()[('VBTMA', 'VBTPATTERN', 'VBTPATTERN', 'VBTMA', 'VBTPATTERN', 1.5, False, 'long', 'bbands', 'BNP')],2),0.83)  

    def test_strat_pattern_light_super_bbands(self):   
        self.st.strat_pattern_light_super_bbands()
        
        pf=vbt.Portfolio.from_signals(self.st.close, self.st.entries,self.st.exits,
                                      short_entries=self.st.entries_short,
                                      short_exits  =self.st.exits_short)              

        self.assertEqual(round(pf.get_total_return()[('VBTSUPERTRENDMA', 'VBTPATTERN', 'VBTPATTERN', 'VBTSUPERTRENDMA', 'VBTPATTERN', 1.5, False, 'long', 'bbands', 'AC')],2),-0.43)
        self.assertEqual(round(pf.get_total_return()[('VBTSUPERTRENDMA', 'VBTPATTERN', 'VBTPATTERN', 'VBTSUPERTRENDMA', 'VBTPATTERN', 1.5, False, 'long', 'bbands', 'AI')],2),-0.09)        
        self.assertEqual(round(pf.get_total_return()[('VBTSUPERTRENDMA', 'VBTPATTERN', 'VBTPATTERN', 'VBTSUPERTRENDMA', 'VBTPATTERN', 1.5, False, 'long', 'bbands', 'AIR')],2),2.59)  
        self.assertEqual(round(pf.get_total_return()[('VBTSUPERTRENDMA', 'VBTPATTERN', 'VBTPATTERN', 'VBTSUPERTRENDMA', 'VBTPATTERN', 1.5, False, 'long', 'bbands', 'BNP')],2),1.17)  

    def test_strat_pattern_light_matrend_macdbb(self):   
        self.st.strat_pattern_light_matrend_macdbb()
        
        pf=vbt.Portfolio.from_signals(self.st.close, self.st.entries,self.st.exits,
                                      short_entries=self.st.entries_short,
                                      short_exits  =self.st.exits_short)              

        self.assertEqual(round(pf.get_total_return()[('VBTMA', 'VBTPATTERN', 'VBTPATTERN', 'VBTMA', 'VBTPATTERN', 1.5, False, 'long', 'macdbb', 'AC')],2),0.12)
        self.assertEqual(round(pf.get_total_return()[('VBTMA', 'VBTPATTERN', 'VBTPATTERN', 'VBTMA', 'VBTPATTERN', 1.5, False, 'long', 'macdbb', 'AI')],2),-0.30)        
        self.assertEqual(round(pf.get_total_return()[('VBTMA', 'VBTPATTERN', 'VBTPATTERN', 'VBTMA', 'VBTPATTERN', 1.5, False, 'long', 'macdbb', 'AIR')],2),1.73)  
        self.assertEqual(round(pf.get_total_return()[('VBTMA', 'VBTPATTERN', 'VBTPATTERN', 'VBTMA', 'VBTPATTERN', 1.5, False, 'long', 'macdbb', 'BNP')],2),1.81)  

    def test_strat_pattern_light_super_macdbb(self):   
        self.st.strat_pattern_light_super_macdbb()
        
        pf=vbt.Portfolio.from_signals(self.st.close, self.st.entries,self.st.exits,
                                      short_entries=self.st.entries_short,
                                      short_exits  =self.st.exits_short)              

        self.assertEqual(round(pf.get_total_return()[('VBTSUPERTRENDMA', 'VBTPATTERN', 'VBTPATTERN', 'VBTSUPERTRENDMA', 'VBTPATTERN', 1.5, False, 'long', 'macdbb', 'AC')],2),0.06)
        self.assertEqual(round(pf.get_total_return()[('VBTSUPERTRENDMA', 'VBTPATTERN', 'VBTPATTERN', 'VBTSUPERTRENDMA', 'VBTPATTERN', 1.5, False, 'long', 'macdbb', 'AI')],2),-0.35)        
        self.assertEqual(round(pf.get_total_return()[('VBTSUPERTRENDMA', 'VBTPATTERN', 'VBTPATTERN', 'VBTSUPERTRENDMA', 'VBTPATTERN', 1.5, False, 'long', 'macdbb', 'AIR')],2),1.34)  
        self.assertEqual(round(pf.get_total_return()[('VBTSUPERTRENDMA', 'VBTPATTERN', 'VBTPATTERN', 'VBTSUPERTRENDMA', 'VBTPATTERN', 1.5, False, 'long', 'macdbb', 'BNP')],2),2.03)  

    def test_strat_careful_super_bbands(self): 
        self.st.strat_careful_super_bbands()
        
        pf=vbt.Portfolio.from_signals(self.st.close, self.st.entries,self.st.exits,
                                      short_entries=self.st.entries_short,
                                      short_exits  =self.st.exits_short)              

        self.assertEqual(round(pf.get_total_return()[('VBTSUPERTRENDMA', 'VBTPATTERN', 'VBTPATTERN', 'VBTVERYBULL', 'VBTVERYBEAR', 1.5, False, 'long', 'bbands', 'AC')],2),-0.41)
        self.assertEqual(round(pf.get_total_return()[('VBTSUPERTRENDMA', 'VBTPATTERN', 'VBTPATTERN', 'VBTVERYBULL', 'VBTVERYBEAR', 1.5, False, 'long', 'bbands', 'AI')],2),-0.29)        
        self.assertEqual(round(pf.get_total_return()[('VBTSUPERTRENDMA', 'VBTPATTERN', 'VBTPATTERN', 'VBTVERYBULL', 'VBTVERYBEAR', 1.5, False, 'long', 'bbands', 'AIR')],2),1.54)  
        self.assertEqual(round(pf.get_total_return()[('VBTSUPERTRENDMA', 'VBTPATTERN', 'VBTPATTERN', 'VBTVERYBULL', 'VBTVERYBEAR', 1.5, False, 'long', 'bbands', 'BNP')],2),1.48)  

    def test_strat_kama_stoch_matrend_bbands_macro(self): 
        self.st.strat_kama_stoch_matrend_bbands_macro(macro_trend_bull="long",macro_trend_uncertain="long",macro_trend_bear="both")
        
        pf=vbt.Portfolio.from_signals(self.st.close, self.st.entries,self.st.exits,
                                      short_entries=self.st.entries_short,
                                      short_exits  =self.st.exits_short)              

        self.assertEqual(round(pf.get_total_return()[('VBTMA', 'VBTSTOCHKAMA', 'VBTSTOCHKAMA', 'VBTMA', 'VBTSTOCHKAMA', 1.5, True, 'long', 'both', 'long','bbands',False, 'AC')],2),0.64)
        self.assertEqual(round(pf.get_total_return()[('VBTMA', 'VBTSTOCHKAMA', 'VBTSTOCHKAMA', 'VBTMA', 'VBTSTOCHKAMA', 1.5, True, 'long', 'both', 'long','bbands',False, 'AI')],2),1.15)        
        self.assertEqual(round(pf.get_total_return()[('VBTMA', 'VBTSTOCHKAMA', 'VBTSTOCHKAMA', 'VBTMA', 'VBTSTOCHKAMA', 1.5, True, 'long', 'both', 'long','bbands',False, 'AIR')],2),3.13)  
        self.assertEqual(round(pf.get_total_return()[('VBTMA', 'VBTSTOCHKAMA', 'VBTSTOCHKAMA', 'VBTMA', 'VBTSTOCHKAMA', 1.5, True, 'long', 'both', 'long','bbands',False,'BNP')],2),1.67)  

        self.st.strat_kama_stoch_matrend_bbands_macro(macro_trend_bull="long",macro_trend_uncertain="both",macro_trend_bear="both")
        
        pf=vbt.Portfolio.from_signals(self.st.close, self.st.entries,self.st.exits,
                                      short_entries=self.st.entries_short,
                                      short_exits  =self.st.exits_short)   
        
        self.assertEqual(round(pf.get_total_return()[('VBTMA', 'VBTSTOCHKAMA', 'VBTSTOCHKAMA', 'VBTMA', 'VBTSTOCHKAMA', 1.5, True, 'long', 'both', 'both','bbands',False, 'AC')],2),1.20)
        self.assertEqual(round(pf.get_total_return()[('VBTMA', 'VBTSTOCHKAMA', 'VBTSTOCHKAMA', 'VBTMA', 'VBTSTOCHKAMA', 1.5, True, 'long', 'both', 'both','bbands',False, 'AI')],2),-0.06)        
        self.assertEqual(round(pf.get_total_return()[('VBTMA', 'VBTSTOCHKAMA', 'VBTSTOCHKAMA', 'VBTMA', 'VBTSTOCHKAMA', 1.5, True, 'long', 'both', 'both','bbands',False, 'AIR')],2),1.67)  
        self.assertEqual(round(pf.get_total_return()[('VBTMA', 'VBTSTOCHKAMA', 'VBTSTOCHKAMA', 'VBTMA', 'VBTSTOCHKAMA', 1.5, True, 'long', 'both', 'both','bbands',False, 'BNP')],2),2.68) 

    def test_strat_kama_stoch_matrend_macdbb_macro(self): 
        self.st.strat_kama_stoch_matrend_macdbb_macro(macro_trend_bull="long",macro_trend_uncertain="long",macro_trend_bear="both")
        
        pf=vbt.Portfolio.from_signals(self.st.close, self.st.entries,self.st.exits,
                                      short_entries=self.st.entries_short,
                                      short_exits  =self.st.exits_short)              

        self.assertEqual(round(pf.get_total_return()[('VBTMA', 'VBTSTOCHKAMA', 'VBTSTOCHKAMA', 'VBTMA', 'VBTSTOCHKAMA', 1.5, True, 'long', 'both', 'long','macdbb',False, 'AC')],2),1.45)
        self.assertEqual(round(pf.get_total_return()[('VBTMA', 'VBTSTOCHKAMA', 'VBTSTOCHKAMA', 'VBTMA', 'VBTSTOCHKAMA', 1.5, True, 'long', 'both', 'long','macdbb',False, 'AI')],2),0.03)        
        self.assertEqual(round(pf.get_total_return()[('VBTMA', 'VBTSTOCHKAMA', 'VBTSTOCHKAMA', 'VBTMA', 'VBTSTOCHKAMA', 1.5, True, 'long', 'both', 'long','macdbb',False, 'AIR')],2),6.12)  
        self.assertEqual(round(pf.get_total_return()[('VBTMA', 'VBTSTOCHKAMA', 'VBTSTOCHKAMA', 'VBTMA', 'VBTSTOCHKAMA', 1.5, True, 'long', 'both', 'long','macdbb',False,'BNP')],2),4.77)  

        self.st.strat_kama_stoch_matrend_macdbb_macro(macro_trend_bull="long",macro_trend_uncertain="both",macro_trend_bear="both")
        
        pf=vbt.Portfolio.from_signals(self.st.close, self.st.entries,self.st.exits,
                                      short_entries=self.st.entries_short,
                                      short_exits  =self.st.exits_short)   
        
        self.assertEqual(round(pf.get_total_return()[('VBTMA', 'VBTSTOCHKAMA', 'VBTSTOCHKAMA', 'VBTMA', 'VBTSTOCHKAMA', 1.5, True, 'long', 'both', 'both','macdbb',False, 'AC')],2),2.78)
        self.assertEqual(round(pf.get_total_return()[('VBTMA', 'VBTSTOCHKAMA', 'VBTSTOCHKAMA', 'VBTMA', 'VBTSTOCHKAMA', 1.5, True, 'long', 'both', 'both','macdbb',False, 'AI')],2),-0.52)        
        self.assertEqual(round(pf.get_total_return()[('VBTMA', 'VBTSTOCHKAMA', 'VBTSTOCHKAMA', 'VBTMA', 'VBTSTOCHKAMA', 1.5, True, 'long', 'both', 'both','macdbb',False, 'AIR')],2),4.61)  
        self.assertEqual(round(pf.get_total_return()[('VBTMA', 'VBTSTOCHKAMA', 'VBTSTOCHKAMA', 'VBTMA', 'VBTSTOCHKAMA', 1.5, True, 'long', 'both', 'both','macdbb',False, 'BNP')],2),5.43) 

    def test_strat_kama_stoch_macro(self): 
        self.st.strat_kama_stoch_macro(macro_trend_bull="long",macro_trend_uncertain="long",macro_trend_bear="both")
        
        pf=vbt.Portfolio.from_signals(self.st.close, self.st.entries,self.st.exits,
                                      short_entries=self.st.entries_short,
                                      short_exits  =self.st.exits_short)  


        self.assertEqual(round(pf.get_total_return()[('VBTSTOCHKAMA',100, True, 'long', 'both', 'long',False, 'AC')],2),0.02)
        self.assertEqual(round(pf.get_total_return()[('VBTSTOCHKAMA', 100, True, 'long', 'both', 'long',False, 'AI')],2),0.89)        
        self.assertEqual(round(pf.get_total_return()[('VBTSTOCHKAMA', 100, True, 'long', 'both', 'long',False, 'AIR')],2),3.54)  
        self.assertEqual(round(pf.get_total_return()[( 'VBTSTOCHKAMA', 100, True, 'long', 'both', 'long',False,'BNP')],2),9.32)  

    def test_strat_pattern_light_macro(self): 
        self.st.strat_pattern_light_macro(macro_trend_bull="long",macro_trend_uncertain="long",macro_trend_bear="both")
        
        pf=vbt.Portfolio.from_signals(self.st.close, self.st.entries,self.st.exits,
                                      short_entries=self.st.entries_short,
                                      short_exits  =self.st.exits_short)  

        self.assertEqual(round(pf.get_total_return()[('VBTPATTERN',100, True, 'long', 'both', 'long',False, 'AC')],2),-0.71)
        self.assertEqual(round(pf.get_total_return()[('VBTPATTERN', 100, True, 'long', 'both', 'long',False, 'AI')],2),-0.51)        
        self.assertEqual(round(pf.get_total_return()[('VBTPATTERN', 100, True, 'long', 'both', 'long',False, 'AIR')],2),0.19)  
        self.assertEqual(round(pf.get_total_return()[( 'VBTPATTERN', 100, True, 'long', 'both', 'long',False,'BNP')],2),2.81)  


if __name__ == '__main__':
    unittest.main()        
        
