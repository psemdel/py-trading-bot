#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jun 26 21:38:23 2022

@author: maxime
"""

from django.test import TestCase
from core import presel, strat
from core.caller import name_to_ust_or_presel
from orders.models import (Fees, StockEx, Action, ActionSector,
                          ActionCategory, Strategy, Currency, Candidates, Excluded,
                          get_exchange_actions, get_candidates)
from reporting.models import Report

class TestbtP(TestCase):
    def setUp(self):
        f=Fees.objects.create(name="zero",fixed=0,percent=0)
        cat=ActionCategory.objects.create(name="actions",short="ACT")
        strategy=Strategy.objects.create(name="none")
        self.strategy2=Strategy.objects.create(name="realmadrid", class_name="PreselRealMadrid")
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
        
        self.report1=Report()
        self.report1.save(testing=True)
        
        actions=get_exchange_actions("Paris")
        self.ust=strat.StratDiv("1y",prd=True, actions=actions,exchange="Paris")
        self.ust.run()
        
  #hist slow does not need code here
    def test_actualize_hist_vol_slow(self):
        strategy=Strategy.objects.create(name="hist_slow")
        self.pr=presel.PreselHistVolSlow("1y",prd=True,input_ust=self.ust,st=strategy)

        Candidates.objects.create(strategy=strategy,stock_ex=self.e)
        self.pr.actualize()
        #cand=get_candidates("hist_slow","Paris")
        
    def test_actualize_hist_vol_slow2(self):
        strategy=Strategy.objects.create(name="hist_slow")
        self.pr=presel.PreselHistVolSlow("1y",prd=True, input_ust=self.ust,st=strategy)
        
        Candidates.objects.create(strategy=strategy,stock_ex=self.e)
        self.pr.actualize()
        #cand=get_candidates("hist_slow","Paris")
        
    def test_actualize_realmadrid(self):
        self.pr=presel.PreselRealMadrid("1y",prd=True,input_ust=self.ust,st=self.strategy2)
        Excluded.objects.create(name="realmadrid", strategy=self.strategy2)
        Candidates.objects.create(strategy=self.strategy2,stock_ex=self.e)
        self.pr.actualize()
        cand=get_candidates("realmadrid","Paris")
        self.assertEqual(len(cand.retrieve()),2)
    
    def test_actualize_realmadrid2(self):
        self.pr=presel.PreselRealMadrid("1y",prd=True, input_ust=self.ust,st=self.strategy2)
        Excluded.objects.create(name="realmadrid", strategy=self.strategy2)
        Candidates.objects.create(strategy=self.strategy2,stock_ex=self.e)
        self.pr.actualize()
        cand=get_candidates("realmadrid","Paris")
        self.assertEqual(len(cand.retrieve()),2)  
        
    def test_realmadrid_perform(self):
        self.pr=presel.PreselRealMadrid("1y",prd=True, input_ust=self.ust, st=self.strategy2)
        Excluded.objects.create(name="realmadrid", strategy=self.strategy2)
        Candidates.objects.create(strategy=self.strategy2,stock_ex=self.e)
        self.pr.actualize()
        
        self.pr.perform(self.report1)

    def test_wq(self):
        st=Strategy.objects.create(name="wq54", class_name="PreselWQ54")
        wq=presel.PreselWQ("1y",input_ust=self.ust,nb=54,st=st)
        wq.perform(self.report1)
        
    def test_retard(self):
        st=Strategy.objects.create(name="retard", class_name="PreselRetard")
        
        ust_or_pr=name_to_ust_or_presel(
            "PreselRetard",
            self.ust.period,
            input_ust=self.ust,
            prd=True,
            it_is_index=False,
            st=st
            )  
        ust_or_pr.perform(self.report1)

    def test_divergence(self):
        st=Strategy.objects.create(name="divergence", class_name="PreselDivergence")
        
        ust_or_pr=name_to_ust_or_presel(
            "PreselDivergence",
            self.ust.period,
            input_ust=self.ust,
            prd=True,
            it_is_index=False,
            st=st
            )  
        ust_or_pr.perform(self.report1)    
