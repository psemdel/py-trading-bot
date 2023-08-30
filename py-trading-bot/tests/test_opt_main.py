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
import copy

import vectorbtpro as vbt

class TestOptMain(TestCase):
    @classmethod
    def setUpClass(self):  
        super().setUpClass()
        self.a={"bull":
           {"ent":[1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.],
            "ex": [0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.]
           },
          "bear":
             {"ent":[0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.],
              "ex": [1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.]
             },
          "uncertain":
             {"ent":[1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,],
              "ex": [0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.]
             },             
          }     

        self.o=opt_main.OptMain("2007_2022_08",
                         loops=1, testing=True, filename="test")
        
    def test_init(self):
        self.assertEqual(np.shape(self.o.close_dic["CAC40"]["total"])[0],4004)
        self.assertEqual(np.shape(self.o.close_dic["CAC40"]["total"])[1],39)
        self.assertEqual(np.shape(self.o.close_dic["CAC40"]["learn"])[0],3203)
        self.assertEqual(np.shape(self.o.close_dic["CAC40"]["learn"])[1],39)
        self.assertEqual(np.shape(self.o.close_dic["CAC40"]["test"])[0],801)
        self.assertEqual(np.shape(self.o.close_dic["CAC40"]["test"])[1],39)

        self.o=opt_main.OptMain("2007_2022_08",
                         loops=1,
                         test_window_start_init=0,
                         testing=True,
                         filename="test")
        
        self.assertEqual(np.shape(self.o.close_dic["CAC40"]["total"])[0],4004)
        self.assertEqual(np.shape(self.o.close_dic["CAC40"]["total"])[1],39)
        self.assertEqual(np.shape(self.o.close_dic["CAC40"]["learn"])[0],3203)
        self.assertEqual(np.shape(self.o.close_dic["CAC40"]["learn"])[1],39)
        self.assertEqual(np.shape(self.o.close_dic["CAC40"]["test"])[0],801)
        self.assertEqual(np.shape(self.o.close_dic["CAC40"]["test"])[1],39)
        self.assertEqual(str(self.o.close_dic["CAC40"]["learn"].index[0]),"2010-02-22 00:00:00+01:00")
        self.assertEqual(str(self.o.close_dic["CAC40"]["learn"].index[-1]),"2022-08-30 00:00:00+02:00")
        self.assertEqual(str(self.o.close_dic["CAC40"]["test"].index[0]),"2007-01-02 00:00:00+01:00")
        self.assertEqual(str(self.o.close_dic["CAC40"]["test"].index[-1]),"2010-02-19 00:00:00+01:00")
        
        self.o=opt_main.OptMain("2007_2022_08",
                         loops=1,
                         test_window_start_init=0,
                         split_learn_train="symbol",
                         testing=True,
                         filename="test")
        
        self.assertEqual(np.shape(self.o.close_dic["CAC40"]["total"])[0],4004)
        self.assertEqual(np.shape(self.o.close_dic["CAC40"]["total"])[1],39)
        self.assertEqual(np.shape(self.o.close_dic["CAC40"]["learn"])[0],4004)
        self.assertEqual(np.shape(self.o.close_dic["CAC40"]["learn"])[1],31)
        self.assertEqual(np.shape(self.o.close_dic["CAC40"]["test"])[0],4004)
        self.assertEqual(np.shape(self.o.close_dic["CAC40"]["test"])[1],8)
    
    def test_filter_symbols(self):
        self.o.filter_symbols(symbols_to_keep=["AC"])
        self.assertEqual(self.o.symbols["CAC40"],['AC'])

        self.o.filter_symbols(symbols_to_keep=["AC","BNP"])
        self.assertEqual(self.o.symbols["CAC40"],['AC',"BNP"])
        
        self.o.filter_symbols(symbols_to_keep=["AC","BNP","APPL"])
        self.assertEqual(self.o.symbols["CAC40"],['AC',"BNP"])
     
    def test_defi_i(self):
        self.o=opt_main.OptMain("2007_2022_08",
                         loops=1, 
                         nb_macro_modes=3,
                         strat_arr=self.a,
                         test_window_start_init=0,
                         testing=True,
                         filename="test"
                         )
        
        self.o.defi_i("total")
        
        self.assertEqual(np.shape(self.o.all_t["CAC40"]["total"]["ent"])[0],22)
        self.assertEqual(np.shape(self.o.all_t["CAC40"]["total"]["ent"])[1],4004)
        self.assertEqual(np.shape(self.o.all_t["CAC40"]["total"]["ent"])[2],39)
        
    def test_defi(self):
        self.o=opt_main.OptMain("2007_2022_08",
                         loops=1, 
                         nb_macro_modes=3,
                         strat_arr=self.a,
                         #test_window_start_init=0
                         )
        self.o.defi_i("total")
        self.o.defi_ex("total")
        
        self.assertEqual(np.shape(self.o.exs["CAC40"])[0],4004)
        self.assertEqual(np.shape(self.o.exs["CAC40"])[1],39)
        self.assertFalse(self.o.exs["CAC40"][self.o.exs["CAC40"].columns[0]].values[0])
        self.assertFalse(self.o.exs["CAC40"][self.o.exs["CAC40"].columns[0]].values[-1])
        self.assertTrue(self.o.exs["CAC40"][self.o.exs["CAC40"].columns[0]].values[-3])
        self.assertFalse(self.o.exs["CAC40"][self.o.exs["CAC40"].columns[0]].values[-4])

        self.o.defi_ent("total")
        self.assertEqual(np.shape(self.o.ents["CAC40"])[0],4004)
        self.assertEqual(np.shape(self.o.ents["CAC40"])[1],39)
        
        self.assertFalse(self.o.ents["CAC40"][self.o.ents["CAC40"].columns[0]].values[0])
        self.assertTrue(self.o.ents["CAC40"][self.o.ents["CAC40"].columns[1]].values[-1])
        self.assertTrue(self.o.ents["CAC40"][self.o.ents["CAC40"].columns[1]].values[-4])
        
        exs_total=copy.deepcopy(self.o.exs)
        ents_total=copy.deepcopy(self.o.ents)
        
        self.o.defi_i("test")
        self.o.defi_ex("test")
        
        i=self.o.exs["CAC40"].index
        self.assertTrue(np.equal(exs_total["CAC40"].loc[i],self.o.exs["CAC40"].loc[i]).all().all())
        self.o.defi_ent("test")
        self.assertTrue(np.equal(ents_total["CAC40"].loc[i],self.o.ents["CAC40"].loc[i]).all().all())

        self.o.defi_i("learn")
        self.o.defi_ex("learn")
        i=self.o.exs["CAC40"].index[:-1]
        self.assertTrue(np.equal(exs_total["CAC40"].loc[i],self.o.exs["CAC40"].loc[i]).all().all())
        self.o.defi_ent("test")
        i2=self.o.ents["CAC40"].index[:-1]
        self.assertTrue(np.equal(ents_total["CAC40"].loc[i2],self.o.ents["CAC40"].loc[i2]).all().all())
        
    def test_random(self):
        self.assertEqual(np.shape(self.o.random(10))[0],10)
        self.assertEqual(np.shape(self.o.random(20))[0],20)
        
    def test_assign_random(self):
        self.o.assign_random()
        self.assertTrue("bull" in self.o.calc_arr)
        self.assertTrue("bear" in self.o.calc_arr)
        self.assertTrue("uncertain" in self.o.calc_arr)
        self.assertFalse("simple" in self.o.calc_arr)
        self.assertTrue("bull" in self.o.arr)
        self.assertTrue("bear" in self.o.arr)
        self.assertTrue("uncertain" in self.o.arr)
        
        self.assertTrue("ent" in self.o.calc_arr["bull"])
        self.assertTrue("ex" in self.o.calc_arr["bull"])
        self.assertTrue(np.equal(self.o.calc_arr["bull"]["ent"],self.o.calc_arr["bear"]["ent"]).all())
        self.assertTrue(np.equal(self.o.calc_arr["bull"]["ent"],self.o.calc_arr["uncertain"]["ent"]).all())
        self.assertTrue(np.equal(self.o.calc_arr["bull"]["ex"],self.o.calc_arr["bear"]["ex"]).all())
        self.assertTrue(np.equal(self.o.calc_arr["bull"]["ex"],self.o.calc_arr["uncertain"]["ex"]).all())
        
        self.o.nb_macro_modes=1
        self.o.assign_random()
        self.assertFalse("bull" in self.o.calc_arr)
        self.assertFalse("bear" in self.o.calc_arr)
        self.assertFalse("uncertain" in self.o.calc_arr)
        self.assertTrue("simple" in self.o.calc_arr)
        self.assertTrue("ent" in self.o.calc_arr["simple"])
        self.assertTrue("ex" in self.o.calc_arr["simple"])
        
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
        t=self.o.get_ret(pf,"CAC40","learn")
        self.assertEqual(len(t),39)
        self.assertEqual(round(t['VIV'],2),-0.97)
        
    def test_append_row(self):
        self.o.test_arrs=None
        self.o.row={'col1':1,'col2':2,'col3':'a'}
        self.o.ind_k="010"
        self.o.append_row()

        self.assertTrue("010" in self.o.test_arrs.index)
        self.assertEqual(self.o.test_arrs.loc["010",'col1'],1)
        self.assertEqual(self.o.test_arrs.loc["010",'col2'],2)
        self.assertEqual(self.o.test_arrs.loc["010",'col3'],'a')
        self.assertEqual(len(self.o.test_arrs.index),1)
        self.o.append_row()
        self.assertEqual(len(self.o.test_arrs.index),1)
        
        self.o.row={'col1':1,'col2':2,'col3':'a','col4':4}
        self.o.append_row()
        self.assertEqual(len(self.o.test_arrs.index),1)
        self.assertEqual(self.o.test_arrs.loc["010",'col1'],1)
        self.assertEqual(self.o.test_arrs.loc["010",'col2'],2)
        self.assertEqual(self.o.test_arrs.loc["010",'col3'],'a')
        self.assertEqual(self.o.test_arrs.loc["010",'col4'],4)
        
        self.o.ind_k="011"
        self.o.append_row()
        self.assertEqual(len(self.o.test_arrs.index),2)
        self.assertTrue("011" in self.o.test_arrs.index)
        self.assertEqual(self.o.test_arrs.loc["011",'col1'],1)
        self.assertEqual(self.o.test_arrs.loc["011",'col2'],2)
        self.assertEqual(self.o.test_arrs.loc["011",'col3'],'a')
        self.assertEqual(self.o.test_arrs.loc["011",'col4'],4)
    
    def test_check_tested_arrs(self):
        self.o=opt_strat.Opt("2007_2022_08",
                         loops=1,
                         testing=True,
                         , filename="test")
        self.o.test_arrs=None
        self.o.calc_arr=self.a
        self.assertTrue(self.o.check_tested_arrs())
        self.o.append_row()
        self.assertFalse(self.o.check_tested_arrs())
        
        self.o.calc_arr["bull"]["ent"]=[1., 1., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 1., 0., 0., 0., 0., 0., 0., 0.,]
        self.assertTrue(self.o.check_tested_arrs())
      