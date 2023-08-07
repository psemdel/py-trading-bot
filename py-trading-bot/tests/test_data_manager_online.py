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
import os
import numpy as np
from django.test import TestCase
from orders import models as m
from core.data_manager_online import retrieve_data_online
from trading_bot.settings import _settings

class TestDatamanagerOnline(TestCase):
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

    def test_retrieve_YF(self):
        _settings["USED_API"]["reporting"]="YF"
        symbols=retrieve_data_online(self,self.actions,"1y") 
               
        self.assertEqual(np.shape(self.close)[1],3)
        self.assertTrue(np.shape(self.close)[0]>200)
        self.assertTrue(np.shape(self.close_ind)[0]>200)
        self.assertEqual(np.shape(self.high)[1],3)
        self.assertTrue(np.shape(self.high)[0]>200)
        
    @unittest.skipIf("TRAVIS" in os.environ and os.environ["TRAVIS"] == "true", \
    reason="This test requires a running instance of IB running in parallel, which is impossible in Travis")
    def test_retrieve_ib(self):
        _settings["USED_API"]["reporting"]="IB"
        symbols=retrieve_data_online(self,self.actions,"1y") 
            
        self.assertEqual(np.shape(self.close)[1],3)
        self.assertTrue(np.shape(self.close)[0]>200)
        self.assertTrue(np.shape(self.close_ind)[0]>200)
        self.assertEqual(np.shape(self.high)[1],3)
        self.assertTrue(np.shape(self.high)[0]>200)


