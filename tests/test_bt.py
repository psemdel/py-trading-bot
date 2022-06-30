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
        self.bti=bt.BT("CAC40","2007_2022","test","long")
        
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

        self.assertEqual(round(pf.get_total_return(),2),2.61)
        
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

        self.assertEqual(round(pf.get_total_return(),2),8.25) 

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

        self.assertEqual(round(pf.get_total_return(),2),1.02) 
        
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

        self.assertEqual(round(pf.get_total_return(),2),0.78) 
        
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

        self.assertEqual(round(pf.get_total_return(),2),10.7)  
        
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

        self.assertEqual(round(pf.get_total_return(),2),-0.5)  
        
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

        self.assertEqual(round(pf.get_total_return(),2),11.5) 

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

        self.assertEqual(round(pf.get_total_return(),2),2.21) 
        
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

        self.assertEqual(round(pf.get_total_return(),2),0.28)   
        
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

         self.assertEqual(round(pf.get_total_return(),2),10.97)     

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

         self.assertEqual(round(pf.get_total_return(),2),1.62) 

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

         self.assertEqual(round(pf.get_total_return(),2),0.47) 

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

         self.assertEqual(round(pf.get_total_return(),2),2.89) 

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

         self.assertEqual(round(pf.get_total_return(),2),-0.35) 
           
if __name__ == '__main__':
    unittest.main()        
