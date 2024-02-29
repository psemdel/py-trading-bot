#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jun 25 12:09:04 2023

@author: maxime
"""
from django.test import TestCase
from core import strat, macro

class TestMacro(TestCase):
    @classmethod
    def setUpClass(self):  
        super().setUpClass()
        self.period="2007_2022_08"
        self.symbol_index="CAC40"
    
    def test_VBTMACROTREND(self):
        self.ust=strat.StratDiv(self.period, symbol_index=self.symbol_index)
        t=macro.VBTMACROTREND.run(self.ust.close)
        
        self.assertEqual(t.macro_trend['AC'].values[0],0)
        self.assertEqual(t.macro_trend['AI'].values[0],0)
        self.assertEqual(t.macro_trend['ORA'].values[0],0) 
        self.assertEqual(t.macro_trend['DSY'].values[0],0)
        
        self.assertEqual(t.macro_trend['AC'].values[1000],-1)
        self.assertEqual(t.macro_trend['AI'].values[1000],-1)
        self.assertEqual(t.macro_trend['ORA'].values[1000],-1) 
        self.assertEqual(t.macro_trend['DSY'].values[1000],-1)
        
        self.assertEqual(t.macro_trend['AC'].values[-1],1)
        self.assertEqual(t.macro_trend['AI'].values[-1],0)
        self.assertEqual(t.macro_trend['ORA'].values[-1],0) 
        self.assertEqual(t.macro_trend['DSY'].values[-1],-1)
                
        self.ust=strat.StratDiv(self.period, symbol_index="DAX")
        t=macro.VBTMACROTREND.run(self.ust.close)
        
        self.assertEqual(t.macro_trend['ADS'].values[0],0)
        self.assertEqual(t.macro_trend['AIR'].values[0],0)
        self.assertEqual(t.macro_trend['ALV'].values[0],0)
        self.assertEqual(t.macro_trend['BAS'].values[0],0)
        self.assertEqual(t.macro_trend['BEI'].values[0],0)

        self.assertEqual(t.macro_trend['ADS'].values[1000],-1)
        self.assertEqual(t.macro_trend['AIR'].values[1000],-1)
        self.assertEqual(t.macro_trend['ALV'].values[1000],0)
        self.assertEqual(t.macro_trend['BAS'].values[1000],-1)
        self.assertEqual(t.macro_trend['BEI'].values[1000],-1)
        
        self.assertEqual(t.macro_trend['ADS'].values[-1],1)
        self.assertEqual(t.macro_trend['AIR'].values[-1],0)
        self.assertEqual(t.macro_trend['ALV'].values[-1],1)
        self.assertEqual(t.macro_trend['BAS'].values[-1],1)
        self.assertEqual(t.macro_trend['BEI'].values[-1],-1)
        
    def test_VBTMACROTRENDPRD(self):
        self.ust=strat.StratDiv(self.period, symbol_index=self.symbol_index)
        t=macro.VBTMACROTRENDPRD.run(self.ust.close)
        
        self.assertEqual(t.macro_trend['AC'].values[-1],1)
        self.assertEqual(t.macro_trend['AI'].values[-1],0)
        self.assertEqual(t.macro_trend['ORA'].values[-1],0)  
        
    def test_VBTMACROFILTER(self):
        self.ust=strat.StratDiv(self.period, symbol_index=self.symbol_index)  
        self.ust.run()
        
        t=macro.VBTMACROTREND.run(self.ust.close)

        self.assertEqual(self.ust.entries[self.ust.entries.columns[0]].values[0],False)
        self.assertEqual(t.macro_trend['AC'].values[0],0)
        
        t2=macro.VBTMACROFILTER.run(self.ust.entries,t.macro_trend, mode=0 )
        
        self.assertEqual(t.macro_trend['AC'].values[0],t2.out[t2.out.columns[0]].values[0])
        self.assertEqual(self.ust.entries[self.ust.entries.columns[0]].values[-12],True)
        self.assertEqual(t.macro_trend['AC'].values[-12],1)
        self.assertFalse(t2.out[t2.out.columns[0]].values[-12])
        
        self.assertEqual(self.ust.entries[self.ust.entries.columns[11]].values[-6],True)
        self.assertEqual(t.macro_trend['DSY'].values[-6],-1)
        self.assertFalse(t2.out[t2.out.columns[11]].values[-6])
        
        self.assertEqual(self.ust.entries[self.ust.entries.columns[5]].values[-11],True) 
        self.assertEqual(t.macro_trend['BN'].values[-11],0)
        self.assertTrue(t2.out[t2.out.columns[5]].values[-11])
        
        self.assertEqual(self.ust.entries[self.ust.entries.columns[8]].values[-5],True)
        self.assertEqual(t.macro_trend['CAP'].values[-5],0)
        self.assertTrue(t2.out[t2.out.columns[8]].values[-5])        
        
        
        
              
        
