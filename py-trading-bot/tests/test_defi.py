#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Aug 10 22:40:52 2023

@author: maxime
"""
from django.test import TestCase
from opt import opt_main
from opt import opt_strat 
import numpy as np
from core import strat
import numbers

import vectorbtpro as vbt
from core.strat import UnderlyingStrat

a={'bull': {'ent': ['RSI20','RSI30','CDLMARUBOZU',"CDL3WHITESOLDIERS","CDLENGULFING","CDLTAKURI",
                    "CDLMORNINGDOJISTAR","CDLMORNINGSTAR","CDLKICKING_INV"],
            'ex': ["CDLRISEFALL3METHODS","CDLABANDONEDBABY"]},
   'bear': {'ent': ['STOCH','RSI20','RSI30',"CDLMARUBOZU","CDL3WHITESOLDIERS","CDLLONGLINE","CDLENGULFING","CDLTAKURI",
                    "CDLMORNINGDOJISTAR","CDLHANGINGMAN","CDLKICKINGBYLENGTH_INV"],
            'ex': ['SUPERTREND','BBANDS',"CDLBELTHOLD"]},
   'uncertain': {'ent': ['STOCH','RSI20','RSI30',"CDLMARUBOZU","CDLCLOSINGMARUBOZU","CDL3WHITESOLDIERS",
                         "CDLLONGLINE","CDLENGULFING","CDLMORNINGDOJISTAR","CDLHANGINGMAN","CDLKICKINGBYLENGTH_INV",
                         "CDLKICKING_INV"],
                 'ex': ["CDLHIKKAKE","CDL3LINESTRIKE","CDLBREAKAWAY"]}}    

a_simple={"simple":
          {"ent":['STOCH','SUPERTREND','RSI20','RSI30',"CDLMARUBOZU","CDL3WHITESOLDIERS","CDLTAKURI","CDLMORNINGDOJISTAR",
                             "CDLKICKINGBYLENGTH_INV","CDLKICKING_INV"],
           "ex": ["CDLRISEFALL3METHODS"]}
           
  } 

class StratT1(UnderlyingStrat):    
    def __init__(self,
                 period: numbers.Number,
                 **kwargs):

        super().__init__(
            period,
            strat_arr=a_simple,
            **kwargs ) 
        
class StratT2(UnderlyingStrat):    
    def __init__(self,
                 period: numbers.Number,
                 **kwargs):

        super().__init__(
            period,
            strat_arr=a,
            **kwargs ) 


class TestDefi(TestCase):
    def test_defi_i1(self):
        '''
        Goal is to compare defi_i with defi_i_fast
        '''
        self.o=opt_main.OptMain("2007_2022_08",
                         loops=1, 
                         nb_macro_modes=1,
                         strat_arr=a_simple,
                         )
        
        self.o.defi_ex("total")
        self.o.defi_ent("total")
        
        ind="CAC40"
        d="total"
        
        pf1=vbt.Portfolio.from_signals(self.o.data_dic[ind][d],
                                      self.o.ents[ind],
                                      self.o.exs[ind],
                                      freq="1d",
                                      ) 

        rr1=round(np.mean(pf1.get_total_return().values),3)
        rb1=round(np.mean(pf1.total_market_return.values),3)        

        ust=StratT1("2007_2022_08",symbol_index="CAC40")
        ust.run()
        
        pf2=vbt.Portfolio.from_signals(ust.data, ust.entries,ust.exits,
                              freq="1d")
        
        rr2=round(np.mean(pf2.get_total_return().values),3)
        rb2=round(np.mean(pf2.total_market_return.values),3)  
        
        self.assertEqual(np.shape(self.o.ents["CAC40"]),np.shape(ust.entries))
        self.assertEqual(np.shape(self.o.exs["CAC40"]),np.shape(ust.exits))
        
        self.assertTrue(np.equal(self.o.ents["CAC40"], ust.entries).all().all())
        self.assertTrue(np.equal(self.o.exs["CAC40"], ust.exits).all().all())

        self.assertEqual(rr1,rr2)
        self.assertEqual(rb1,rb2)

    def test_defi_i2(self):
        '''
        Goal is to compare defi_i with defi_i_fast
        '''
        self.o=opt_main.OptMain("2007_2022_08",
                         loops=1, 
                         nb_macro_modes=3,
                         strat_arr=a,
                         test_window_start_init=0,
                         )

        self.o.defi_ex("total")
        self.o.defi_ent("total")
        
        ind="CAC40"
        d="total"
        
        pf1=vbt.Portfolio.from_signals(self.o.data_dic[ind][d],
                                      self.o.ents[ind],
                                      self.o.exs[ind],
                                      freq="1d",
                                      ) 

        rr1=round(np.mean(pf1.get_total_return().values),3)
        rb1=round(np.mean(pf1.total_market_return.values),3)  
        
        ust=StratT2("2007_2022_08",symbol_index="CAC40")
        ust.run()
        
        pf2=vbt.Portfolio.from_signals(ust.data, ust.entries,ust.exits,
                              freq="1d")
        
        rr2=round(np.mean(pf2.get_total_return().values),3)
        rb2=round(np.mean(pf2.total_market_return.values),3)  
        
        self.assertEqual(np.shape(self.o.ents["CAC40"]),np.shape(ust.entries))
        self.assertEqual(np.shape(self.o.exs["CAC40"]),np.shape(ust.exits))

        self.assertTrue(np.equal(self.o.ents["CAC40"], ust.entries).all().all())
        self.assertTrue(np.equal(self.o.exs["CAC40"], ust.exits).all().all())

        self.assertEqual(rr1,rr2)
        self.assertEqual(rb1,rb2)
        
    def test_defi_i3(self):
        '''
        With macro in addition
        '''
        self.o=opt_main.OptMain("2007_2022_08",
                         loops=1, 
                         nb_macro_modes=1,
                         strat_arr=a_simple,
                         )
        
        self.o.defi_ex("total")
        self.o.defi_ent("total")
        self.o.macro_mode("total")
        
        ind="CAC40"
        d="total"
        
        pf1=vbt.Portfolio.from_signals(self.o.data_dic[ind][d],
                                      self.o.ents[ind],
                                      self.o.exs[ind],
                                      short_entries=self.o.ents_short[ind],
                                      short_exits=self.o.exs_short[ind],
                                      freq="1d",
                                      ) 

        rr1=round(np.mean(pf1.get_total_return().values),3)
        rb1=round(np.mean(pf1.total_market_return.values),3)        

        ust=StratT1("2007_2022_08",symbol_index="CAC40")
        ust.run()
        
        pf2=vbt.Portfolio.from_signals(ust.data, ust.entries,ust.exits,
                              short_entries=ust.entries_short,short_exits  =ust.exits_short,
                              freq="1d")
        
        rr2=round(np.mean(pf2.get_total_return().values),3)
        rb2=round(np.mean(pf2.total_market_return.values),3)  
        
        self.assertEqual(np.shape(self.o.ents["CAC40"]),np.shape(ust.entries))
        self.assertEqual(np.shape(self.o.exs["CAC40"]),np.shape(ust.exits))
        
        self.assertTrue(np.equal(self.o.ents["CAC40"], ust.entries).all().all())
        self.assertTrue(np.equal(self.o.exs["CAC40"], ust.exits).all().all())
        self.assertTrue(np.equal(self.o.ents_short["CAC40"], ust.entries_short).all().all())
        self.assertTrue(np.equal(self.o.exs_short["CAC40"], ust.exits_short).all().all())
        
        self.assertEqual(rr1,rr2)
        self.assertEqual(rb1,rb2)
        
    def test_defi_i4(self):
        '''
        With macro in addition
        '''
        self.o=opt_main.OptMain("2007_2022_08",
                         loops=1, 
                         nb_macro_modes=3,
                         strat_arr=a, 
                         test_window_start_init=0,
                         dir_bull="long", 
                         dir_uncertain="both",
                         dir_bear="both"
                         )

        self.o.defi_ex("total")
        self.o.defi_ent("total")
        self.o.macro_mode("total")
        
        ind="CAC40"
        d="total"
        
        pf1=vbt.Portfolio.from_signals(self.o.data_dic[ind][d],
                                      self.o.ents[ind],
                                      self.o.exs[ind],
                                      short_entries=self.o.ents_short[ind],
                                      short_exits=self.o.exs_short[ind],
                                      freq="1d",
                                      ) 

        rr1=round(np.mean(pf1.get_total_return().values),3)
        rb1=round(np.mean(pf1.total_market_return.values),3)  
        
        ust=StratT2("2007_2022_08",symbol_index="CAC40")
        ust.run()
        
        pf2=vbt.Portfolio.from_signals(ust.data, ust.entries,ust.exits,
                              short_entries=ust.entries_short,short_exits  =ust.exits_short,         
                              freq="1d")
        
        rr2=round(np.mean(pf2.get_total_return().values),3)
        rb2=round(np.mean(pf2.total_market_return.values),3)  
        
        self.assertEqual(np.shape(self.o.ents["CAC40"]),np.shape(ust.entries))
        self.assertEqual(np.shape(self.o.exs["CAC40"]),np.shape(ust.exits))

        self.assertTrue(np.equal(self.o.ents["CAC40"], ust.entries).all().all())
        self.assertTrue(np.equal(self.o.exs["CAC40"], ust.exits).all().all())
        self.assertTrue(np.equal(self.o.macro_trend["CAC40"]["total"], ust.macro_trend).all().all())

        self.assertTrue(np.equal(self.o.ents_short["CAC40"], ust.entries_short).all().all())
        self.assertTrue(np.equal(self.o.exs_short["CAC40"], ust.exits_short).all().all())

        self.assertEqual(rr1,rr2)
        self.assertEqual(rb1,rb2)        
