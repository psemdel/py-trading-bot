#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jun 26 21:39:46 2022

@author: maxime
"""


from core import strat
import vectorbtpro as vbt
import numpy as np
from django.test import TestCase
from orders.models import Action, ActionSector, StockEx, Currency, ActionCategory, Strategy, Fees

class TestStratP(TestCase):
    def setUp(self):
        f=Fees.objects.create(name="zero",fixed=0,percent=0)
        
        e=StockEx.objects.create(name="Paris",fees=f,ib_ticker="SBF",main_index=None,ib_auth=True)
        e3=StockEx.objects.create(name="Nasdaq",fees=f,ib_ticker="SMART",main_index=None,ib_auth=True)
        e4=StockEx.objects.create(name="Monep",fees=f,ib_ticker="MONEP",main_index=None,ib_auth=True)
        c=Currency.objects.create(name="euro", symbol="EUR")
        cat=ActionCategory.objects.create(name="actions")
        strategy=Strategy.objects.create(name="none")
        s=ActionSector.objects.create(name="sec")
        
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
        
        cat2=ActionCategory.objects.create(name="index",short="IND")
        cat3=ActionCategory.objects.create(name="ETF",short="ETF")
        
        etf1=Action.objects.create(
            symbol='BNP.PA',
            #ib_ticker='AC',
            name="bbs",
            stock_ex=e,
            currency=c,
            category=cat3,
            #strategy=strategy,
            sector=s,
            ) 
        
        self.a5=Action.objects.create(
            symbol='^FCHI',
            ib_ticker_explicit='CAC40',
            name='Cac40',
            stock_ex=e4,
            currency=c,
            category=cat2,
            etf_long=etf1,
            etf_short=etf1,
            sector=s
            ) 
        
        e.main_index=self.a5
        e.save()
        
        self.actions=[self.a, self.a2, self.a3]
        self.st=strat.UnderlyingStrat("1y",prd=True, actions=self.actions)
        
    def test_stratPRD(self):
        st=self.st

        self.assertEqual(np.shape(st.close)[1],3)
        self.assertTrue(np.shape(st.close)[0]>200)
        self.assertTrue(np.shape(st.close_ind)[0]>200)
        self.assertEqual(np.shape(st.high)[1],3)
        self.assertTrue(np.shape(st.high)[0]>200)
        
    def test_grow_past(self):

        res=self.st.grow_past(50,False)
        self.assertEqual(res[(50,False,'AC')].values[0],0)
        self.assertFalse(res[(50,False,'AC')].values[-1]==0)
        self.assertEqual(res[(50,False,'AIR')].values[0],0)
        self.assertFalse(res[(50,False,'AIR')].values[-1]==0)
        res=self.st.grow_past(50,True)
        self.assertEqual(res[(50,True,'AC')].values[0],0)
        self.assertFalse(res[(50,True,'AC')].values[-1]==0)      
        self.assertEqual(res[(50,True,'AIR')].values[0],0)
        self.assertFalse(res[(50,True,'AIR')].values[-1]==0)        
        
    def test_call_strat(self):
        self.ust=getattr(strat, "StratKamaStochMatrendMacdbbMacro")("1y",prd=True, actions=self.actions)
        self.ust.run()
        
        pf=vbt.Portfolio.from_signals(self.ust.close, self.ust.entries,self.ust.exits,
                                      short_entries=self.ust.entries_short,
                                      short_exits  =self.ust.exits_short)

        self.assertTrue(pf.get_total_return()[pf.wrapper.columns[0]]!=0)
        self.assertTrue(pf.get_total_return()[pf.wrapper.columns[1]]!=0)
        self.assertTrue(pf.get_total_return()[pf.wrapper.columns[2]]!=0)
