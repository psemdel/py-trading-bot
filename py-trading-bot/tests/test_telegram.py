#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 28 21:22:48 2022

@author: maxime
"""

import unittest
from django.test import TestCase
import reporting.telegram as tel
from reporting.models import Alert
from orders.models import Fees, StockEx, Action, ActionSector, ActionCategory, Strategy, Currency

class MockTelegramBot():
    def send_message_to_all(self,msg):
        pass

class TestTelegram(TestCase):
    def setUp(self):
        f=Fees.objects.create(name="zero",fixed=0,percent=0)
        
        e=StockEx.objects.create(name="Paris",fees=f,ib_ticker="SBF")
        self.e=e
        e2=StockEx.objects.create(name="XETRA",fees=f,ib_ticker="IBIS")
        c=Currency.objects.create(name="euro")
        cat=ActionCategory.objects.create(name="actions",short="ACT")
        strategy=Strategy.objects.create(name="none")
        s=ActionSector.objects.create(name="sec")
        
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

        bot=MockTelegramBot()
        self.sched=tel.MyScheduler(bot,test=True)
    
    #to be tested during opening hours
    def test_check_change(self):
        self.sched.check_change(1, "AC.PA",False)
        self.assertEqual(len(Alert.objects.all()),0)       
        self.sched.check_change(10, "AC.PA",False)
        self.assertEqual(len(Alert.objects.all()),0) 
        self.sched.check_change(-1, "AC.PA",False)
        self.assertEqual(len(Alert.objects.all()),0) 
        self.sched.check_change(-4, "AC.PA",False)
        self.assertEqual(len(Alert.objects.all()),1) 
        self.sched.check_change(1, "AI.PA",True)
        self.assertEqual(len(Alert.objects.all()),1)   
        self.sched.check_change(-1, "AI.PA",True)
        self.assertEqual(len(Alert.objects.all()),1) 
        self.sched.check_change(-4, "AI.PA",True)
        self.assertEqual(len(Alert.objects.all()),1) 
        self.sched.check_change(10, "AC.PA",True)
        self.assertEqual(len(Alert.objects.all()),2) 
 

if __name__ == '__main__':
    unittest.main() 
