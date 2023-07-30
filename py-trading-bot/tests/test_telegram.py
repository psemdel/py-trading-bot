#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 28 21:22:48 2022

@author: maxime
"""

import unittest
import os
from django.test import TestCase
import reporting.telegram as tel
from reporting.models import Alert
from orders.models import Fees, StockEx, Action, ActionSector, ActionCategory, Strategy, Currency
import vectorbtpro as vbt
from reporting import telegram_sub
from datetime import time

class MockTelegramBot():
    def send_message_to_all(self,msg):
        pass

class TestTelegram(TestCase):
    def setUp(self):
        f=Fees.objects.create(name="zero",fixed=0,percent=0)
        
        e=StockEx.objects.create(name="Paris",fees=f,ib_ticker="SBF",main_index=None,ib_auth=True,
                                 timezone="Europe/Paris", 
                                 opening_time=time(9,0),
                                 closing_time=time(17,30)
                                 )
        self.e=e
        e2=StockEx.objects.create(name="XETRA",fees=f,ib_ticker="IBIS",main_index=None,ib_auth=True,
                                  timezone="Europe/Paris", 
                                  opening_time=time(9,0),
                                  closing_time=time(17,30)
                                  )
        c=Currency.objects.create(name="euro")
        cat=ActionCategory.objects.create(name="actions",short="ACT")
        cat2=ActionCategory.objects.create(name="actions",short="ETFLONG")
        cat3=ActionCategory.objects.create(name="actions",short="ETFSHORT")
        
        strategy=Strategy.objects.create(name="none")
        s=ActionSector.objects.create(name="sec")
        
        self.strategy=strategy
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

        bot=MockTelegramBot()
        self.sched=tel.MyScheduler(bot,test=True)
    
    #to be tested during opening hours, otherwise will fail
    def test_check_change(self):
        self.sched.check_change(1, self.a,False)
        self.assertEqual(len(Alert.objects.all()),0)       
        self.sched.check_change(10, self.a,False)
        self.assertEqual(len(Alert.objects.all()),0) 
        self.sched.check_change(-1, self.a,False)
        self.assertEqual(len(Alert.objects.all()),0) 
        self.sched.check_change(-4, self.a,False)
        self.assertEqual(len(Alert.objects.all()),1) 
        self.sched.check_change(1, self.a2,True)
        self.assertEqual(len(Alert.objects.all()),1)   
        self.sched.check_change(-1, self.a2,True)
        self.assertEqual(len(Alert.objects.all()),1) 
        self.sched.check_change(-4, self.a2,True)
        self.assertEqual(len(Alert.objects.all()),1) 
        self.sched.check_change(10, self.a,True)
        self.assertEqual(len(Alert.objects.all()),2) 
        
    def test_start_telegram(self):
        with open('trading_bot/etc/TELEGRAM_TOKEN') as f:
            TELEGRAM_TOKEN = f.read().strip()
        bot = telegram_sub.TelegramBot(token=TELEGRAM_TOKEN) #vbt.TelegramBot should work, don't hesitate to replace it
        bot.start(in_background=True)
        bot.stop()
        
    #to be tested during opening hours, otherwise will fail
    def test_check_stock_ex_open(self):
        self.assertTrue(self.sched.check_stock_ex_open(self.e))
        
    #to be tested during opening hours, otherwise will fail
    def test_check_stock_ex_open_from_action(self):
        self.assertTrue(self.sched.check_stock_ex_open_from_action(self.a))
    
    def test_check_pf(self):
        self.sched.check_pf(s_ex=self.e)
        self.sched.check_pf(s_ex=self.e,it_is_index=True)
        self.sched.check_pf(s_ex=self.e,opening=True)
        self.sched.check_pf(s_ex=self.e,it_is_index=True,opening=True)

    def test_check_cours(self):    
        self.sched.check_cours([self.a])
        self.sched.check_cours([self.a],both=True)
        self.sched.check_cours([self.a],opening=True)
        self.sched.check_cours([self.a],both=True,opening=True)
            
if __name__ == '__main__':
    unittest.main() 
