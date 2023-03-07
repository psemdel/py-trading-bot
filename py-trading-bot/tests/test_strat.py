#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 24 19:45:34 2022

@author: maxime
"""

import unittest
from core import strat, macro, strat_legacy
import vectorbtpro as vbt

class TestStrat(unittest.TestCase):
    @classmethod
    def setUpClass(self):  
        self.st=strat.Strat("CAC40","2007_2022_08","test") 
        self.st_legacy=strat_legacy.StratLegacy("CAC40","2007_2022_08","test") 
        
    def test_ext_major(self):
        t=macro.VBTMACROTREND.run(self.st.close)
        
        self.assertEqual(t.macro_trend['AC'].values[-1],1)
        self.assertEqual(t.macro_trend['AI'].values[-1],0)
        self.assertEqual(t.macro_trend['ORA'].values[-1],0)  
        
    def test_strat_kama_stoch(self):
        self.st_legacy.strat_kama_stoch()
        
        pf=vbt.Portfolio.from_signals(self.st_legacy.close, self.st_legacy.entries,self.st_legacy.exits,
                                      short_entries=self.st_legacy.entries_short,
                                      short_exits  =self.st_legacy.exits_short) 

        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[0]],2),1.04)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[1]],2),1.35)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[2]],2),4.62)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[6]],2),4.73)
        
    def test_strat_pattern_light(self):   
        self.st_legacy.strat_pattern_light()
        
        pf=vbt.Portfolio.from_signals(self.st_legacy.close, self.st_legacy.entries,self.st_legacy.exits,
                                      short_entries=self.st_legacy.entries_short,
                                      short_exits  =self.st_legacy.exits_short)     
        
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[0]],2),0.61)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[1]],2),2.42)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[2]],2),1.17)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[6]],2),0.20)
     
    def test_strat_kama_stoch_matrend_bbands(self):   
        self.st_legacy.strat_kama_stoch_matrend_bbands()
        
        pf=vbt.Portfolio.from_signals(self.st_legacy.close, self.st_legacy.entries,self.st_legacy.exits,
                                      short_entries=self.st_legacy.entries_short,
                                      short_exits  =self.st_legacy.exits_short)             

        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[0]],2),2.38)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[1]],2),1.39)        
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[2]],2),2.78)  
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[6]],2),2.02)  

    def test_strat_kama_stoch_super_bbands(self):   
        self.st_legacy.strat_kama_stoch_super_bbands()
        
        pf=vbt.Portfolio.from_signals(self.st_legacy.close, self.st_legacy.entries,self.st_legacy.exits,
                                      short_entries=self.st_legacy.entries_short,
                                      short_exits  =self.st_legacy.exits_short)             

        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[0]],2),2.47)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[1]],2),1.19)        
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[2]],2),5.70)  
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[6]],2),2.21)  

    def test_strat_kama_stoch_matrend_macdbb(self):   
        self.st_legacy.strat_kama_stoch_matrend_macdbb()
        
        pf=vbt.Portfolio.from_signals(self.st_legacy.close, self.st_legacy.entries,self.st_legacy.exits,
                                      short_entries=self.st_legacy.entries_short,
                                      short_exits  =self.st_legacy.exits_short)  
            
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[0]],2),1.83)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[1]],2),0.45)        
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[2]],2),5.10)  
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[6]],2),2.84)  

    def test_strat_kama_stoch_super_macdbb(self):   
        self.st_legacy.strat_kama_stoch_super_macdbb()
        
        pf=vbt.Portfolio.from_signals(self.st_legacy.close, self.st_legacy.entries,self.st_legacy.exits,
                                      short_entries=self.st_legacy.entries_short,
                                      short_exits  =self.st_legacy.exits_short)              

        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[0]],2),1.78)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[1]],2),0.64)        
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[2]],2),3.96)  
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[6]],2),3.84)  

    def test_strat_pattern_light_matrend_bbands(self):   
        self.st_legacy.strat_pattern_light_matrend_bbands()
        
        pf=vbt.Portfolio.from_signals(self.st_legacy.close, self.st_legacy.entries,self.st_legacy.exits,
                                      short_entries=self.st_legacy.entries_short,
                                      short_exits  =self.st_legacy.exits_short)              

        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[0]],2),0.54)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[1]],2),2.24)        
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[2]],2),1.94)  
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[6]],2),-0.26)  

    def test_strat_pattern_light_super_bbands(self):   
        self.st_legacy.strat_pattern_light_super_bbands()
        
        pf=vbt.Portfolio.from_signals(self.st_legacy.close, self.st_legacy.entries,self.st_legacy.exits,
                                      short_entries=self.st_legacy.entries_short,
                                      short_exits  =self.st_legacy.exits_short)              

        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[0]],2),0.4)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[1]],2),2.44)        
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[2]],2),1.61)  
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[6]],2),0.37)  

    def test_strat_pattern_light_matrend_macdbb(self):   
        self.st_legacy.strat_pattern_light_matrend_macdbb()
        
        pf=vbt.Portfolio.from_signals(self.st_legacy.close, self.st_legacy.entries,self.st_legacy.exits,
                                      short_entries=self.st_legacy.entries_short,
                                      short_exits  =self.st_legacy.exits_short)              

        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[0]],2),0.16)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[1]],2),0.52)        
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[2]],2),2.05)  
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[6]],2),-0.64)  

    def test_strat_pattern_light_super_macdbb(self):   
        self.st_legacy.strat_pattern_light_super_macdbb()
        
        pf=vbt.Portfolio.from_signals(self.st_legacy.close, self.st_legacy.entries,self.st_legacy.exits,
                                      short_entries=self.st_legacy.entries_short,
                                      short_exits  =self.st_legacy.exits_short)              

        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[0]],2),0.12) 
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[1]],2),0.95)        
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[2]],2),1.29)  
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[6]],2),-0.52)  

    def test_strat_careful_super_bbands(self): 
        self.st_legacy.strat_careful_super_bbands()
        
        pf=vbt.Portfolio.from_signals(self.st_legacy.close, self.st_legacy.entries,self.st_legacy.exits,
                                      short_entries=self.st_legacy.entries_short,
                                      short_exits  =self.st_legacy.exits_short)             

        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[0]],2),-0.48)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[1]],2),0.77)        
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[2]],2),-0.16)  
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[6]],2),0.03)  

    def test_strat_kama_stoch_matrend_bbands_macro(self): 
        self.st_legacy.strat_kama_stoch_matrend_bbands_macro(macro_trend_bull="long",macro_trend_uncertain="long",macro_trend_bear="both")
        
        pf=vbt.Portfolio.from_signals(self.st_legacy.close, self.st_legacy.entries,self.st_legacy.exits,
                                      short_entries=self.st_legacy.entries_short,
                                      short_exits  =self.st_legacy.exits_short)             

        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[0]],2),0.94)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[1]],2),1.35)        
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[2]],2),0.60)  
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[6]],2),1.36)  

        self.st_legacy.strat_kama_stoch_matrend_bbands_macro(macro_trend_bull="long",macro_trend_uncertain="both",macro_trend_bear="both")
        
        pf=vbt.Portfolio.from_signals(self.st_legacy.close, self.st_legacy.entries,self.st_legacy.exits,
                                      short_entries=self.st_legacy.entries_short,
                                      short_exits  =self.st_legacy.exits_short)   
        
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[0]],2),1.93)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[1]],2),0.08)        
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[2]],2),0.74)  
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[6]],2),1.73) 

    def test_strat_kama_stoch_matrend_macdbb_macro(self): 
        self.st.strat_kama_stoch_matrend_macdbb_macro(macro_trend_bull="long",macro_trend_uncertain="long",macro_trend_bear="both")
        
        pf=vbt.Portfolio.from_signals(self.st.close, self.st.entries,self.st.exits,
                                      short_entries=self.st.entries_short,
                                      short_exits  =self.st.exits_short)    
          
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[0]],2),1.22)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[1]],2),0.16)        
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[2]],2),2.89)  
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[6]],2),4.07)  

        self.st.strat_kama_stoch_matrend_macdbb_macro(macro_trend_bull="long",macro_trend_uncertain="both",macro_trend_bear="both")
        
        pf=vbt.Portfolio.from_signals(self.st.close, self.st.entries,self.st.exits,
                                      short_entries=self.st.entries_short,
                                      short_exits  =self.st.exits_short)   
        

        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[0]],2),2.05)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[1]],2),-0.50)        
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[2]],2),3.64)  
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[6]],2),2.66) 

    def test_strat_kama_stoch_macro(self): 
        self.st_legacy.strat_kama_stoch_macro(macro_trend_bull="long",macro_trend_uncertain="long",macro_trend_bear="both")
        
        pf=vbt.Portfolio.from_signals(self.st_legacy.close, self.st_legacy.entries,self.st_legacy.exits,
                                      short_entries=self.st_legacy.entries_short,
                                      short_exits  =self.st_legacy.exits_short)  

        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[0]],2),0.02)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[1]],2),1.03)        
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[2]],2),1.14)  
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[6]],2),9.73)  

    def test_strat_pattern_light_macro(self): 
        self.st_legacy.strat_pattern_light_macro(macro_trend_bull="long",macro_trend_uncertain="long",macro_trend_bear="both")
        
        pf=vbt.Portfolio.from_signals(self.st_legacy.close, self.st_legacy.entries,self.st_legacy.exits,
                                      short_entries=self.st_legacy.entries_short,
                                      short_exits  =self.st_legacy.exits_short)  

        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[0]],2),0.96)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[1]],2),2.33)        
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[2]],2),0.55)  
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[6]],2),-0.13)  

    def test_stratF(self):
        self.st.stratF()
        
        pf=vbt.Portfolio.from_signals(self.st.close, self.st.entries,self.st.exits,
                                      short_entries=self.st.entries_short,
                                      short_exits  =self.st.exits_short)   
        
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[0]],2),-0.6) 
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[1]],2),0.19) 
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[2]],2),7.47) 
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[3]],2),-0.22) 
        
    def test_stratIndex(self):
        self.st.stratIndex()        
 
        pf=vbt.Portfolio.from_signals(self.st.close, self.st.entries,self.st.exits,
                                      short_entries=self.st.entries_short,
                                      short_exits  =self.st.exits_short)  
        
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[0]],2),1.7) 
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[1]],2),-0.53) 
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[2]],2),1.41) 
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[3]],2),-0.74) 
        
        self.st=strat.Strat("CAC40","2007_2022_08","test",index=True)
        self.st.stratIndex()      
        pf=vbt.Portfolio.from_signals(self.st.close, self.st.entries,self.st.exits,
                                      short_entries=self.st.entries_short,
                                      short_exits  =self.st.exits_short)         
        
        self.assertEqual(round(pf.get_total_return(),2),5.72) 
        
    def test_stratReal(self):
        self.st.stratReal()
        
        pf=vbt.Portfolio.from_signals(self.st.close, self.st.entries,self.st.exits,
                                      short_entries=self.st.entries_short,
                                      short_exits  =self.st.exits_short)
        
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[0]],2),-0.44) 
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[1]],2),-0.19) 
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[2]],2),3.72) 
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[3]],2),-0.12) 

    def test_stratDiv(self):
        self.st.stratDiv()
        
        pf=vbt.Portfolio.from_signals(self.st.close, self.st.entries,self.st.exits,
                                      short_entries=self.st.entries_short,
                                      short_exits  =self.st.exits_short)  
        
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[0]],2),0.01)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[1]],2),0.07)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[2]],2),1.09)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[3]],2),-0.53) 

    def test_stratSL(self):
        self.st.stratSL()
        
        pf=vbt.Portfolio.from_signals(self.st.close, self.st.entries,self.st.exits,
                                      short_entries=self.st.entries_short,
                                      short_exits  =self.st.exits_short,
                                      sl_stop=0.005)  
        
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[0]],2),280.4)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[1]],2),28.47)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[2]],2),695.37)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[3]],2),236.14) 
        
    def test_stratTSL(self):
        self.st.stratTSL()
        
        pf=vbt.Portfolio.from_signals(self.st.close, self.st.entries,self.st.exits,
                                      short_entries=self.st.entries_short,
                                      short_exits  =self.st.exits_short,
                                      tsl_stop=0.005)  
        
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[0]],2),16127.0)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[1]],2),407.78)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[2]],2),75398.95)
        self.assertEqual(round(pf.get_total_return()[pf.wrapper.columns[3]],2),37324.82) 
        
if __name__ == '__main__':
    unittest.main()        
        
