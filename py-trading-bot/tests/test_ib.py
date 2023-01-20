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

class TestIB(TestCase):
    def setUp(self):
        f=m.Fees.objects.create(name="zero",fixed=0,percent=0)
        
        self.e=m.StockEx.objects.create(name="Paris",fees=f,ib_ticker="SBF")
        self.e2=m.StockEx.objects.create(name="XETRA",fees=f,ib_ticker="IBIS")
        self.e3=m.StockEx.objects.create(name="MONEP",fees=f,ib_ticker="MONEP")
        c=m.Currency.objects.create(name="euro")
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

        m.Action.objects.create(
            symbol='^FCHI',
            #ib_ticker='AC',
            name='Cac40',
            stock_ex=self.e3,
            currency=c,
            category=cat2,
            etf_long=etf1,
            etf_short=etf1,
            sector=self.s
            ) 
        
        self.actions=[self.a, self.a2, self.a3]
        m.Excluded.objects.create(name="all",strategy=self.strategy)

    def test_retrieve_YF(self):
        cours_high, cours_low, cours_close, cours_open, cours_volume,  \
               cours_high_ind, cours_low_ind,  cours_close_ind, cours_open_ind,\
               cours_volume_ind, use_IB=ib.retrieve_data(self.actions,"1y",False) 
               
        self.assertEqual(np.shape(cours_close)[1],3)
        self.assertTrue(np.shape(cours_close)[0]>200)
        self.assertTrue(np.shape(cours_close_ind)[0]>200)
        self.assertEqual(np.shape(cours_high)[1],3)
        self.assertTrue(np.shape(cours_high)[0]>200)
        
    @unittest.skipIf("TRAVIS" in os.environ and os.environ["TRAVIS"] == "true", \
    reason="This test requires a running instance of IB running in parallel, which is impossible in Travis")
    def test_retrieve_ib(self):
        cours_high, cours_low, cours_close, cours_open, cours_volume,  \
               cours_high_ind, cours_low_ind,  cours_close_ind, cours_open_ind,\
               cours_volume_ind, use_IB=ib.retrieve_data(self.actions,"1y",True) 
            
        self.assertEqual(np.shape(cours_close)[1],3)
        self.assertTrue(np.shape(cours_close)[0]>200)
        self.assertTrue(np.shape(cours_close_ind)[0]>200)
        self.assertEqual(np.shape(cours_high)[1],3)
        self.assertTrue(np.shape(cours_high)[0]>200)
     
    def test_get_ratio(self):
        t=ib.get_ratio(self.a)
        self.assertTrue(t!=0)

    def test_entry_order_manual(self):
        pf=m.PF.objects.create(name="none_Paris",short=False,strategy=self.strategy,stock_ex=self.e,sector=self.s)
        ocap=m.OrderCapital.objects.create(capital=1,name="none_Paris",strategy=self.strategy,stock_ex=self.e,sector=self.s)
        
        t=ib.entry_order_sub("AIR.PA","none","Paris",False,False)

        self.assertTrue(t)
        self.assertEqual(len(pf.retrieve()),1)
        
        ocap=m.get_order_capital("none","Paris")
        self.assertEqual(ocap.capital,0)
        
        t=ib.entry_order_sub("AIR.PA","none","Paris",False,False)
        self.assertFalse(t)
        
    def test_exit_order_manual(self):        
        pf=m.PF.objects.create(name="none_Paris",short=False,strategy=self.strategy,stock_ex=self.e,sector=self.s)
        ocap=m.OrderCapital.objects.create(capital=1,name="none_Paris",strategy=self.strategy,stock_ex=self.e,sector=self.s)
                
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
        
if __name__ == '__main__':
    unittest.main() 
