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

from orders.models import (Fees, StockEx, Action, ActionCategory, ActionSector, Strategy, 
                          Currency, StratCandidates, PF, Excluded, OrderCapital)
                          
from trading_bot.settings import _settings                         
import vectorbtpro as vbt

#Test reporting, it looks for errors.
class TestReporting(TestCase):
    def setUp(self):
        f=Fees.objects.create(name="zero",fixed=0,percent=0)
        
        e=StockEx.objects.create(name="Paris",fees=f,ib_ticker="SBF",main_index=None,ib_auth=True)
        self.e=e
        e2=StockEx.objects.create(name="XETRA",fees=f,ib_ticker="IBIS",main_index=None,ib_auth=True)
        e3=StockEx.objects.create(name="Nasdaq",fees=f,ib_ticker="SMART",main_index=None,ib_auth=True)
        e4=StockEx.objects.create(name="NYSE",fees=f,ib_ticker="NYSE",main_index=None,ib_auth=True)
        e5=StockEx.objects.create(name="MONEP",fees=f,ib_ticker="MONEP",main_index=None,ib_auth=True)
        e6=StockEx.objects.create(name="EUREX",fees=f,ib_ticker="EUREX",main_index=None,ib_auth=True)
        
        c=Currency.objects.create(name="euro")
        c2=Currency.objects.create(name="dollar")
        
        cat=ActionCategory.objects.create(name="actions",short="ACT")
        cat2=ActionCategory.objects.create(name="ETF",short="ETF")
        cat3=ActionCategory.objects.create(name="index",short="IND")
        strategy=Strategy.objects.create(name="none")
        strategy2=Strategy.objects.create(name="normal")
        strategy3=Strategy.objects.create(name="divergence")
        strategy4=Strategy.objects.create(name="retard")
        strategy5=Strategy.objects.create(name="macd_vol")
        strategy6=Strategy.objects.create(name="realmadrid")
        strategy7=Strategy.objects.create(name="wq7")
        strategy8=Strategy.objects.create(name="wq31")
        strategy9=Strategy.objects.create(name="wq53")
        strategy10=Strategy.objects.create(name="wq54")
        strategy11=Strategy.objects.create(name="retard_keep")
        strategy12=Strategy.objects.create(name="hist_slow")
        
        StratCandidates.objects.create(name="normal",strategy=strategy2)
        s=ActionSector.objects.create(name="undefined")
        s2=ActionSector.objects.create(name="it")
        s3=ActionSector.objects.create(name="fin")
        
        self.strategy=strategy
        a=Action.objects.create(
            symbol='AC.PA',
            #ib_ticker='AC',
            name="Accor",
            stock_ex=e,
            currency=c,
            category=cat,
            #strategy=strategy,
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
            #strategy=strategy,
            sector=s,
            )
        a=Action.objects.create(
            symbol='AIR.PA',
            #ib_ticker='AC',
            name="Airbus",
            stock_ex=e,
            currency=c,
            category=cat,
            #strategy=strategy,
            sector=s,
            )   
        a=Action.objects.create(
            symbol='LIN.DE',
            #ib_ticker='AC',
            name="Linde",
            stock_ex=e2,
            currency=c,
            category=cat,
            #strategy=strategy,
            sector=s,
            )  
        a=Action.objects.create(
            symbol='BAYN.DE',
            #ib_ticker='AC',
            name="Bayer",
            stock_ex=e2,
            currency=c,
            category=cat,
            #strategy=strategy,
            sector=s,
            )  
        a=Action.objects.create(
            symbol='MBG.DE',
            #ib_ticker='AC',
            name="Mercedes",
            stock_ex=e2,
            currency=c,
            category=cat,
            #strategy=strategy,
            sector=s,
            )         
        a=Action.objects.create(
            symbol='AMZN',
            #ib_ticker='AC',
            name="Amazon",
            stock_ex=e3,
            currency=c2,
            category=cat,
            #strategy=strategy,
            sector=s,
            )         
        a=Action.objects.create(
            symbol='DDOG',
            #ib_ticker='AC',
            name="Datadog",
            stock_ex=e3,
            currency=c2,
            category=cat,
            #strategy=strategy,
            sector=s,
            )         
        a=Action.objects.create(
            symbol='GOOG',
            #ib_ticker='AC',
            name="Google",
            stock_ex=e3,
            currency=c2,
            category=cat,
            #strategy=strategy,
            sector=s,
            )             
        a=Action.objects.create(
            symbol="ACN",
            #ib_ticker='AC',
            name="ACN",
            stock_ex=e4,
            currency=c2,
            category=cat,
            #strategy=strategy,
            sector=s2,
            )        
        a=Action.objects.create(
            symbol="ADBE",
            #ib_ticker='AC',
            name="ADBE",
            stock_ex=e4,
            currency=c2,
            category=cat,
            #strategy=strategy,
            sector=s2,
            )   
        a=Action.objects.create(
            symbol="ADP",
            #ib_ticker='AC',
            name="ADP",
            stock_ex=e4,
            currency=c2,
            category=cat,
            #strategy=strategy,
            sector=s2,
            )         
        a=Action.objects.create(
            symbol="AFL",
            #ib_ticker='AC',
            name="AFL",
            stock_ex=e4,
            currency=c2,
            category=cat,
            #strategy=strategy,
            sector=s3,
            )          
        a=Action.objects.create(
            symbol="ALL",
            #ib_ticker='AC',
            name="ALL",
            stock_ex=e4,
            currency=c2,
            category=cat,
            #strategy=strategy,
            sector=s3,
            )   
        a=Action.objects.create(
            symbol="AXP",
            #ib_ticker='AC',
            name="AXP",
            stock_ex=e4,
            currency=c2,
            category=cat,
            #strategy=strategy,
            sector=s3,
            )     
        
        etf1=Action.objects.create(
            symbol='BNP.PA',
            #ib_ticker='AC',
            name="bbs",
            stock_ex=e,
            currency=c,
            category=cat2,
            #strategy=strategy,
            sector=s,
            )   

        self.a5=Action.objects.create(
            symbol='^FCHI',
            ib_ticker_explicit='CAC40',
            name='Cac40',
            stock_ex=e5,
            currency=c,
            category=cat3,
            etf_long=etf1,
            etf_short=etf1,
            sector=s
            ) 
        self.a6=Action.objects.create(
            symbol='^GDAXI',
            ib_ticker_explicit='DAX',
            name='DAX',
            stock_ex=e6,
            currency=c,
            category=cat3,
            etf_long=etf1,
            etf_short=etf1,
            sector=s,
            )  
        self.a7=Action.objects.create(
            symbol='^IXIC',
            ib_ticker_explicit='COMP',
            name='Nasdaq',
            stock_ex=e3,
            currency=c2,
            category=cat3,
            etf_long=etf1,
            etf_short=etf1,
            sector=s,
            )         
        
        self.a8=Action.objects.create(
            symbol='^DJI',
            name='Dow Jones',
            ib_ticker_explicit='INDU',
            stock_ex=e4,
            currency=c2,
            category=cat3,
            etf_long=etf1,
            etf_short=etf1,
            sector=s,
            )    

         
        #PF.objects.create(name="divergence",short=False,strategy= strategy3,stock_ex=e,sector=s)
        #PF.objects.create(name="retard",short=False,strategy= strategy4,stock_ex=e,sector=s)
        #PF.objects.create(name="retard",short=True,strategy= strategy4,stock_ex=e,sector=s)
       
        Excluded.objects.create(name="retard", strategy=strategy4)
        Excluded.objects.create(name="all",strategy=strategy)
        OrderCapital.objects.create(capital=1,name="divergence_Paris",strategy=strategy3,stock_ex=e,sector=s)
        OrderCapital.objects.create(capital=1,name="retard_Paris",strategy=strategy4,stock_ex=e,sector=s)
        OrderCapital.objects.create(capital=1,name="macd_vol_Paris",strategy=strategy5,stock_ex=e,sector=s)
        OrderCapital.objects.create(capital=1,name="realmadrid_Paris",strategy=strategy6,stock_ex=e,sector=s)
        OrderCapital.objects.create(capital=1,name="wq7_Paris",strategy=strategy7,stock_ex=e,sector=s)
        OrderCapital.objects.create(capital=1,name="wq31_Paris",strategy=strategy8,stock_ex=e,sector=s)
        OrderCapital.objects.create(capital=1,name="wq53_Paris",strategy=strategy9,stock_ex=e,sector=s)
        OrderCapital.objects.create(capital=1,name="wq54_Paris",strategy=strategy10,stock_ex=e,sector=s)
        OrderCapital.objects.create(capital=1,name="retard_keep",strategy=strategy11,stock_ex=e,sector=s)
        
        self.report1=m.Report(sector=s)
        self.report1.save()
        
        _settings["PERFORM_ORDER"]=False #avoid to perform orders
        
        e.main_index=self.a5
        e.strategies_in_use.add(strategy3)
        e.strategies_in_use.add(strategy4)
        e.strategies_in_use.add(strategy5)
        e.strategies_in_use.add(strategy6)
        e.strategies_in_use.add(strategy7)
        e.strategies_in_use.add(strategy8)
        e.strategies_in_use.add(strategy9)
        e.strategies_in_use.add(strategy10)
        e.strategies_in_use.add(strategy11)
        e.save()
        
        e2.main_index=self.a6
        e2.strategies_in_use.add(strategy3)
        e2.strategies_in_use.add(strategy4)
        e2.strategies_in_use.add(strategy5)
        e2.strategies_in_use.add(strategy6)
        e2.strategies_in_use.add(strategy7)
        e2.strategies_in_use.add(strategy8)
        e2.strategies_in_use.add(strategy9)
        e2.strategies_in_use.add(strategy10)
        e2.strategies_in_use.add(strategy11)
        e2.save() 
        
        e3.main_index=self.a7
        e3.strategies_in_use.add(strategy3)
        e3.strategies_in_use.add(strategy4)
        e3.strategies_in_use.add(strategy5)
        e3.strategies_in_use.add(strategy6)
        e3.strategies_in_use.add(strategy7)
        e3.strategies_in_use.add(strategy8)
        e3.strategies_in_use.add(strategy9)
        e3.strategies_in_use.add(strategy10)
        e3.strategies_in_use.add(strategy11)
        e3.save()         
        
        e4.main_index=self.a8
        e4.presel_at_sector_level=True
        e4.save()   
        
        s2.strategies_in_use.add(strategy3)
        s2.strategies_in_use.add(strategy4)
        s2.strategies_in_use.add(strategy5)
        s2.strategies_in_use.add(strategy6)
        s2.strategies_in_use.add(strategy7)
        s2.strategies_in_use.add(strategy8)
        s2.strategies_in_use.add(strategy9)
        s2.strategies_in_use.add(strategy10)
        s2.strategies_in_use.add(strategy11)
        s2.save() 
        
        s3.strategies_in_use.add(strategy3)
        s3.strategies_in_use.add(strategy4)
        s3.strategies_in_use.add(strategy5)
        s3.strategies_in_use.add(strategy6)
        s3.strategies_in_use.add(strategy7)
        s3.strategies_in_use.add(strategy8)
        s3.strategies_in_use.add(strategy9)
        s3.strategies_in_use.add(strategy10)
        s3.strategies_in_use.add(strategy11)
        s3.save()         
        
        
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
        
    def test_presel_XETRA(self):
        self.st=self.report1.daily_report_action("XETRA")   
        self.report1.presel(self.st,"XETRA")
        
    def test_presel_wq_XETRA(self):
        self.st=self.report1.daily_report_action("XETRA")      
        self.report1.presel_wq(self.st,"XETRA")
        
    def test_presel_Nasdaq(self):
        self.st=self.report1.daily_report_action("Nasdaq")   
        self.report1.presel(self.st,"Nasdaq")
        
    def test_presel_wq_Nasdaq(self):
        self.st=self.report1.daily_report_action("Nasdaq")      
        self.report1.presel_wq(self.st,"Nasdaq")   
        
    def test_presel_NYSE(self):
        for s in ["it","fin"]: 
            report=m.Report()
            st=report.daily_report_action("NYSE",sec=s) 
            report.presel(st,"NYSE",sec=s)
            report.presel_wq(st,"NYSE",sec=s)
                 
if __name__ == '__main__':
    unittest.main() 
