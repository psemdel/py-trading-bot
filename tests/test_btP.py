#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jun 26 21:38:23 2022

@author: maxime
"""

from django.test import TestCase
import unittest
from core import btP, stratP
from orders.models import (Fees, StockEx, Action, ActionSector,
                          ActionCategory, Strategy, Currency, Candidates, Excluded)
from orders.models import  get_candidates

class TestbtP(TestCase):
    def setUp(self):
        f=Fees.objects.create(name="zero",fixed=0,percent=0)
        cat=ActionCategory.objects.create(name="actions",short="ACT")
        strategy=Strategy.objects.create(name="none")
        e=StockEx.objects.create(name="Paris",fees=f,ib_ticker="SBF")
        self.e=e
        c=Currency.objects.create(name="euro")
        s=ActionSector.objects.create(name="sec")
        
        self.strategy=strategy
        a=Action.objects.create(
            symbol='AC.PA',
            #ib_ticker='AC',
            name="Accor",
            stock_ex=e,
            currency=c,
            category=cat,
            strategy=strategy,
            sector=s,
            )
        self.a=a
        a=Action.objects.create(
            symbol='AI.PA',
            #ib_ticker='AC',
            name="Air liquide",
            stock_ex=e,
            currency=c,
            category=cat,
            strategy=strategy,
            sector=s,
            )
        a=Action.objects.create(
            symbol='AIR.PA',
            #ib_ticker='AC',
            name="Airbus",
            stock_ex=e,
            currency=c,
            category=cat,
            strategy=strategy,
            sector=s,
            )        
        self.st=stratP.StratPRD(["AC.PA", "AI.PA","AIR.PA"],"1y")
        self.st.call_strat("strat_kama_stoch_matrend_macdbb_macro",
                      macro_trend_bull="long",
                      macro_trend_uncertain="both",
                      macro_trend_bear="both"
                      ) 
        
        self.presel=btP.Presel(st=self.st,exchange="Paris")
        
  #hist slow does not need code here
    def test_actualize_hist_vol_slow(self):
        strategy=Strategy.objects.create(name="hist_slow")
        Candidates.objects.create(name="hist_slow", strategy=strategy,stock_ex=self.e)
        self.presel.actualize_hist_vol_slow("Paris")
        #cand=get_candidates("hist_slow","Paris")
        
    def test_actualize_realmadrid(self):
        strategy=Strategy.objects.create(name="realmadrid")
        Excluded.objects.create(name="realmadrid", strategy=strategy)
        Candidates.objects.create(name="realmadrid", strategy=strategy,stock_ex=self.e)
        self.presel.actualize_realmadrid("Paris")
        cand=get_candidates("realmadrid","Paris")
        self.assertEqual(len(cand.retrieve()),2)
        
    def test_wq(self):
        wq=btP.WQPRD(st=self.st,exchange="Paris")
        wq.call_wqa(7)
        
if __name__ == '__main__':
    unittest.main() 