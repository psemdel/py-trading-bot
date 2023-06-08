#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 31 17:40:09 2023

@author: maxime
"""

import unittest
from opt import opt_strat 

import vectorbtpro as vbt

class TestOptStrat(unittest.TestCase):
    @classmethod
    def setUpClass(self):  
        self.a_bull=[0., 1., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 1., 0.,
        0., 0., 0., 0., 0., 0., 0., 1., 1., 0., 0., 0., 0., 0., 0., 0.,
        0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.]  
        self.a_bear=[0., 1., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 1., 0.,
        0., 0., 0., 0., 0., 0., 0., 1., 1., 0., 0., 0., 0., 0., 0., 0.,
        0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.]  
        self.a_uncertain= [0., 1., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 1., 0.,
        0., 0., 0., 0., 0., 0., 0., 1., 1., 0., 0., 0., 0., 0., 0., 0.,
        0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.]  
        
    def test_check_tested_arrs(self):
        self.o=opt_strat.Opt("2007_2022_08",
                         loops=1)
        
        self.o.calc_arrs=[self.a_bull,self.a_bear,self.a_uncertain]
        self.assertTrue(self.o.check_tested_arrs(just_test=True))
        self.assertTrue(len(self.o.tested_arrs)==0)
        self.assertTrue(self.o.check_tested_arrs())
        self.assertTrue(len(self.o.tested_arrs)==1)
        self.assertFalse(self.o.check_tested_arrs()) #already tested
        self.assertTrue(len(self.o.tested_arrs)==1)
        
        c=[1., 1., 1., 1., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 1., 0.,
        0., 0., 0., 0., 0., 0., 0., 1., 1., 0., 0., 0., 0., 0., 0., 0.,
        0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.]  
        self.o.calc_arrs=[c,self.a_bear,self.a_uncertain]
        self.assertTrue(self.o.check_tested_arrs())
        self.assertTrue(len(self.o.tested_arrs)==2)
        
    def test1(self):
        self.o=opt_strat.Opt("2007_2022_08",
                         loops=1,
                         nb_macro_modes=1)        
        self.o.perf()            

    def test2(self):
        self.o=opt_strat.Opt("2007_2022_08",
                         loops=1,
                         nb_macro_modes=3)        
        self.o.perf()          
        
    def test3(self):              
       a_bull=[1, 1, 1, 0, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1,
              0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0]
       a_bear=[0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 1, 0, 1, 0, 0, 0, 0, 1, 1,
       0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0]
       a_uncertain= [1, 0, 1, 1, 0, 0, 1, 0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1,
       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0]

       self.o=opt_strat.Opt("2007_2023",
              loops=1,
              predefined=True,
              a_bull=a_bull,
              a_bear=a_bear,
              a_uncertain=a_uncertain,   
              macro_trend_bull="long", 
              macro_trend_uncertain="long",
              macro_trend_bear="long",
              )
       self.o.perf()
    