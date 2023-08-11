#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jun  3 23:03:23 2023

@author: maxime
"""

from django.test import TestCase
from opt import opt_main
from opt import opt_strat 
import numpy as np
from core import strat

import vectorbtpro as vbt

class TestOptMain(TestCase):
    @classmethod
    def setUpClass(self):  
        self.a_bull=[
        1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
        1., 1., 1., 1., 1., 1., 
        0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 
        0., 0., 0., 0., 0., 0.]  
        self.a_bear=[ 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
         0., 0., 0., 0., 0., 0., 
         1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
         1., 1., 1., 1., 1., 1.]
        self.a_uncertain= [
        1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
        1., 1., 1., 1., 1., 1., 
        0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 
        0., 0., 0., 0., 0., 0.]  

        self.o=opt_main.OptMain("2007_2022_08",
                         loops=1)
        
    def test_init(self):
        self.assertEqual(np.shape(self.o.close_dic["CAC40"]["total"])[0],4005)
        self.assertEqual(np.shape(self.o.close_dic["CAC40"]["total"])[1],39)
        self.assertEqual(np.shape(self.o.close_dic["CAC40"]["learn"])[0],3204)
        self.assertEqual(np.shape(self.o.close_dic["CAC40"]["learn"])[1],39)
        self.assertEqual(np.shape(self.o.close_dic["CAC40"]["test"])[0],801)
        self.assertEqual(np.shape(self.o.close_dic["CAC40"]["test"])[1],39)

        self.o=opt_main.OptMain("2007_2022_08",
                         loops=1,
                         test_window_start_init=0)
        
        self.assertEqual(np.shape(self.o.close_dic["CAC40"]["total"])[0],4005)
        self.assertEqual(np.shape(self.o.close_dic["CAC40"]["total"])[1],39)
        self.assertEqual(np.shape(self.o.close_dic["CAC40"]["learn"])[0],3204)
        self.assertEqual(np.shape(self.o.close_dic["CAC40"]["learn"])[1],39)
        self.assertEqual(np.shape(self.o.close_dic["CAC40"]["test"])[0],801)
        self.assertEqual(np.shape(self.o.close_dic["CAC40"]["test"])[1],39)
        self.assertEqual(str(self.o.close_dic["CAC40"]["learn"].index[0]),"2010-02-22 00:00:00+00:00")
        self.assertEqual(str(self.o.close_dic["CAC40"]["learn"].index[-1]),"2022-08-31 00:00:00+00:00")
        self.assertEqual(str(self.o.close_dic["CAC40"]["test"].index[0]),"2007-01-02 00:00:00+00:00")
        self.assertEqual(str(self.o.close_dic["CAC40"]["test"].index[-1]),"2010-02-19 00:00:00+00:00")
        
        self.o=opt_main.OptMain("2007_2022_08",
                         loops=1,
                         test_window_start_init=0,
                         split_learn_train="symbol")
        
        self.assertEqual(np.shape(self.o.close_dic["CAC40"]["total"])[0],4005)
        self.assertEqual(np.shape(self.o.close_dic["CAC40"]["total"])[1],39)
        self.assertEqual(np.shape(self.o.close_dic["CAC40"]["learn"])[0],4005)
        self.assertEqual(np.shape(self.o.close_dic["CAC40"]["learn"])[1],31)
        self.assertEqual(np.shape(self.o.close_dic["CAC40"]["test"])[0],4005)
        self.assertEqual(np.shape(self.o.close_dic["CAC40"]["test"])[1],8)
    
    def test_filter_symbols(self):
        self.o.filter_symbols(symbols_to_keep=["AC"])
        self.assertEqual(self.o.symbols["CAC40"],['AC'])

        self.o.filter_symbols(symbols_to_keep=["AC","BNP"])
        self.assertEqual(self.o.symbols["CAC40"],['AC',"BNP"])
        
        self.o.filter_symbols(symbols_to_keep=["AC","BNP","APPL"])
        self.assertEqual(self.o.symbols["CAC40"],['AC',"BNP"])
        
    def test_predef(self):
        self.assertTrue(np.equal(self.o.predef(),[None, None, None]).all())
        
        self.o=opt_strat.OptMain("2007_2022_08",
                         loops=1, 
                         nb_macro_modes=1)

        self.assertTrue(np.equal(self.o.predef(),[None]).all())
        
        self.o=opt_main.OptMain("2007_2022_08",
                         loops=1, 
                         nb_macro_modes=3,
                         predefined=True,
                         a_bull=self.a_bull,
                         a_bear=self.a_bear,
                         a_uncertain=self.a_uncertain,   
                         )

        self.assertTrue(np.equal(self.o.predef(),[self.a_bull,self.a_bear, self.a_uncertain]).all())
        
    def test_defi_i(self):
        self.o=opt_main.OptMain("2007_2022_08",
                         loops=1, 
                         nb_macro_modes=3,
                         predefined=True,
                         a_bull=self.a_bull,
                         a_bear=self.a_bear,
                         a_uncertain=self.a_uncertain, 
                         test_window_start_init=0,
                         )
        
        self.o.defi_i("total")
        
        self.assertEqual(np.shape(self.o.all_t_ents["CAC40"]["total"])[0],22)
        self.assertEqual(np.shape(self.o.all_t_ents["CAC40"]["total"])[1],4005)
        self.assertEqual(np.shape(self.o.all_t_ents["CAC40"]["total"])[2],39)
        
    def test_defi(self):
        self.o=opt_main.OptMain("2007_2022_08",
                         loops=1, 
                         nb_macro_modes=3,
                         predefined=True,
                         a_bull=self.a_bull,
                         a_bear=self.a_bear,
                         a_uncertain=self.a_uncertain,   
                         test_window_start_init=0
                         )
        self.o.defi_i("total")
        self.o.defi_ex("total")
        
        self.assertEqual(np.shape(self.o.exs["CAC40"])[0],4005)
        self.assertEqual(np.shape(self.o.exs["CAC40"])[1],39)
        self.assertFalse(self.o.exs["CAC40"][self.o.exs["CAC40"].columns[0]].values[0])
        self.assertTrue(self.o.exs["CAC40"][self.o.exs["CAC40"].columns[0]].values[-1])
        self.assertTrue(self.o.exs["CAC40"][self.o.exs["CAC40"].columns[0]].values[-4])

        self.o.defi_ent("total")
        self.assertEqual(np.shape(self.o.ents["CAC40"])[0],4005)
        self.assertEqual(np.shape(self.o.ents["CAC40"])[1],39)
        self.assertFalse(self.o.ents["CAC40"][self.o.ents["CAC40"].columns[0]].values[0])
        self.assertTrue(self.o.ents["CAC40"][self.o.ents["CAC40"].columns[1]].values[-1])
        self.assertTrue(self.o.ents["CAC40"][self.o.ents["CAC40"].columns[1]].values[-4])
        
    def test_random(self):
        self.assertEqual(np.shape(self.o.random())[0],44)
     
    def test_get_ret_sub(self):
        #the idea is to have p1>p2 is rr1>rr2
        self.assertEqual(round(self.o.get_ret_sub(1,1),2),0)
        self.assertEqual(round(self.o.get_ret_sub(1,1.1),2),0.1)
        self.assertEqual(round(self.o.get_ret_sub(0.5,1),2),1)
        
        self.assertEqual(round(self.o.get_ret_sub(0,1),2),10)
        self.assertEqual(round(self.o.get_ret_sub(0.01,1),2),10)
        self.assertEqual(round(self.o.get_ret_sub(0.001,1),2),10)
        
        #also if rb is negative
        self.assertEqual(round(self.o.get_ret_sub(-0.2,0),2),1)
        self.assertEqual(round(self.o.get_ret_sub(-0.2,0.2),2),2)
        self.assertEqual(round(self.o.get_ret_sub(-0.2,0.4),2),3)
        
        self.assertEqual(round(self.o.get_ret_sub(-0.01,0.4),2),4)
        self.assertEqual(round(self.o.get_ret_sub(-0.001,1),2),10)
        
        #both negative
        self.assertEqual(round(self.o.get_ret_sub(-0.2,-0.2),2),0)
        self.assertEqual(round(self.o.get_ret_sub(-0.2,-0.4),2),-1)
        self.assertEqual(round(self.o.get_ret_sub(0.01,-0.4),2),-4)
        
    def test_get_ret(self):
        self.ust=strat.StratF("2007_2022_08", symbol_index="CAC40")
        self.ust.run()
        
        pf=vbt.Portfolio.from_signals(self.ust.close, self.ust.entries,self.ust.exits,
                                      short_entries=self.ust.entries_short,
                                      short_exits  =self.ust.exits_short)
        t=self.o.get_ret(pf)
        self.assertEqual(len(t),39)
        self.assertEqual(round(t['VIV'],2),-0.97)