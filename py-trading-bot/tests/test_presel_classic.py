#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Mar 26 23:30:05 2023

@author: maxime
"""

from django.test import TestCase
import unittest
from core import presel_classic, strat
import vectorbtpro as vbt
import numpy as np

class TestPreselClassic(TestCase):
    def setUp(self):
        self.bti=presel_classic.PreselClassic("2007_2022_08",symbol_index="CAC40")
        
        
    def test_hold(self):
        pf_opt = vbt.PortfolioOptimizer.from_pypfopt(
            prices=self.bti.close,
            every="Y",
            target="max_sharpe"
        )
        pf_ref=pf_opt.simulate(self.bti.close,freq="1d")
        
        self.bti.max_sharpeY()
        pf_test=self.bti.apply_underlying_strat("StratHold")
        self.assertEqual(round(pf_ref.get_total_return(),2),round(pf_test.get_total_return(),2))
        
    def test_one_action(self):
        ust=strat.StratG("2007_2022_08",symbol_index="CAC40")
        ust.run()
        pf_ref=vbt.Portfolio.from_signals(ust.close[509:], ust.entries[509:],ust.exits[509:],
                              short_entries=ust.entries_short[509:],short_exits  =ust.exits_short[509:],
                              freq="1d")
        
        self.bti.pf_opt = vbt.PortfolioOptimizer.from_pypfopt(
            prices=self.bti.close,
            every="Y",
            target="max_sharpe"
        )
        
        arr=[0 for ii in range(np.shape(self.bti.pf_opt._allocations)[1])]
        arr[0]=1

        for ii in range(len(self.bti.pf_opt._allocations)):
            self.bti.pf_opt._allocations[ii]=arr
            
        
        pf_test=self.bti.apply_underlying_strat("StratG")
        
        #tolerance as at the year change there is a sell/buy which can have an impact
        self.assertTrue(abs(round(pf_ref.get_total_return()[0],2)-round(pf_test.get_total_return(),2))<0.1)
        
        arr=[0 for ii in range(np.shape(self.bti.pf_opt._allocations)[1])]
        arr[1]=1

        for ii in range(len(self.bti.pf_opt._allocations)):
            self.bti.pf_opt._allocations[ii]=arr
        
        pf_test=self.bti.apply_underlying_strat("StratG")
        
        #tolerance as at the year change there is a sell/buy which can have an impact
        self.assertTrue(abs(round(pf_ref.get_total_return()[1],2)-round(pf_test.get_total_return(),2))<0.1)   
        
    def test_two_action(self):
        ust=strat.StratG("2007_2022_08",symbol_index="CAC40")
        ust.run()
        
        window_start=509
        pf_ref=vbt.Portfolio.from_signals(ust.close[window_start:], ust.entries[window_start:],ust.exits[window_start:],
                              short_entries=ust.entries_short[window_start:],short_exits  =ust.exits_short[window_start:],
                              freq="1d")
        
        self.bti.pf_opt = vbt.PortfolioOptimizer.from_pypfopt(
            prices=self.bti.close,
            every="Y",
            target="max_sharpe"
        )
        
        arr=[0 for ii in range(np.shape(self.bti.pf_opt._allocations)[1])]
        arr[0]=0.5
        arr[1]=0.5
    
        for ii in range(len(self.bti.pf_opt._allocations)):
            self.bti.pf_opt._allocations[ii]=arr
            
        pf_test=self.bti.apply_underlying_strat("StratG")
        self.assertTrue(abs(round((pf_ref.get_total_return()[0]+pf_ref.get_total_return()[1])/2,2)-round(pf_test.get_total_return(),2))<0.2)
            
        arr=[0 for ii in range(np.shape(self.bti.pf_opt._allocations)[1])]
        arr[0]=0.5
        
        for ii in range(len(self.bti.pf_opt._allocations)):
            self.bti.pf_opt._allocations[ii]=arr
            
        pf_test2=self.bti.apply_underlying_strat("StratG")    
        
        arr=[0 for ii in range(np.shape(self.bti.pf_opt._allocations)[1])]
        arr[1]=0.5
        
        for ii in range(len(self.bti.pf_opt._allocations)):
            self.bti.pf_opt._allocations[ii]=arr
            
        pf_test3=self.bti.apply_underlying_strat("StratG")  
        
        #is not equal as targetpercent takes money from one action for the other
        self.assertTrue(abs(pf_test2.get_total_return()+pf_test3.get_total_return()-pf_test.get_total_return())<0.2)

        #needs to check for unique as balancing order can occurs for pf_test.
        self.assertEqual(
            len(np.unique(np.concatenate((pf_test2.trades.records["entry_idx"],pf_test3.trades.records["entry_idx"])))),
            len(np.unique(pf_test.trades.records["entry_idx"]))
            )
    
if __name__ == '__main__':
    unittest.main()          