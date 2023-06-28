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

class TestIB(TestCase):
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

    def test_retrieve_YF(self):
        api_used, symbols=ib.retrieve_data(self,self.actions,"1y",api_used="YF") 
               
        self.assertEqual(np.shape(self.close)[1],3)
        self.assertTrue(np.shape(self.close)[0]>200)
        self.assertTrue(np.shape(self.close_ind)[0]>200)
        self.assertEqual(np.shape(self.high)[1],3)
        self.assertTrue(np.shape(self.high)[0]>200)
        
    @unittest.skipIf("TRAVIS" in os.environ and os.environ["TRAVIS"] == "true", \
    reason="This test requires a running instance of IB running in parallel, which is impossible in Travis")
    def test_retrieve_ib(self):
        api_used, symbols=ib.retrieve_data(self,self.actions,"1y",api_used="IB") 
            
        self.assertEqual(np.shape(self.close)[1],3)
        self.assertTrue(np.shape(self.close)[0]>200)
        self.assertTrue(np.shape(self.close_ind)[0]>200)
        self.assertEqual(np.shape(self.high)[1],3)
        self.assertTrue(np.shape(self.high)[0]>200)
     
    def test_get_ratio(self):
        t=ib.get_ratio(self.a)
        self.assertTrue(t!=0)
        
    def test_get_last_price(self):
        ib.get_last_price(self.a4)       
        
    def test_cash_balance(self):
        self.assertTrue(ib.cash_balance()>=0)   
        self.assertTrue(ib.cash_balance(currency="USD")>=0)   

    def test_check_enough_cash(self):
        self.assertTrue(ib.check_enough_cash(10000,currency="USD"))        

    def test_entry_order_manual(self):
        pf=m.PF.objects.create(short=False,strategy=self.strategy,stock_ex=self.e,sector=self.s)
        ocap=m.OrderCapital.objects.create(capital=1,strategy=self.strategy,stock_ex=self.e,sector=self.s)
        
        t=ib.entry_order_sub("AIR.PA","none","Paris",False,False)

        self.assertTrue(t)
        self.assertEqual(len(pf.retrieve()),1)
        
        ocap=m.get_order_capital("none","Paris")
        self.assertEqual(ocap.capital,0)
        
        t=ib.entry_order_sub("AIR.PA","none","Paris",False,False)
        self.assertFalse(t)
        
    def test_exit_order_manual(self):        
        pf=m.PF.objects.create(short=False,strategy=self.strategy,stock_ex=self.e,sector=self.s)
        ocap=m.OrderCapital.objects.create(capital=1,strategy=self.strategy,stock_ex=self.e,sector=self.s)
                
        ib.entry_order_sub("AIR.PA","none","Paris",False,False)   
        t=ib.exit_order_sub("AIR.PA","none","Paris",False,False)   
        self.assertTrue(t)
        self.assertEqual(len(pf.retrieve()),0)
        ocap=m.get_order_capital("none","Paris")
        self.assertEqual(ocap.capital,1)
        
        order=m.Order.objects.get(action=self.a3)
        self.assertFalse(order.active)
        self.assertTrue(order.exiting_date is not None)
        
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
        
    def test_check_hold_duration(self):
        st_retard=m.Strategy.objects.create(name="retard")
        pf=m.PF.objects.create(short=False,strategy=st_retard,stock_ex=self.e,sector=self.s)
        pf.append(self.a.symbol)
        d=datetime.now()
        o=m.Order.objects.create(action=self.a, pf=pf, short=False,entering_date=d) 
        
        self.assertEqual(ib.check_hold_duration(self.a.symbol,st_retard.name, self.e.name,False,sector=self.s),0)

        d2=d- timedelta(days=10)
        o2=m.Order.objects.create(action=self.a2, pf=pf, short=False) 
        o2.entering_date=d2
        o2.save()
        pf.append(self.a2.symbol)
        self.assertEqual(ib.check_hold_duration(self.a2.symbol,st_retard.name, self.e.name,False,sector=self.s),10)         
        
     #   check_hold_duration
    #def test_retrieve_quantity(self):
    #    retrieve_quantity()

if __name__ == '__main__':
    unittest.main() 
####!!!Those functions will cause real orders to be performed, as the _settings["PERFORM_ORDER"] is entry_order but not in entry_order_sub!!
#Use it only outside of trade time!
'''
    def test_entry_order_auto(self):
        pf=m.PF.objects.create(name="none_Paris",short=False,strategy=self.strategy,stock_ex=self.e,sector=self.s)
        ocap=m.OrderCapital.objects.create(capital=1,name="none_Paris",strategy=self.strategy,stock_ex=self.e,sector=self.s)
        
        t=ib.entry_order_sub("AIR.PA","none","Paris",False,True)

        self.assertTrue(t)
        self.assertEqual(len(pf.retrieve()),1)
        
        ocap=m.get_order_capital("none","Paris")
        self.assertEqual(ocap.capital,0)

        order=m.Order.objects.get(action=self.a3) #it is a test.
        
        t=ib.entry_order_sub("AIR.PA","none","Paris",False,True)
        self.assertFalse(t)
        
    def test_exit_order_auto(self):        
        pf=m.PF.objects.create(name="none_Paris",short=False,strategy=self.strategy,stock_ex=self.e,sector=self.s)
        ocap=m.OrderCapital.objects.create(capital=1,name="none_Paris",strategy=self.strategy,stock_ex=self.e,sector=self.s)
                
        t=ib.entry_order_sub(self.a.symbol,"none","Paris",False,True)   
        self.assertTrue(t)
        t=ib.exit_order_sub(self.a.symbol,"none","Paris",False,True)   
        self.assertTrue(t)
        self.assertEqual(len(pf.retrieve()),0)
        ocap=m.get_order_capital("none","Paris")
        self.assertEqual(ocap.capital,1)
        
        order=m.Order.objects.get(action=self.a)
        self.assertFalse(order.active)
        self.assertTrue(order.exiting_date is not None)
'''
        

