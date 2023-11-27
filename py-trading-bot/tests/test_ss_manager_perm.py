#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 12 21:59:42 2023

@author: maxime
"""
import numpy as np
from django.test import TestCase
from orders import ss_manager
from orders import models as m
import pandas as pd
import reporting.models as m2

class TestSSManager(TestCase):
    def setUp(self):
        f=m.Fees.objects.create(name="zero",fixed=0,percent=0)
        
        self.e=m.StockEx.objects.create(name="Paris",fees=f,ib_ticker="SBF",main_index=None,ib_auth=True)
        self.e2=m.StockEx.objects.create(name="XETRA",fees=f,ib_ticker="IBIS",main_index=None,ib_auth=True)
        self.e3=m.StockEx.objects.create(name="MONEP",fees=f,ib_ticker="MONEP",main_index=None,ib_auth=True)
        self.e4=m.StockEx.objects.create(name="NYSE",fees=f,ib_ticker="NYSE",main_index=None,ib_auth=True)
        c=m.Currency.objects.create(name="euro")
        c2=m.Currency.objects.create(name="US")
        cat=m.ActionCategory.objects.create(name="actions",short="ACT")
        cat2=m.ActionCategory.objects.create(name="index",short="IND") #for action_to_etf
        cat3=m.ActionCategory.objects.create(name="ETF",short="ETF")
        self.strategy=m.Strategy.objects.create(name="none",priority=10,target_order_size=1000)
        self.strategy2=m.Strategy.objects.create(name="strat2",priority=20,target_order_size=1000)
        self.strategy3=m.Strategy.objects.create(name="retard_keep",priority=30,target_order_size=1000)
        
        self.s=m.ActionSector.objects.create(name="undefined")
        
        self.a=m.Action.objects.create(
            symbol='AC.PA',
            #ib_ticker='AC',
            name="Accor",
            stock_ex=self.e,
            currency=c,
            category=cat,
            #strategy=strategy,
            sector=self.s,
            )
        self.a2=m.Action.objects.create(
            symbol='AI.PA',
            #ib_ticker='AC',
            name="Air liquide",
            stock_ex=self.e,
            currency=c,
            category=cat,
            #strategy=strategy,
            sector=self.s,
            )
        self.a3=m.Action.objects.create(
            symbol='AIR.PA',
            #ib_ticker='AC',
            name="Airbus",
            stock_ex=self.e,
            currency=c,
            category=cat,
            #strategy=strategy,
            sector=self.s,
            )
        self.a4=m.Action.objects.create(
            symbol='JKHY',
            #ib_ticker='AC',
            name="Jack Henry",
            stock_ex=self.e4,
            currency=c2,
            category=cat,
            #strategy=strategy,
            sector=self.s,
            )
        
        etf1=m.Action.objects.create(
            symbol='BNP.PA',
            #ib_ticker='AC',
            name="bbs",
            stock_ex=self.e,
            currency=c,
            category=cat3,
            #strategy=strategy,
            )   
        
        etf2=m.Action.objects.create(
            symbol='KER.PA',
            #ib_ticker='AC',
            name="KER",
            stock_ex=self.e,
            currency=c,
            category=cat3,
            #strategy=strategy,
            )         
        
        self.a5=m.Action.objects.create(
            symbol='^FCHI',
            ib_ticker_explicit='CAC40',
            name='Cac40',
            stock_ex=self.e,
            currency=c,
            category=cat2,
            etf_long=etf1,
            etf_short=etf2,
            ) 
        self.a6=m.Action.objects.create(
            symbol='MC.PA',
            #ib_ticker='AC',
            name="LVMH",
            stock_ex=self.e,
            currency=c,
            category=cat,
            #strategy=strategy,
            sector=self.s,
            )
        
        ss1=m.StockStatus.objects.get(action=self.a)
        ss1.strategy=self.strategy
        ss1.save()
        
        ss2=m.StockStatus.objects.get(action=self.a2)
        ss2.strategy=self.strategy
        ss2.save()
        
        ss3=m.StockStatus.objects.get(action=self.a3)
        ss3.strategy=self.strategy2
        ss3.save()
        
        ss4=m.StockStatus.objects.get(action=self.a4)
        ss4.strategy=self.strategy2
        ss4.save()
        
        ss5=m.StockStatus.objects.get(action=self.a6)
        ss5.strategy=None
        ss5.save()
        
        self.r=m2.Report.objects.create()
        self.ss_m=ss_manager.StockStatusManager(self.r,"Paris")
  

    def test_perform_orders(self):
        ss1=m.StockStatus.objects.get(action=self.a)
        self.assertEqual(ss1.quantity,0)

        df=pd.DataFrame(data=[["AC.PA",0,self.strategy.id,True,10,1,1]],
                        columns=["symbol","quantity","strategy_id","order_in_ib","priority","norm_quantity","norm_delta_quantity"],
                        )
        df.set_index("symbol",inplace=True)
        self.ss_m.target_ss=df
        self.ss_m.perform_orders(testing=True)
        
        ss1=m.StockStatus.objects.get(action=self.a) #need to be called again otherwise not actualized somehow
        self.assertTrue(ss1.quantity>0)
        ent_ex_symbols=m2.OrderExecutionMsg.objects.filter(report=self.r)
        self.assertEqual(ent_ex_symbols[0].action,self.a)
    
        self.r=m2.Report.objects.create()
        self.ss_m=ss_manager.StockStatusManager(self.r,"Paris")
        df=pd.DataFrame(data=[["AI.PA",0,self.strategy.id,True,10,-1,-1]],
                        columns=["symbol","quantity","strategy_id","order_in_ib","priority","norm_quantity","norm_delta_quantity"],
                        )
        df.set_index("symbol",inplace=True)
        self.ss_m.target_ss=df
        self.ss_m.perform_orders(testing=True) 
        
        ss1=m.StockStatus.objects.get(action=self.a2)
        self.assertTrue(ss1.quantity<0)
        ent_ex_symbols=m2.OrderExecutionMsg.objects.filter(report=self.r)
        self.assertEqual(ent_ex_symbols[0].action,self.a2)

    def test_perform_orders2(self):  
        df=pd.DataFrame(data=[["AI.PA",0,self.strategy.id,True,10,1,2]],
                        columns=["symbol","quantity","strategy_id","order_in_ib","priority","norm_quantity","norm_delta_quantity"],
                        )
        df.set_index("symbol",inplace=True)
        self.ss_m.target_ss=df
        self.ss_m.perform_orders(testing=True) 
        
        ss1=m.StockStatus.objects.get(action=self.a2)
        self.assertTrue(ss1.quantity>0)     
        
