#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Aug 27 09:27:58 2023

@author: maxime
"""

from django.test import TestCase
from opt import opt_presel, opt_keep
from core import presel
import vectorbtpro as vbt
import numpy as np

class TestOptPresel(TestCase):
    def test_div(self):
        a={'simple': 
         {'ent': [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
          'ex':  [0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0]}}
        
        self.o=opt_presel.Opt("PreselDivergence",
                              "2007_2022_08",
                         strat_arr=a,
                         testing=True,
                         fees=0,
                         test_window_start_init=0,
                         filename="test"
                         )
        self.o.test_arrs=None
        
        self.period="2007_2022_08"
        self.symbol_index="CAC40"
        self.bti=presel.PreselDivergence(self.period,symbol_index=self.symbol_index)
        self.bti.run()

        pf_dic=self.o.calculate_pf_sub(dic="total")

        pf=vbt.Portfolio.from_signals(self.bti.close,
                                      self.bti.entries,
                                      self.bti.exits,
                                      short_entries=self.bti.entries_short,
                                      short_exits  =self.bti.exits_short,
                                      freq="1d",
                                      call_seq='auto',
                                      cash_sharing=True,
                             )

        self.assertTrue(np.equal(self.bti.entries, self.o.ents["CAC40"]).all().all())
        self.assertTrue(np.equal(self.bti.exits, self.o.exs["CAC40"]).all().all())
        self.assertTrue(np.equal(self.bti.entries_short, self.o.ents_short["CAC40"]).all().all())
        self.assertTrue(np.equal(self.bti.exits_short, self.o.exs_short["CAC40"]).all().all())

        self.assertTrue(np.equal(pf.get_total_return(), pf_dic["CAC40"].get_total_return()).all())
        pf_dic=self.o.calculate_pf_sub(dic="learn")
        i=self.o.ents["CAC40"].index
        
        self.assertTrue(np.equal(self.bti.entries.loc[i], self.o.ents["CAC40"]).all().all())
        self.assertTrue(np.equal(self.bti.exits.loc[i], self.o.exs["CAC40"]).all().all())
        self.assertTrue(np.equal(self.bti.entries_short.loc[i], self.o.ents_short["CAC40"]).all().all())
        self.assertTrue(np.equal(self.bti.exits_short.loc[i], self.o.exs_short["CAC40"]).all().all())
       
        pf=vbt.Portfolio.from_signals(self.bti.close.loc[i],
                                      self.bti.entries.loc[i],
                                      self.bti.exits.loc[i],
                                      short_entries=self.bti.entries_short.loc[i],
                                      short_exits  =self.bti.exits_short.loc[i],
                                      freq="1d",
                                      call_seq='auto',
                                      cash_sharing=True,
                             )

        self.assertTrue(np.equal(pf.get_total_return(), pf_dic["CAC40"].get_total_return()).all())                                          
        
        pf_dic=self.o.calculate_pf_sub(dic="test")
        i=self.o.ents["CAC40"].index

        pf=vbt.Portfolio.from_signals(self.bti.close.loc[i],
                                      self.bti.entries.loc[i],
                                      self.bti.exits.loc[i],
                                      short_entries=self.bti.entries_short.loc[i],
                                      short_exits  =self.bti.exits_short.loc[i],
                                      freq="1d",
                                      call_seq='auto',
                                      cash_sharing=True,
                             )  
        self.assertTrue(np.equal(pf.get_total_return(), pf_dic["CAC40"].get_total_return()).all())  

    def test_keep(self):
        a={'bull': 
           {'ent': [0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
            'ex': [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 1, 0, 0, 1, 0, 0]},
           'bear': 
           {'ent': [0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
            'ex': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 0, 0]},
           'uncertain': 
           {'ent': [0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
            'ex': [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 1, 0, 0, 0, 0, 0]}
           }
            
        self.o=opt_keep.Opt(
                         "2007_2022_08",
                         strat_arr=a,
                         testing=True,
                         fees=0,
                         test_window_start_init=0,
                         filename="test"
                         )
        self.o.test_arrs=None
        
        self.period="2007_2022_08"
        self.symbol_index="CAC40"
        self.bti=presel.PreselRetardKeepBT(self.period,symbol_index=self.symbol_index)
        self.bti.run()   

        pf_dic=self.o.calculate_pf_sub(dic="total")
        
        pf=vbt.Portfolio.from_signals(self.bti.close,
                                      self.bti.entries,
                                      self.bti.exits,
                                      short_entries=self.bti.entries_short,
                                      short_exits  =self.bti.exits_short,
                                      freq="1d",
                                      call_seq='auto',
                                      cash_sharing=True,
                             )

        self.assertTrue(np.equal(self.bti.entries, self.o.ents["CAC40"]).all().all())
        self.assertTrue(np.equal(self.bti.exits, self.o.exs["CAC40"]).all().all())

        self.bti2=presel.PreselRetardMacro(self.period,symbol_index=self.symbol_index)
        self.bti2.run()
        
        self.assertTrue(np.equal(self.bti.entries, self.bti2.exits).all().all())

        self.assertTrue(np.equal(pf.get_total_return(), pf_dic["CAC40"].get_total_return()).all())
        
        self.period="2007_2022_08"
        self.symbol_index="DAX"
        self.bti3=presel.PreselRetardKeepBT(self.period,symbol_index=self.symbol_index)
        self.bti3.run()  
        
        #calculate_pf_sub should also have calculated DAX correctly the first time
        self.assertTrue(np.equal(self.bti3.entries, self.o.ents["DAX"]).all().all())
        self.assertTrue(np.equal(self.bti3.exits, self.o.exs["DAX"]).all().all())

        pf3=vbt.Portfolio.from_signals(self.bti3.close,
                                      self.bti3.entries,
                                      self.bti3.exits,
                                      short_entries=self.bti3.entries_short,
                                      short_exits  =self.bti3.exits_short,
                                      freq="1d",
                                      call_seq='auto',
                                      cash_sharing=True,
                             )

        self.assertTrue(np.equal(pf3.get_total_return(), pf_dic["DAX"].get_total_return()).all())        
        
        pf_dic=self.o.calculate_pf_sub(dic="learn")
        i=self.o.ents["CAC40"].index   
        
        pf=vbt.Portfolio.from_signals(self.bti.close.loc[i],
                                      self.bti.entries.loc[i],
                                      self.bti.exits.loc[i],
                                      short_entries=self.bti.entries_short.loc[i],
                                      short_exits  =self.bti.exits_short.loc[i],
                                      freq="1d",
                                      call_seq='auto',
                                      cash_sharing=True,
                             )
        
        self.assertTrue(np.equal(self.bti.entries.loc[i], self.o.ents["CAC40"]).all().all())
        self.assertTrue(np.equal(self.bti.exits.loc[i], self.o.exs["CAC40"]).all().all())
        self.assertTrue(np.equal(pf.get_total_return(), pf_dic["CAC40"].get_total_return()).all())                                          
        
        pf_dic=self.o.calculate_pf_sub(dic="test")
        i=self.o.ents["CAC40"].index

        pf=vbt.Portfolio.from_signals(self.bti.close.loc[i],
                                      self.bti.entries.loc[i],
                                      self.bti.exits.loc[i],
                                      short_entries=self.bti.entries_short.loc[i],
                                      short_exits  =self.bti.exits_short.loc[i],
                                      freq="1d",
                                      call_seq='auto',
                                      cash_sharing=True,
                             )  
        self.assertTrue(np.equal(pf.get_total_return(), pf_dic["CAC40"].get_total_return()).all())  