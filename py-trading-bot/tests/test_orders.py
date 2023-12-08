#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 28 20:20:29 2022

@author: maxime
"""
import numpy as np
from django.test import TestCase
from orders import models as m
from datetime import datetime
from trading_bot.settings import _settings 

import sys
if sys.version_info.minor>=9:
    from zoneinfo import ZoneInfo
else:
    from backports.zoneinfo import ZoneInfo
    
tz_Paris=ZoneInfo('Europe/Paris')

class TestConversion(TestCase):
    def test_period_YF_to_ib(self):
        self.assertEqual(m.period_YF_to_ib("10"),None)
        self.assertEqual(m.period_YF_to_ib("10 d"),"10 D")
        self.assertEqual(m.period_YF_to_ib("10 mo"),"10 M")
        self.assertEqual(m.period_YF_to_ib("10 y"),"10 Y")

    def test_interval_YF_to_ib(self):
        self.assertEqual(m.interval_YF_to_ib(None),"1 day")
        self.assertEqual(m.interval_YF_to_ib("10"),"1 day")
        self.assertEqual(m.interval_YF_to_ib("10 m"),"10 mins")
        self.assertEqual(m.interval_YF_to_ib("10 h"),"10 hours")
        self.assertEqual(m.interval_YF_to_ib("10 d"),"10 day")

class TestOrders(TestCase):
    def setUp(self):
        f=m.Fees.objects.create(name="zero",fixed=0,percent=0)
        
        self.e=m.StockEx.objects.create(name="Paris",fees=f,ib_ticker="SBF",main_index=None,ib_auth=True)
        self.e2=m.StockEx.objects.create(name="XETRA",fees=f,ib_ticker="IBIS",main_index=None,ib_auth=True)
        self.e3=m.StockEx.objects.create(name="MONEP",fees=f,ib_ticker="MONEP",main_index=None,ib_auth=True)
        self.e4=m.StockEx.objects.create(name="EUREX",fees=f,ib_ticker="EUREX",main_index=None,ib_auth=False)
        c=m.Currency.objects.create(name="euro")
        self.c=c
        cat=m.ActionCategory.objects.create(name="actions",short="ACT")
        cat2=m.ActionCategory.objects.create(name="index",short="IND") #for action_to_etf
        self.cat2=cat2
        self.strategy=m.Strategy.objects.create(name="none")
        self.strategy2=m.Strategy.objects.create(name="strat2")
        self.s=m.ActionSector.objects.create(name="undefined")
        
        m.Action.objects.create(
            symbol='AC.PA',
            #ib_ticker='AC',
            name="Accor",
            stock_ex=self.e,
            currency=c,
            category=cat,
            #strategy=strategy,
            sector=self.s,
            )
        self.a=m.Action.objects.create(
            symbol='AI.PA',
            #ib_ticker='AC',
            name="Air liquide",
            stock_ex=self.e,
            currency=c,
            category=cat,
            #strategy=strategy,
            sector=self.s,
            intro_date=datetime(2020,1,1,tzinfo=tz_Paris)
            )
        self.a2=m.Action.objects.create(
            symbol='AIR.PA',
            #ib_ticker='AC',
            name="Airbus",
            stock_ex=self.e,
            currency=c,
            category=cat,
            #strategy=strategy,
            sector=self.s,
            )
        self.a3=m.Action.objects.create(
            symbol='SIE.DE',
            #ib_ticker='AC',
            name="Siemens",
            stock_ex=self.e2,
            currency=c,
            category=cat,
            #strategy=strategy,
            sector=self.s,
            
            )
        
        self.a5=m.Action.objects.create(
            symbol='^FCHI',
            ib_ticker_explicit='CAC40',
            name='Cac40',
            stock_ex=self.e3,
            currency=c,
            category=cat2,
            sector=self.s
            ) 
        
        self.e.main_index=self.a5
        self.e.save()
        
        self.a6=m.Action.objects.create(
            symbol='^GDAXI',
            ib_ticker_explicit='DAX',
            name='DAX',
            stock_ex=self.e4,
            currency=c,
            category=cat2,
            sector=self.s
            ) 
        
        self.e2.main_index=self.a6
        self.e2.save()        

        self.actions=[self.a, self.a2, self.a3]
        m.Excluded.objects.create(name="all",strategy=self.strategy)
 
    def test_exchange_to_symbol(self):
        self.assertEqual(m.exchange_to_index_symbol("Paris"),["CAC40","^FCHI"])
        self.assertEqual(m.exchange_to_index_symbol("XETRA"),["DAX","^GDAXI"])

    def test_get_exchange_actions(self):
        self.assertEqual(len(m.get_exchange_actions("Paris")),3)
        self.assertEqual(len(m.get_exchange_actions("XETRA")),1)     
        
    def test_get_pf(self):
        ss1=m.StockStatus.objects.get(action=self.a)
        ss1.quantity=1
        ss1.strategy=self.strategy
        ss1.save()

        ss2=m.StockStatus.objects.get(action=self.a2)
        ss2.quantity=1
        ss2.strategy=self.strategy2
        ss2.save()
        
        r=m.get_pf("none","Paris",False)
        self.assertEqual(r,["AI.PA"])
        
        r=m.get_pf("strat2","Paris",False)
        self.assertEqual(r,["AIR.PA"])

        r=m.get_pf("strat2","Paris",True)
        self.assertEqual(r,[])
        
        r=m.get_pf("strat2","XETRA",False)
        self.assertEqual(r,[])
        
        ss1=m.StockStatus.objects.get(action=self.a)
        ss1.quantity=-1
        ss1.strategy=self.strategy
        ss1.save()
        
        r=m.get_pf("none","Paris",False)
        self.assertEqual(r,[])
        r=m.get_pf("none","Paris",True)
        self.assertEqual(r,["AI.PA"])

    def test_pf_retrieve_all(self):
        ss1=m.StockStatus.objects.get(action=self.a)
        ss1.quantity=1
        ss1.save()
        
        ss2=m.StockStatus.objects.get(action=self.a3)
        ss2.quantity=-1
        ss2.save()
        
        self.assertTrue(self.a in m.pf_retrieve_all())
        self.assertFalse(self.a2 in m.pf_retrieve_all())
        self.assertTrue(self.a3 in m.pf_retrieve_all())
        
    def test_pf_retrieve_all_symbols(self):
        ss1=m.StockStatus.objects.get(action=self.a)
        ss1.quantity=1
        ss1.save()
        
        ss2=m.StockStatus.objects.get(action=self.a3)
        ss2.quantity=-1
        ss2.save()

        self.assertTrue(self.a.symbol in m.pf_retrieve_all_symbols())
        self.assertFalse(self.a2.symbol in m.pf_retrieve_all_symbols())
        self.assertTrue(self.a3.symbol in m.pf_retrieve_all_symbols())
        
    def test_filter_intro_action(self):
        res=m.filter_intro_action([self.a2],5)
        self.assertEqual([self.a2],res)
        res=m.filter_intro_action([self.a],5)
        self.assertEqual(0,len(res))
        
    def test_symbol_to_action(self):
        self.assertEqual(self.a, m.symbol_to_action('AI.PA'))
        self.assertEqual(self.a, m.symbol_to_action(self.a))
        
    def test_check_ib_permission(self):
        _settings["USED_API_DEFAULT"]={
            "orders": "IB", 
            "alerting": "IB", 
            "reporting": "YF", 
            }
        
        m.check_ib_permission(None)    
        self.assertEqual(_settings["USED_API"]["orders"],"IB")
        self.assertEqual(_settings["USED_API"]["alerting"],"IB")
        self.assertEqual(_settings["USED_API"]["reporting"],"YF")
        
    def test_check_ib_permission2(self):
        _settings["USED_API_DEFAULT"]={
            "orders": "CCXT", 
            "alerting": "MT5", 
            "reporting": "TS", 
            }
        
        m.check_ib_permission(["AI","AC"])    
        self.assertEqual(_settings["USED_API"]["orders"],"CCXT")
        self.assertEqual(_settings["USED_API"]["alerting"],"MT5")
        self.assertEqual(_settings["USED_API"]["reporting"],"TS")      

        
        