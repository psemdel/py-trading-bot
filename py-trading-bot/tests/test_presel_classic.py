#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Mar 26 23:30:05 2023

@author: maxime
"""

from django.test import TestCase
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

        #proves that StratHold changed nothing
        self.assertTrue(abs(round(pf_ref.get_total_return(),2)-round(pf_test.get_total_return(),2))<0.02) #some micro orders
        
    def test_one_action(self):
        ust=strat.StratG("2007_2022_08",symbol_index="CAC40")
        ust.run()
        
        #year 2
        pf_ref_part1=vbt.Portfolio.from_signals(ust.close[509:766], ust.entries[509:766],ust.exits[509:766],
                              short_entries=ust.entries_short[509:766],short_exits  =ust.exits_short[509:766],
                              freq="1d")
        
        #At year change there is a buy/sell which impact the result, first we test it and then the total
        #year 3
        pf_ref_part2=vbt.Portfolio.from_signals(ust.close[766:1022], ust.entries[766:1022],ust.exits[766:1022],
                              short_entries=ust.entries_short[766:1022],short_exits  =ust.exits_short[766:1022],
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

        pf_test_part1=vbt.Portfolio.from_orders( 
            self.bti.close[509:766], 
            size_type="targetpercent", 
            size=self.bti.size[509:766],                              
            freq="1d", 
            call_seq = "auto",
            cash_sharing=True 
            )

        pf_test_part2=vbt.Portfolio.from_orders( 
            self.bti.close[766:1022], 
            size_type="targetpercent", 
            size=self.bti.size[766:1022],                              
            freq="1d", 
            call_seq = "auto",
            cash_sharing=True 
            )

        self.assertEqual(round(pf_ref_part1.get_total_return().iloc[0],2), round(pf_test_part1.get_total_return(),2))
        self.assertEqual(round(pf_ref_part2.get_total_return().iloc[0],2), round(pf_test_part2.get_total_return(),2))   
        
        pf_ref=vbt.Portfolio.from_signals(ust.close[509:], ust.entries[509:],ust.exits[509:],
                              short_entries=ust.entries_short[509:],short_exits  =ust.exits_short[509:],
                              freq="1d")
        

        self.assertEqual(round(pf_ref.get_total_return().iloc[0],2), round(pf_test.get_total_return(),2))

        #Same with 2nd stock
        arr=[0 for ii in range(np.shape(self.bti.pf_opt._allocations)[1])]
        arr[1]=1

        for ii in range(len(self.bti.pf_opt._allocations)):
            self.bti.pf_opt._allocations[ii]=arr
        
        pf_test=self.bti.apply_underlying_strat("StratG")
        number_of_trades_ref=len(pf_ref.trades.records[pf_ref.trades.records['col']==1])
        number_of_trades_test=len(pf_test.trades.records)
        self.assertTrue(abs(number_of_trades_test-number_of_trades_ref)<5) #some trades for balancing at year end     
        self.assertTrue((1-abs(round(pf_ref.get_total_return().iloc[1],2)/round(pf_test.get_total_return(),2)))<0.1) 

    def test_two_action(self):
        #Complicated to test as 0,5 and 0,5 does not behave like 0,5 + 0,5
        #indeed when one symbol is in long and the other in short, the size becomes 1 and -1 and not 0.5 and -0.5 like by the stratG sum

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
        
        trades_ref0=pf_ref.trades.records[pf_ref.trades.records['col']==0]
        trades_ref1=pf_ref.trades.records[pf_ref.trades.records['col']==1]
        trades_ptest0=pf_test.trades.records[pf_test.trades.records['col']==0]
        trades_ptest1=pf_test.trades.records[pf_test.trades.records['col']==1]
        
        self.assertTrue(set(trades_ref0) & set(trades_ptest0)==set(trades_ref0))
        self.assertTrue(set(trades_ref1) & set(trades_ptest1)==set(trades_ref0))

        
        self.assertTrue(abs(round((pf_ref.get_total_return().iloc[0]+pf_ref.get_total_return().iloc[1])/2,2)-round(pf_test.get_total_return(),2))<0.2)
            
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

        trades_test2=pf_test2.trades.records
        trades_test3=pf_test3.trades.records

        self.assertTrue(set(trades_ref0) & set(trades_test2)==set(trades_ref0))
        self.assertTrue(set(trades_ref1) & set(trades_test3)==set(trades_ref0))    

        
        
        
