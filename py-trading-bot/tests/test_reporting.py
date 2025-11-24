#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 30 13:49:54 2022

@author: maxime
"""

from django.test import TestCase
import reporting.models as m

from orders.models import (Fees, StockEx, Action, ActionCategory, ActionSector, Strategy, 
                          Currency, StratCandidates, Excluded)
                          
from trading_bot.settings import _settings                         

#Test reporting, it looks for errors.
class TestReporting(TestCase):
    def setUp(self):
        f=Fees.objects.create(name="zero",fixed=0,percent=0)
        
        e=StockEx.objects.create(name="Paris",fees=f,ib_ticker="SBF",main_index=None,ib_auth=True)
        self.e=e
        e2=StockEx.objects.create(name="XETRA",fees=f,ib_ticker="IBIS",main_index=None,ib_auth=True)
        e3=StockEx.objects.create(name="Nasdaq",fees=f,ib_ticker="NASDAQ",main_index=None,ib_auth=True)
        e4=StockEx.objects.create(name="NYSE",fees=f,ib_ticker="NYSE",main_index=None,ib_auth=True,presel_at_sector_level=True)
        e5=StockEx.objects.create(name="MONEP",fees=f,ib_ticker="MONEP",main_index=None,ib_auth=True)
        e6=StockEx.objects.create(name="EUREX",fees=f,ib_ticker="EUREX",main_index=None,ib_auth=True)
        e7=StockEx.objects.create(name="CME",fees=f,ib_ticker="CME",main_index=None,ib_auth=True)
        
        c=Currency.objects.create(name="euro",symbol="EUR")
        c2=Currency.objects.create(name="dollar",symbol="USD")
        
        cat=ActionCategory.objects.create(name="actions",short="ACT")
        cat2=ActionCategory.objects.create(name="ETF",short="ETF")
        cat3=ActionCategory.objects.create(name="index",short="IND")
        strategy=Strategy.objects.create(name="none")
        strategy2=Strategy.objects.create(name="normal",class_name="StratG")
        strategy3=Strategy.objects.create(name="divergence",class_name="PreselDivergence")
        strategy4=Strategy.objects.create(name="retard",class_name="PreselRetard")
        strategy5=Strategy.objects.create(name="macd_vol",class_name="PreselMacdVol")
        strategy6=Strategy.objects.create(name="realmadrid",class_name="PreselRealMadrid")
        strategy7=Strategy.objects.create(name="wq7",class_name="PreselWQ7")
        strategy8=Strategy.objects.create(name="wq31",class_name="PreselWQ31")
        strategy9=Strategy.objects.create(name="wq53",class_name="PreselWQ53")
        strategy10=Strategy.objects.create(name="wq54",class_name="PreselWQ54")
        strategy11=Strategy.objects.create(name="retard_keep",class_name="PreselRetardKeep")
        strategy12=Strategy.objects.create(name="hist_slow",class_name="PreselHistVolSlow")
        
        self.strategy7=strategy7
        self.strategy8=strategy8
        self.strategy9=strategy9
        self.strategy10=strategy10
        
        StratCandidates.objects.create(strategy=strategy2)
        s=ActionSector.objects.create(name="undefined")
        s2=ActionSector.objects.create(name="it")
        s3=ActionSector.objects.create(name="fin")
        
        self.ustrategy=strategy
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
            stock_ex=e7,
            currency=c2,
            category=cat3,
            etf_long=etf1,
            etf_short=etf1,
            sector=s,
            )    
       
        Excluded.objects.create(name="retard", strategy=strategy4)
        Excluded.objects.create(name="all",strategy=strategy)
        
        self.report1=m.Report(sector=s)
        self.report1.save(testing=True)
        _settings["PERFORM_ORDER"]=False #avoid to perform orders
        
        e.main_index=self.a5
        e.strategies_in_use.add(strategy3)
        e.strategies_in_use.add(strategy4)
        e.strategies_in_use.add(strategy5)
        e.strategies_in_use.add(strategy6)
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
        self.report1.daily_report(symbols=["^FCHI","^GDAXI"],it_is_index=True,testing=True)

    def test_Paris(self):
        self.report1.daily_report(exchange="Paris",testing=True)  
        
    def test_Paris_wq(self):
        self.e.strategies_in_use.add(self.strategy7)
        self.e.strategies_in_use.add(self.strategy8)
        self.e.strategies_in_use.add(self.strategy9)
        self.e.strategies_in_use.add(self.strategy10)
        self.e.save()
        self.report1.daily_report(exchange="Paris",testing=True)      

    def test_XETRA(self):
        self.ust=self.report1.daily_report(exchange="XETRA",testing=True)   
        
    def test_presel_Nasdaq(self):
        self.ust=self.report1.daily_report(exchange="Nasdaq",testing=True)   
        
    def test_presel_NYSE(self):
        #should perform the report at sector level
        report=m.Report()
        report.daily_report(exchange="NYSE",testing=True) 
                 
