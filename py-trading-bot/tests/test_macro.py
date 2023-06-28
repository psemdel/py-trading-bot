#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jun 25 12:09:04 2023

@author: maxime
"""

import unittest
from core import strat, macro
import vectorbtpro as vbt

class TestMacro(unittest.TestCase):
    @classmethod
    def setUpClass(self):  
        self.period="2007_2022_08"
        self.symbol_index="CAC40"
    
    def test_ext_major(self):
        self.ust=strat.StratDiv(self.period, symbol_index=self.symbol_index)
        t=macro.VBTMACROTREND.run(self.ust.close)
        
        self.assertEqual(t.macro_trend['AC'].values[-1],1)
        self.assertEqual(t.macro_trend['AI'].values[-1],0)
        self.assertEqual(t.macro_trend['ORA'].values[-1],0)  