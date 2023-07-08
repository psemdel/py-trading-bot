#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jan  7 13:46:08 2023

@author: maxime
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 28 20:20:29 2022

@author: maxime
"""

import unittest
import os
import numpy as np
from django.test import TestCase
from orders import ib
from orders import models as m
from trading_bot.settings import _settings  
from datetime import datetime, timedelta
import pandas as pd

class TestIB(TestCase):
    def setUp(self):
        f=m.Fees.objects.create(name="zero",fixed=0,percent=0)
        
        self.e=m.StockEx.objects.create(name="Paris",fees=f,ib_ticker="SBF",main_index=None,ib_auth=True)
        self.e2=m.StockEx.objects.create(name="XETRA",fees=f,ib_ticker="IBIS",main_index=None,ib_auth=True)
        self.e3=m.StockEx.objects.create(name="MONEP",fees=f,ib_ticker="MONEP",main_index=None,ib_auth=True)
        self.e4=m.StockEx.objects.create(name="NYSE",fees=f,ib_ticker="NYSE",main_index=None,ib_auth=True)
        c=m.Currency.objects.create(name="euro",symbol="EUR")
        c2=m.Currency.objects.create(name="dollar",symbol="USD")
        cat=m.ActionCategory.objects.create(name="actions",short="ACT")
        cat2=m.ActionCategory.objects.create(name="index",short="IND") #for action_to_etf
        cat3=m.ActionCategory.objects.create(name="ETF",short="ETF")
        self.strategy=m.Strategy.objects.create(name="none")
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
        self.a5=m.Action.objects.create(
            symbol='MC.PA',
            #ib_ticker='AC',
            name="Airbus",
            stock_ex=self.e,
            currency=c,
            category=cat,
            #strategy=strategy,
            sector=self.s,
            )
        self.a6=m.Action.objects.create(
            symbol='KER.PA',
            #ib_ticker='AC',
            name="Airbus",
            stock_ex=self.e,
            currency=c,
            category=cat,
            #strategy=strategy,
            sector=self.s,
            )  
        self.a5=m.Action.objects.create(
            symbol='TMUS',
            #ib_ticker='AC',
            name="T-Mobile",
            stock_ex=self.e4,
            currency=c2,
            category=cat,
            #strategy=strategy,
            sector=self.s,
            )
        self.a6=m.Action.objects.create(
            symbol='PAYX',
            #ib_ticker='AC',
            name="Pay X",
            stock_ex=self.e4,
            currency=c2,
            category=cat,
            #strategy=strategy,
            sector=self.s,
            )        
        '''
        self.a4=m.Action.objects.create(
            symbol='SIE.DE',
            #ib_ticker='AC',
            name="Siemens",
            stock_ex=self.e2,
            currency=c,
            category=cat,
            #strategy=strategy,
            sector=self.s,
            )
        '''
        etf1=m.Action.objects.create(
            symbol='BNP.PA',
            #ib_ticker='AC',
            name="bbs",
            stock_ex=self.e,
            currency=c,
            category=cat3,
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
            etf_long=etf1,
            etf_short=etf1,
            sector=self.s
            ) 
        
        self.e.main_index=self.a5
        self.e.save()
        
        self.actions=[self.a, self.a2, self.a3]
        m.Excluded.objects.create(name="all",strategy=self.strategy)
     
    def test_get_ratio(self):
        t=ib.get_ratio(self.a)
        self.assertTrue(t!=0)
        
    def test_get_last_price(self):
        ib.get_last_price(self.a4)       
        
    def test_cash_balance(self):
        self.assertTrue(ib.cash_balance()>=0)   
        self.assertTrue(ib.cash_balance(currency="USD")>=0)   

    def test_check_enough_cash(self):
        self.assertTrue(ib.check_enough_cash(1000,currency="USD"))        

    def test_entry_order_manual(self):
        _settings["PERFORM_ORDER"]=True
        op=ib.OrderPerformer("AIR.PA",self.strategy.id,10000)
        self.strategy.perform_order=False
        self.e.perform_order=False
        self.strategy.save()
        self.e.save()
        
        op=ib.OrderPerformer("AIR.PA",self.strategy.id,10000)
        op.check_auto_manual()
        self.assertEqual(op.api_used,"YF")
        
        self.strategy.perform_order=True
        self.strategy.save()
        
        op=ib.OrderPerformer("AIR.PA",self.strategy.id,10000)
        op.check_auto_manual()
        self.assertEqual(op.api_used,"YF")
        
        self.strategy.perform_order=False
        self.e.perform_order=True
        self.strategy.save()
        self.e.save()
        
        op=ib.OrderPerformer("AIR.PA",self.strategy.id,10000)
        op.check_auto_manual()
        self.assertEqual(op.api_used,"YF")
        
        self.strategy.perform_order=True
        self.e.perform_order=True
        self.strategy.save()
        self.e.save()
        
        op=ib.OrderPerformer("AIR.PA",self.strategy.id,10000)
        op.check_auto_manual()
        self.assertEqual(op.api_used,"IB")
        
        _settings["PERFORM_ORDER"]=False
        op=ib.OrderPerformer("AIR.PA",self.strategy.id,10000)
        op.check_auto_manual()
        self.assertEqual(op.api_used,"YF")

    def test_get_order(self):
        #Entry and buy
        op=ib.OrderPerformer("AC.PA",self.strategy.id,1)
        
        op.get_order(True)
        self.assertTrue(op.new_order_bool)
        
        #Entry and sell
        op=ib.OrderPerformer("AI.PA",self.strategy.id,1)
        
        op.get_order(False)
        self.assertTrue(op.new_order_bool)
        
        #Entry and buy
        op=ib.OrderPerformer("AIR.PA",self.strategy.id,1)
        o=m.Order.objects.create(action=self.a3, strategy=self.strategy, short=True)          
        op.get_order(True)

        self.assertFalse(op.new_order_bool)      
        self.assertEqual(o, op.order)

    def test_get_delta_size(self):
        op=ib.OrderPerformer("AIR.PA",self.strategy.id,10000)
        op.api_used="YF"
        op.get_order(True) #to create self.order
        op.get_delta_size()
        self.assertFalse(op.reverse)
        self.assertEqual(op.delta_size,10000)

    def test_entry_place(self):

        op=ib.OrderPerformer("AIR.PA",self.strategy.id,10000)
        op.reverse=False
        
        op.api_used="YF"
        op.entry_place(True)
        self.assertEqual(op.new_order.entering_price,1.0)
        self.assertEqual(op.ss.quantity,1.0)
        
        #op.api_used="IB"
        op.entry_place(True)
        self.assertEqual(op.new_order.entering_price,1.0)
        
        #if excluded no order
        op=ib.OrderPerformer("AI.PA",self.strategy.id,10000)
        op.excluded.append("AI.PA")
        op.api_used="YF"
        op.reverse=False
        op.entry_place(True)
        self.assertFalse("new_order" in op.__dir__())
        op.entry_place(False)
        self.assertFalse("new_order" in op.__dir__())

    def test_entry_place2(self):        
        #If already in pf, no order
        op=ib.OrderPerformer("AI.PA",self.strategy.id,10000)
        op.api_used="YF"
        op.reverse=False
        
        op.ss.quantity=1
        op.ss.save()
        op.entry_place(True)
        self.assertFalse("new_order" in op.__dir__())
        
        #if reverse
        op.reverse=True
        op.entry_place(False)
        self.assertTrue("new_order" in op.__dir__())
        self.assertEqual(op.ss.quantity,-1.0)
        
        op.entry_place(True)
        self.assertTrue("new_order" in op.__dir__())
        self.assertEqual(op.ss.quantity,1.0)
        
    def test_buy_order(self):
        op=ib.OrderPerformer("AIR.PA",self.strategy.id,10000,testing=True)
        
        op.api_used="YF"
        self.assertTrue(op.buy_order_sub())
        self.assertEqual(op.ss.quantity,1)
        self.assertEqual(op.new_order.entering_price,1.0)
        self.assertFalse(op.ss.order_in_ib)
        self.assertTrue(op.executed)

        op=ib.OrderPerformer("AIR.PA",self.strategy.id,10000000,testing=True)
        op.api_used="IB"
        #expected not enough cash
        self.assertFalse(op.buy_order_sub())
        
        op=ib.OrderPerformer("AC.PA",self.strategy.id,1,testing=True)
        op.api_used="IB"
        #expected enough cash
        self.assertTrue(op.buy_order_sub())
        self.assertEqual(op.new_order.entering_price,1.0)  

    def test_sell_order(self):
        op=ib.OrderPerformer("AIR.PA",self.strategy.id,10000,testing=True)
        
        op.api_used="YF"
        self.assertTrue(op.sell_order_sub())
        self.assertEqual(op.ss.quantity,-1)
        self.assertEqual(op.new_order.entering_price,1.0)
        self.assertFalse(op.ss.order_in_ib)
        self.assertTrue(op.executed)
    
    def test_actualize_ss(self):
        ib.actualize_ss()
        
        present_ss=pd.DataFrame.from_records(m.StockStatus.objects.all().values(),index="action_id")
        print(present_ss)
        
        
    def test_get_tradable_contract_ib(self):
        c=ib.get_tradable_contract_ib(self.a2,False)
        c2=ib.IBData.get_contract_ib("AI","SBF",False)
        self.assertEqual(c,c2)
        
        from ib_insync import Stock
        c3=Stock("AI","SBF")
        self.assertEqual(c,c3)
        
        #to see the contract details
        t=Stock("IBM","SMART", primaryExchange='NYSE')
        print(ib.IBData.client.reqContractDetails(t))
        
    

if __name__ == '__main__':
    unittest.main() 

