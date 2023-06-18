#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jun  3 23:28:20 2023

@author: maxime
"""


import unittest
from opt import opt_by_part, opt_macro, opt_div, opt_corr, opt_symbols, opt_presel

class TestOptByPart(unittest.TestCase):
    def test_by_part(self):
        self.o=opt_by_part.Opt("2007_2022_08",
                         loops=1)
        self.o.outer_perf()   

class TestOptPressel(unittest.TestCase):
    def test_pressel(self):
        self.o=opt_presel.Opt("2007_2022_08",
                         loops=1)
        self.o.perf()

class TestOptMacro(unittest.TestCase):
    def test_macro(self):
        self.o=opt_macro.Opt("2007_2022_08",
                         loops=1)
        self.o.perf()        

class TestOptDiv(unittest.TestCase):
    def test_div(self):
        self.o=opt_div.Opt("2007_2022_08",
                         loops=1,
                         nb_macro_modes=3)
        self.o.perf()
        
class TestOptCorr(unittest.TestCase):
    def test_corr(self):
        self.o=opt_corr.Opt("2007_2022_08",
                         indexes="CAC40",
                         loops=1,
                         nb_macro_modes=3)
        self.o.outer_perf()           
 
class TestOptSymbols(unittest.TestCase):
    def test_symbols(self):
        self.o=opt_symbols.Opt("2007_2022_08",
                         "CAC40",
                         ['AC', 'ATO', 'RNO'],
                         loops=1,
                         nb_macro_modes=3)
        self.o.outer_perf()  

        