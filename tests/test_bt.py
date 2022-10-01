#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 24 19:45:34 2022

@author: maxime
"""

import unittest
import core.indicators as ic
from core import bt
import math
import vectorbtpro as vbt

class TestBT(unittest.TestCase):
    def setUp(self):
        self.bti=bt.BT("CAC40","2007_2022_08","test","long")
        
    def test_preselect_vol(self):
        self.bti.preselect_vol()

        pf=vbt.Portfolio.from_signals(self.bti.close,
                                      self.bti.entries,
                                      self.bti.exits,
                                      short_entries=self.bti.entries_short,
                                      short_exits  =self.bti.exits_short,
                                      freq="1d",
                                      call_seq='auto',
                                      cash_sharing=True,
                             )

        self.assertEqual(round(pf.get_total_return(),2),1.88)
        
    def test_preselect_retard(self):
        self.bti.preselect_retard()

        pf=vbt.Portfolio.from_signals(self.bti.close,
                                      self.bti.entries,
                                      self.bti.exits,
                                      short_entries=self.bti.entries_short,
                                      short_exits  =self.bti.exits_short,
                                      freq="1d",
                                      call_seq='auto',
                                      cash_sharing=True,
                             )

        self.assertEqual(round(pf.get_total_return(),2),18.03) 

    def test_preselect_macd_vol(self):
        self.bti.preselect_macd_vol()

        pf=vbt.Portfolio.from_signals(self.bti.close,
                                      self.bti.entries,
                                      self.bti.exits,
                                      short_entries=self.bti.entries_short,
                                      short_exits  =self.bti.exits_short,
                                      freq="1d",
                                      call_seq='auto',
                                      cash_sharing=True,
                             )

        self.assertEqual(round(pf.get_total_return(),2),-0.20) 
        
    def test_preselect_hist_vol(self):
        self.bti.preselect_hist_vol()

        pf=vbt.Portfolio.from_signals(self.bti.close,
                                      self.bti.entries,
                                      self.bti.exits,
                                      short_entries=self.bti.entries_short,
                                      short_exits  =self.bti.exits_short,
                                      freq="1d",
                                      call_seq='auto',
                                      cash_sharing=True,
                             )

        self.assertEqual(round(pf.get_total_return(),2),0.24) 
        
    def test_preselect_divergence(self):
        self.bti.preselect_divergence()

        pf=vbt.Portfolio.from_signals(self.bti.close,
                                      self.bti.entries,
                                      self.bti.exits,
                                      short_entries=self.bti.entries_short,
                                      short_exits  =self.bti.exits_short,
                                      freq="1d",
                                      call_seq='auto',
                                      cash_sharing=True,
                             )

        self.assertEqual(round(pf.get_total_return(),2),19.67)  
        
    def test_preselect_macd_vol_macro(self):
        self.bti.preselect_macd_vol_macro()

        pf=vbt.Portfolio.from_signals(self.bti.close,
                                      self.bti.entries,
                                      self.bti.exits,
                                      short_entries=self.bti.entries_short,
                                      short_exits  =self.bti.exits_short,
                                      freq="1d",
                                      call_seq='auto',
                                      cash_sharing=True,
                             )

        self.assertEqual(round(pf.get_total_return(),2),-1.61)  
        
    def test_preselect_retard_macro(self):
        self.bti.preselect_retard_macro()

        pf=vbt.Portfolio.from_signals(self.bti.close,
                                      self.bti.entries,
                                      self.bti.exits,
                                      short_entries=self.bti.entries_short,
                                      short_exits  =self.bti.exits_short,
                                      freq="1d",
                                      call_seq='auto',
                                      cash_sharing=True,
                             )

        self.assertEqual(round(pf.get_total_return(),2),13.35) 

    def test_preselect_divergence_blocked(self):
        self.bti.preselect_divergence_blocked()

        pf=vbt.Portfolio.from_signals(self.bti.close,
                                      self.bti.entries,
                                      self.bti.exits,
                                      short_entries=self.bti.entries_short,
                                      short_exits  =self.bti.exits_short,
                                      freq="1d",
                                      call_seq='auto',
                                      cash_sharing=True,
                             )

        self.assertEqual(round(pf.get_total_return(),2),5.74) 
        
    def test_preselect_vol_slow(self):
        self.bti.preselect_vol_slow()

        pf=vbt.Portfolio.from_signals(self.bti.close,
                                      self.bti.entries,
                                      self.bti.exits,
                                      short_entries=self.bti.entries_short,
                                      short_exits  =self.bti.exits_short,
                                      freq="1d",
                                      call_seq='auto',
                                      cash_sharing=True,
                             )

        self.assertEqual(round(pf.get_total_return(),2),-0.12)   
        
    def test_preselect_realmadrid(self):
         self.bti.preselect_realmadrid()

         pf=vbt.Portfolio.from_signals(self.bti.close,
                                       self.bti.entries,
                                       self.bti.exits,
                                       short_entries=self.bti.entries_short,
                                       short_exits  =self.bti.exits_short,
                                       freq="1d",
                                       call_seq='auto',
                                       cash_sharing=True,
                              )

         self.assertEqual(round(pf.get_total_return(),2),8.05)     

    def test_preselect_macd_vol_slow(self):
         self.bti.preselect_macd_vol_slow()

         pf=vbt.Portfolio.from_signals(self.bti.close,
                                       self.bti.entries,
                                       self.bti.exits,
                                       short_entries=self.bti.entries_short,
                                       short_exits  =self.bti.exits_short,
                                       freq="1d",
                                       call_seq='auto',
                                       cash_sharing=True,
                              )

         self.assertEqual(round(pf.get_total_return(),2),-0.86) 

         self.bti.preselect_macd_vol_slow(only_exit_strat11=True)

         pf=vbt.Portfolio.from_signals(self.bti.close,
                                       self.bti.entries,
                                       self.bti.exits,
                                       short_entries=self.bti.entries_short,
                                       short_exits  =self.bti.exits_short,
                                       freq="1d",
                                       call_seq='auto',
                                       cash_sharing=True,
                              )

         self.assertEqual(round(pf.get_total_return(),2),-0.86) 

    def test_preselect_hist_vol_slow(self):
         self.bti.preselect_hist_vol_slow()

         pf=vbt.Portfolio.from_signals(self.bti.close,
                                       self.bti.entries,
                                       self.bti.exits,
                                       short_entries=self.bti.entries_short,
                                       short_exits  =self.bti.exits_short,
                                       freq="1d",
                                       call_seq='auto',
                                       cash_sharing=True,
                              )

         self.assertEqual(round(pf.get_total_return(),2),-0.21) 

         self.bti.preselect_hist_vol_slow(only_exit_strat11=True)

         pf=vbt.Portfolio.from_signals(self.bti.close,
                                       self.bti.entries,
                                       self.bti.exits,
                                       short_entries=self.bti.entries_short,
                                       short_exits  =self.bti.exits_short,
                                       freq="1d",
                                       call_seq='auto',
                                       cash_sharing=True,
                              )

         self.assertEqual(round(pf.get_total_return(),2),-0.04) 
           
if __name__ == '__main__':
    unittest.main()        
