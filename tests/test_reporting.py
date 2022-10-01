#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 30 13:49:54 2022

@author: maxime
"""

import unittest
import numpy as np
from django.test import TestCase
import reporting.models as m
from reporting.models import Alert
from orders.models import (Fees, StockEx, Action, Index, ActionCategory, ActionSector, Strategy, 
                          Currency, StratCandidates, PF, Excluded, OrderCapital)
import vectorbtpro as vbt

class TestReporting(TestCase):
    def setUp(self):
        f=Fees.objects.create(name="zero",fixed=0,percent=0)
        
        e=StockEx.objects.create(name="Paris",fees=f,ib_ticker="SBF")
        self.e=e
        e2=StockEx.objects.create(name="XETRA",fees=f,ib_ticker="IBIS")
        c=Currency.objects.create(name="euro")
        cat=ActionCategory.objects.create(name="actions",short="ACT")
        cat2=ActionCategory.objects.create(name="actions",short="ETF")
        strategy=Strategy.objects.create(name="none")
        strategy2=Strategy.objects.create(name="normal")
        strategy3=Strategy.objects.create(name="divergence")
        strategy4=Strategy.objects.create(name="retard")
        strategy5=Strategy.objects.create(name="wq7")
        strategy6=Strategy.objects.create(name="wq31")
        strategy7=Strategy.objects.create(name="wq53")
        strategy8=Strategy.objects.create(name="wq54")
        StratCandidates.objects.create(name="normal",strategy=strategy2)
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
        
        etf1=Action.objects.create(
            symbol='BNP.PA',
            #ib_ticker='AC',
            name="Airbus",
            stock_ex=e,
            currency=c,
            category=cat2,
            strategy=strategy,
            sector=s,
            )   

        Index.objects.create(
            symbol='^FCHI',
            #ib_ticker='AC',
            name='Cac40',
            stock_ex=e,
            currency=c,
            etf_long=etf1,
            etf_short=etf1
            ) 
        Index.objects.create(
            symbol='^GDAXI',
            #ib_ticker='AC',
            name='DAX',
            stock_ex=e,
            currency=c,
            etf_long=etf1,
            etf_short=etf1
            )           
        PF.objects.create(name="divergence",short=False,strategy= strategy3,stock_ex=e,sector=s)
        PF.objects.create(name="retard",short=False,strategy= strategy4,stock_ex=e,sector=s)
        PF.objects.create(name="retard",short=True,strategy= strategy4,stock_ex=e,sector=s)
        
        Excluded.objects.create(name="retard", strategy=strategy4)
        Excluded.objects.create(name="all",strategy=strategy)
        OrderCapital.objects.create(capital=1,name="divergence",strategy=strategy3,stock_ex=e,sector=s)
        OrderCapital.objects.create(capital=1,name="retard",strategy=strategy4,stock_ex=e,sector=s)
        OrderCapital.objects.create(capital=1,name="wq7",strategy=strategy5,stock_ex=e,sector=s)
        OrderCapital.objects.create(capital=1,name="wq31",strategy=strategy6,stock_ex=e,sector=s)
        OrderCapital.objects.create(capital=1,name="wq53",strategy=strategy7,stock_ex=e,sector=s)
        OrderCapital.objects.create(capital=1,name="wq54",strategy=strategy8,stock_ex=e,sector=s)
        
        self.report1=m.Report()
        self.report1.save()

    def test_concat(self):
        self.report1.concat("test")
        self.assertEqual(self.report1.text,"test\n")

    def test_daily_report_index(self):
        self.report1.daily_report_index(["^FCHI","^GDAXI"])

    def test_presel(self):
        self.st=self.report1.daily_report_action("Paris")   
        self.report1.presel(self.st,"Paris")
        
    def test_presel_wq(self):
        self.st=self.report1.daily_report_action("Paris")      
        self.report1.presel_wq(self.st,"Paris")
         
if __name__ == '__main__':
    unittest.main() 