#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jun  3 23:28:20 2023

@author: maxime
"""
from django.test import TestCase
from opt import opt_by_part, opt_macro, opt_corr, opt_symbols, opt_presel

class TestOptByPart(TestCase):
    def test_by_part(self):
        self.o=opt_by_part.Opt("2007_2022_08",
                         loops=1,
                         testing=True)
        self.o.outer_perf()   

class TestOptPressel(TestCase):
    def test_pressel(self):
        self.o=opt_presel.Opt("PreselHistVol","2007_2022_08",
                         loops=1,
                         testing=True)
        self.o.perf()

class TestOptMacro(TestCase):
    def test_macro(self):
        self.o=opt_macro.Opt("2007_2022_08",
                         loops=1,
                         testing=True)
        self.o.perf()        

class TestOptDiv(TestCase):
    def test_div(self):
        self.o=opt_presel.Opt("PreselDivergence","2007_2022_08",
                         loops=1,
                         testing=True)
        self.o.perf()
        
class TestOptCorr(TestCase):
    def test_corr(self):
        self.o=opt_corr.Opt("2007_2022_08",
                         indexes="CAC40",
                         loops=1,
                         nb_macro_modes=3,
                         testing=True)
        self.o.outer_perf()           
 
class TestOptSymbols(TestCase):
    def test_symbols(self):
        self.o=opt_symbols.Opt("2007_2022_08",
                         "CAC40",
                         ['AC', 'ATO', 'RNO'],
                         loops=1,
                         nb_macro_modes=3,
                         testing=True)
        self.o.outer_perf()  

        
