#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jun 26 21:38:23 2022

@author: maxime
"""

from django.test import TestCase
import unittest
from core import preselP, stratP
from orders.models import (Fees, StockEx, Action, ActionSector,
                          ActionCategory, Strategy, Currency, Candidates, Excluded,
                          get_exchange_actions)
from orders.models import  get_candidates

class TestbtP(TestCase):
    def setUp(self):
        f=Fees.objects.create(name="zero",fixed=0,percent=0)
        cat=ActionCategory.objects.create(name="actions",short="ACT")
        strategy=Strategy.objects.create(name="none")
        e=StockEx.objects.create(name="Paris",fees=f,ib_ticker="SBF",main_index=None,ib_auth=True)
        e3=StockEx.objects.create(name="Nasdaq",fees=f,ib_ticker="SMART",main_index=None,ib_auth=True)
        self.e=e
        c=Currency.objects.create(name="euro")
        s=ActionSector.objects.create(name="sec")
        
        self.strategy=strategy
        self.a=Action.objects.create(
            symbol='AC.PA',
            #ib_ticker='AC',
            name="Accor",
            stock_ex=e,
            currency=c,
            category=cat,
            #strategy=strategy,
            sector=s,
            )
        self.a2=Action.objects.create(
            symbol='AI.PA',
            #ib_ticker='AC',
            name="Air liquide",
            stock_ex=e,
            currency=c,
            category=cat,
            #strategy=strategy,
            sector=s,
            )
        self.a3=Action.objects.create(
            symbol='AIR.PA',
            #ib_ticker='AC',
            name="Airbus",
            stock_ex=e,
            currency=c,
            category=cat,
            #strategy=strategy,
            sector=s,
            )
        self.actions=[self.a, self.a2, self.a3]   
        
        cat2=ActionCategory.objects.create(name="index",short="IND")
        cat3=ActionCategory.objects.create(name="ETF",short="ETF")
        
        etf1=Action.objects.create(
            symbol='BNP.PA',
            #ib_ticker='AC',
            name="bbs",
            stock_ex=self.e,
            currency=c,
            category=cat3,
            #strategy=strategy,
            sector=s,
            ) 
        
        self.a5=Action.objects.create(
            symbol='^FCHI',
            ib_ticker_explicit='CAC40',
            name='Cac40',
            stock_ex=e3,
            currency=c,
            category=cat2,
            etf_long=etf1,
            etf_short=etf1,
            sector=s
            ) 
        
        e.main_index=self.a5
        e.save()
        
  #hist slow does not need code here
    def test_actualize_hist_vol_slow(self):
        use_IB, actions=get_exchange_actions("Paris")
        print(actions)
        
        self.presel=preselP.PreselPRD(use_IB,actions1=actions,period1="1y",exchange="Paris")
        
        strategy=Strategy.objects.create(name="hist_slow")
        Candidates.objects.create(strategy=strategy,stock_ex=self.e)
        self.presel.actualize_hist_vol_slow("Paris")
        #cand=get_candidates("hist_slow","Paris")
        
    def test_actualize_hist_vol_slow2(self):
        use_IB, actions=get_exchange_actions("Paris")
        self.st=stratP.StratPRD(use_IB,actions1=self.actions,period1="1y")
        self.st.call_strat("strat_kama_stoch_matrend_macdbb_macro",
                      macro_trend_bull="long",
                      macro_trend_uncertain="both",
                      macro_trend_bear="both"
                      ) 
        
        self.presel=preselP.PreselPRD(use_IB,st=self.st,exchange="Paris")
        
        strategy=Strategy.objects.create(name="hist_slow")
        Candidates.objects.create(strategy=strategy,stock_ex=self.e)
        self.presel.actualize_hist_vol_slow("Paris")
        #cand=get_candidates("hist_slow","Paris")
        
    def test_actualize_realmadrid(self):
        use_IB, actions=get_exchange_actions("Paris")
        self.presel=preselP.PreselPRD(use_IB,actions1=actions,period1="1y",exchange="Paris")
        
        strategy=Strategy.objects.create(name="realmadrid")
        Excluded.objects.create(name="realmadrid", strategy=strategy)
        Candidates.objects.create(strategy=strategy,stock_ex=self.e)
        self.presel.actualize_realmadrid("Paris")
        cand=get_candidates("realmadrid","Paris")
        self.assertEqual(len(cand.retrieve()),2)
        
    def test_actualize_realmadrid2(self):
        use_IB, actions=get_exchange_actions("Paris")
        
        self.st=stratP.StratPRD(use_IB,actions1=self.actions,period1="1y")
        self.st.call_strat("strat_kama_stoch_matrend_macdbb_macro",
                      macro_trend_bull="long",
                      macro_trend_uncertain="both",
                      macro_trend_bear="both"
                      ) 
        
        self.presel=preselP.PreselPRD(use_IB,st=self.st,exchange="Paris")
        
        strategy=Strategy.objects.create(name="realmadrid")
        Excluded.objects.create(name="realmadrid", strategy=strategy)
        Candidates.objects.create(strategy=strategy,stock_ex=self.e)
        self.presel.actualize_realmadrid("Paris")
        cand=get_candidates("realmadrid","Paris")
        self.assertEqual(len(cand.retrieve()),2)        
        
    def test_wq(self):
        self.st=stratP.StratPRD(False,actions1=self.actions,period1="1y")
        self.st.call_strat("strat_kama_stoch_matrend_macdbb_macro",
                      macro_trend_bull="long",
                      macro_trend_uncertain="both",
                      macro_trend_bear="both"
                      ) 
                
        wq=preselP.WQPRD(False,st=self.st,exchange="Paris")
        wq.call_wqa(7)
        
        
if __name__ == '__main__':
    unittest.main() 
