#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 31 17:40:09 2023

@author: maxime
"""

from django.test import TestCase
from opt import opt_strat 
from core import strat
import vectorbtpro as vbt
import numpy as np

class TestOptStrat(TestCase):
    @classmethod
    def setUpClass(self):  
        super().setUpClass()
        
    def test1(self):
        self.o=opt_strat.Opt("2007_2022_08",
                         loops=1,
                         nb_macro_modes=1,
                         testing=True,
                         filename="test")        
        self.o.perf()            

    def test2(self):
        self.o=opt_strat.Opt("2007_2022_08",
                         loops=1,
                         nb_macro_modes=3,
                         testing=True,
                         filename="test")        
        self.o.perf()          
        
    def test3(self):              
        a={"bull":
           {"ent":[0., 1., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 1., 0., 0., 0., 0., 0., 0., 0.,],
            "ex": [0., 1., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.]
           },
          "bear":
             {"ent":[0., 1., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 1., 0., 0., 0., 0., 0., 0., 0.],
              "ex": [0., 1., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.]
             },
          "uncertain":
             {"ent":[0., 1., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 1., 0., 0., 0., 0., 0., 0.,0.],
              "ex": [0., 1., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.]
             },             
          } 

        self.o=opt_strat.Opt("2007_2022_08",
              strat_arr=a,
              dir_bull="long", 
              dir_uncertain="long",
              dir_bear="long",
              testing=True
              )
        self.o.perf()
        
    def test_same_pf(self):
        self.period="2007_2022_08"
        self.symbol_index="CAC40"
        self.ust=strat.StratG(self.period, symbol_index=self.symbol_index)
        self.ust.run()
        
        pf1=vbt.Portfolio.from_signals(self.ust.close, self.ust.entries,self.ust.exits,
                                      short_entries=self.ust.entries_short,
                                      short_exits  =self.ust.exits_short)   

        a={"bull":
           {"ent":[0., 0., 1., 0., 0., 1., 1., 0., 0., 1., 0., 1., 0., 1., 0., 1., 1., 1., 0., 0., 0., 1.],
            "ex": [0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 1., 0., 0., 1., 0., 0., 0., 0., 0., 0.]
           },
          "bear":
             {"ent":[0., 1., 0., 0., 0., 1., 1., 0., 0., 1., 0., 1., 1., 1., 0., 1., 1., 0., 1., 0., 1., 0.],
              "ex": [0., 0., 0., 1., 1., 0., 0., 0., 0., 0., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.]
             },
          "uncertain":
             {"ent":[0., 1., 1., 0., 0., 1., 1., 0., 0., 1., 1., 1., 1., 1., 0., 0., 1., 0., 1., 0., 1., 1.],
              "ex": [0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 1., 0., 1., 1., 0., 0., 0., 0., 1., 0., 0.]
             },             
          }   

        self.o=opt_strat.Opt("2007_2022_08",
              strat_arr=a,
              dir_bull="long", 
              dir_uncertain="both",
              dir_bear="both",
              testing=True,
              fees=0, ###Important!!!
              test_window_start_init=0,
              filename="test"
              )        
        
        self.o.test_arrs=None
        self.o.defi_i("total")
        pf_dic=self.o.calculate_pf_sub(dic="total")

        self.assertTrue(np.equal(self.o.ents["CAC40"],self.ust.entries).all().all())
        self.assertTrue(np.equal(self.o.exs["CAC40"],self.ust.exits).all().all())  
        self.assertTrue(np.equal(self.o.ents_short["CAC40"],self.ust.entries_short).all().all())
        self.assertTrue(np.equal(self.o.exs_short["CAC40"],self.ust.exits_short).all().all())   
        
        self.assertTrue(np.equal(pf1.get_total_return(), pf_dic["CAC40"].get_total_return()).all())
        
        self.o.test_arrs=None
        self.o.calculate_pf_sub(dic="total")
        i=self.o.ents["CAC40"].index

        self.assertTrue(np.equal(self.o.ents["CAC40"].loc[i],self.ust.entries.loc[i]).all().all())
        self.assertTrue(np.equal(self.o.exs["CAC40"].loc[i],self.ust.exits.loc[i]).all().all())  
        self.assertTrue(np.equal(self.o.ents_short["CAC40"].loc[i],self.ust.entries_short.loc[i]).all().all())
        self.assertTrue(np.equal(self.o.exs_short["CAC40"].loc[i],self.ust.exits_short.loc[i]).all().all())  
        
        self.o.calculate_pf_sub(dic="test")
        i=self.o.ents["CAC40"].index

        self.assertTrue(np.equal(self.o.ents["CAC40"].loc[i],self.ust.entries.loc[i]).all().all())
        self.assertTrue(np.equal(self.o.exs["CAC40"].loc[i],self.ust.exits.loc[i]).all().all())  
        self.assertTrue(np.equal(self.o.ents_short["CAC40"].loc[i],self.ust.entries_short.loc[i]).all().all())
        self.assertTrue(np.equal(self.o.exs_short["CAC40"].loc[i],self.ust.exits_short.loc[i]).all().all())   
        
        self.o.calculate_pf_sub(dic="learn")
        i=self.o.ents["CAC40"].index #last has a closing order
        self.assertTrue(np.equal(self.o.ents["CAC40"].loc[i],self.ust.entries.loc[i]).all().all())
        self.assertTrue(np.equal(self.o.exs["CAC40"].loc[i],self.ust.exits.loc[i]).all().all())  
        self.assertTrue(np.equal(self.o.ents_short["CAC40"].loc[i],self.ust.entries_short.loc[i]).all().all())
        self.assertTrue(np.equal(self.o.exs_short["CAC40"].loc[i],self.ust.exits_short.loc[i]).all().all())  
        