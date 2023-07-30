#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 24 19:45:34 2022

@author: maxime
"""

import unittest
from core import presel
import vectorbtpro as vbt

class TestBT(unittest.TestCase):
    def setUp(self):
        self.period="2007_2022_08"
        self.symbol_index="CAC40"
        
    def test_preselect_vol(self):
        self.bti=presel.PreselVol(self.period,symbol_index=self.symbol_index)
        self.bti.run()

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
        
    def test_preselect_retard(self):
        self.bti=presel.PreselRetard(self.period,symbol_index=self.symbol_index)
        self.bti.run()

        pf=vbt.Portfolio.from_signals(self.bti.close,
                                      self.bti.entries,
                                      self.bti.exits,
                                      short_entries=self.bti.entries_short,
                                      short_exits  =self.bti.exits_short,
                                      freq="1d",
                                      call_seq='auto',
                                      cash_sharing=True,
                             )

        self.assertEqual(round(pf.get_total_return(),2),17.97) 

    def test_preselect_macd_vol(self):
        self.bti=presel.PreselMacdVol(self.period,symbol_index=self.symbol_index)
        self.bti.run()

        pf=vbt.Portfolio.from_signals(self.bti.close,
                                      self.bti.entries,
                                      self.bti.exits,
                                      short_entries=self.bti.entries_short,
                                      short_exits  =self.bti.exits_short,
                                      freq="1d",
                                      call_seq='auto',
                                      cash_sharing=True,
                             )

        self.assertEqual(round(pf.get_total_return(),2),1.78) 
        
    def test_preselect_hist_vol(self):
        self.bti=presel.PreselHistVol(self.period,symbol_index=self.symbol_index)
        self.bti.run()

        pf=vbt.Portfolio.from_signals(self.bti.close,
                                      self.bti.entries,
                                      self.bti.exits,
                                      short_entries=self.bti.entries_short,
                                      short_exits  =self.bti.exits_short,
                                      freq="1d",
                                      call_seq='auto',
                                      cash_sharing=True,
                             )

        self.assertEqual(round(pf.get_total_return(),2),2.74) 
        
    def test_preselect_divergence(self):
        self.bti=presel.PreselDivergence(self.period,symbol_index=self.symbol_index)
        self.bti.run()

        pf=vbt.Portfolio.from_signals(self.bti.close,
                                      self.bti.entries,
                                      self.bti.exits,
                                      short_entries=self.bti.entries_short,
                                      short_exits  =self.bti.exits_short,
                                      freq="1d",
                                      call_seq='auto',
                                      cash_sharing=True,
                             )

        self.assertEqual(round(pf.get_total_return(),2),17.73)  
        
    def test_preselect_macd_vol_macro(self):
        self.bti=presel.PreselMacdVolMacro(self.period,symbol_index=self.symbol_index)
        self.bti.run()

        pf=vbt.Portfolio.from_signals(self.bti.close,
                                      self.bti.entries,
                                      self.bti.exits,
                                      short_entries=self.bti.entries_short,
                                      short_exits  =self.bti.exits_short,
                                      freq="1d",
                                      call_seq='auto',
                                      cash_sharing=True,
                             )

        self.assertEqual(round(pf.get_total_return(),2),2.74 ) 
        
    def test_preselect_retard_macro(self):
        self.bti=presel.PreselRetardMacro(self.period,symbol_index=self.symbol_index)
        self.bti.run()

        pf=vbt.Portfolio.from_signals(self.bti.close,
                                      self.bti.entries,
                                      self.bti.exits,
                                      short_entries=self.bti.entries_short,
                                      short_exits  =self.bti.exits_short,
                                      freq="1d",
                                      call_seq='auto',
                                      cash_sharing=True,
                             )

        self.assertEqual(round(pf.get_total_return(),2),23.68) 

    def test_preselect_divergence_blocked(self):
        self.bti=presel.PreselDivergenceBlocked(self.period,symbol_index=self.symbol_index)
        self.bti.run()

        pf=vbt.Portfolio.from_signals(self.bti.close,
                                      self.bti.entries,
                                      self.bti.exits,
                                      short_entries=self.bti.entries_short,
                                      short_exits  =self.bti.exits_short,
                                      freq="1d",
                                      call_seq='auto',
                                      cash_sharing=True,
                             )

        self.assertEqual(round(pf.get_total_return(),2),5.11) 

    def test_preselect_divergence_blocked_im(self):
        self.bti=presel.PreselDivergenceBlockedIm(self.period,symbol_index=self.symbol_index)
        self.bti.run()

        pf=vbt.Portfolio.from_signals(self.bti.close,
                                      self.bti.entries,
                                      self.bti.exits,
                                      short_entries=self.bti.entries_short,
                                      short_exits  =self.bti.exits_short,
                                      freq="1d",
                                      call_seq='auto',
                                      cash_sharing=True,
                             )

        self.assertEqual(round(pf.get_total_return(),2),8.14) 
        
    def test_preselect_vol_slow(self):
        self.bti=presel.PreselVolSlow(self.period,symbol_index=self.symbol_index)
        self.bti.run()

        pf=vbt.Portfolio.from_signals(self.bti.close,
                                      self.bti.entries,
                                      self.bti.exits,
                                      short_entries=self.bti.entries_short,
                                      short_exits  =self.bti.exits_short,
                                      freq="1d",
                                      call_seq='auto',
                                      cash_sharing=True,
                             )

        self.assertEqual(round(pf.get_total_return(),2),10.1)   
        
    def test_preselect_realmadrid(self):
        self.bti=presel.PreselRealMadrid(self.period,symbol_index=self.symbol_index)
        self.bti.run()

        pf=vbt.Portfolio.from_signals(self.bti.close,
                                       self.bti.entries,
                                       self.bti.exits,
                                       short_entries=self.bti.entries_short,
                                       short_exits  =self.bti.exits_short,
                                       freq="1d",
                                       call_seq='auto',
                                       cash_sharing=True,
                              )

        self.assertEqual(round(pf.get_total_return(),2),9.08 )     

    def test_preselect_realmadrid_blocked(self):
        self.bti=presel.PreselRealMadridBlocked(self.period,symbol_index=self.symbol_index)
        self.bti.run()

        pf=vbt.Portfolio.from_signals(self.bti.close,
                                       self.bti.entries,
                                       self.bti.exits,
                                       short_entries=self.bti.entries_short,
                                       short_exits  =self.bti.exits_short,
                                       freq="1d",
                                       call_seq='auto',
                                       cash_sharing=True,
                              )

        self.assertEqual(round(pf.get_total_return(),2),6.0) 


    def test_preselect_macd_vol_slow(self):
        self.bti=presel.PreselMacdVolSlow(self.period,symbol_index=self.symbol_index)
        self.bti.run()

        pf=vbt.Portfolio.from_signals(self.bti.close,
                                       self.bti.entries,
                                       self.bti.exits,
                                       short_entries=self.bti.entries_short,
                                       short_exits  =self.bti.exits_short,
                                       freq="1d",
                                       call_seq='auto',
                                       cash_sharing=True,
                              )

        self.assertEqual(round(pf.get_total_return(),2),-0.61) 

    def test_preselect_hist_vol_slow(self):
        self.bti=presel.PreselHistVolSlow(self.period,symbol_index=self.symbol_index)
        self.bti.run()

        pf=vbt.Portfolio.from_signals(self.bti.close,
                                       self.bti.entries,
                                       self.bti.exits,
                                       short_entries=self.bti.entries_short,
                                       short_exits  =self.bti.exits_short,
                                       freq="1d",
                                       call_seq='auto',
                                       cash_sharing=True,
                              )

        self.assertEqual(round(pf.get_total_return(),2),2.81)  
           
if __name__ == '__main__':
    unittest.main()        
