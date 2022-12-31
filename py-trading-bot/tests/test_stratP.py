#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jun 26 21:39:46 2022

@author: maxime
"""


import unittest
from core import stratP
import vectorbtpro as vbt
import numpy as np
from django.test import TestCase
from orders.models import Action, ActionSector, StockEx, Currency, ActionCategory, Strategy, Fees

class TestStratP(TestCase):
    def setUp(self):
        f=Fees.objects.create(name="zero",fixed=0,percent=0)
        
        e=StockEx.objects.create(name="Paris",fees=f,ib_ticker="SBF")
        c=Currency.objects.create(name="euro")
        cat=ActionCategory.objects.create(name="actions")
        strategy=Strategy.objects.create(name="none")
        s=ActionSector.objects.create(name="sec")
        
        Action.objects.create(
            symbol='AC.PA',
            #ib_ticker='AC',
            name="Accor",
            stock_ex=e,
            currency=c,
            category=cat,
            #strategy=strategy,
            sector=s,
            )
        Action.objects.create(
            symbol='AI.PA',
            #ib_ticker='AC',
            name="Air liquide",
            stock_ex=e,
            currency=c,
            category=cat,
            #strategy=strategy,
            sector=s,
            )
        Action.objects.create(
            symbol='AIR.PA',
            #ib_ticker='AC',
            name="Airbus",
            stock_ex=e,
            currency=c,
            category=cat,
            #strategy=strategy,
            sector=s,
            )
        symbols=['AC.PA','AI.PA','AIR.PA'] 
        self.st=stratP.StratPRD(symbols,"1y")
        
    def test_stratPRD(self):
        st=self.st

        self.assertEqual(np.shape(st.close)[1],3)
        self.assertTrue(np.shape(st.close)[0]>200)
        self.assertTrue(np.shape(st.close_ind)[0]>200)
        self.assertEqual(np.shape(st.high)[1],3)
        self.assertTrue(np.shape(st.high)[0]>200)
        
    def test_grow_past(self):
        res=self.st.grow_past(50,False)
        self.assertEqual(res[(50,False,'AC.PA')].values[0],0)
        self.assertFalse(res[(50,False,'AC.PA')].values[-1]==0)
        self.assertEqual(res[(50,False,'AIR.PA')].values[0],0)
        self.assertFalse(res[(50,False,'AIR.PA')].values[-1]==0)
        res=self.st.grow_past(50,True)
        self.assertEqual(res[(50,True,'AC.PA')].values[0],0)
        self.assertFalse(res[(50,True,'AC.PA')].values[-1]==0)      
        self.assertEqual(res[(50,True,'AIR.PA')].values[0],0)
        self.assertFalse(res[(50,True,'AIR.PA')].values[-1]==0)        
        
    def test_call_strat(self):
        self.st.call_strat("strat_kama_stoch")
        
        pf=vbt.Portfolio.from_signals(self.st.close, self.st.entries,self.st.exits,
                                      short_entries=self.st.entries_short,
                                      short_exits  =self.st.exits_short)

        self.assertTrue(pf.get_total_return()[('VBTSTOCHKAMA',100,False,'long','AC.PA')]!=0)
        self.assertTrue(pf.get_total_return()[('VBTSTOCHKAMA',100,False,'long','AI.PA')]!=0)
        self.assertTrue(pf.get_total_return()[('VBTSTOCHKAMA',100,False,'long','AIR.PA')]!=0)

if __name__ == '__main__':
    unittest.main()           
