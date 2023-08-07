#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 24 19:45:34 2022

@author: maxime
"""

from django.test import TestCase
from core import presel
import vectorbtpro as vbt
from orders import models as m
from core import strat
from datetime import datetime

import sys
if sys.version_info.minor>=9:
    from zoneinfo import ZoneInfo
else:
    from backports.zoneinfo import ZoneInfo
    
class TestBT(TestCase):
    def setUp(self):
        self.period="2007_2022_08"
        self.symbol_index="CAC40"
        
        f=m.Fees.objects.create(name="zero",fixed=0,percent=0)
        cat=m.ActionCategory.objects.create(name="actions",short="ACT")
        
        self.e=m.StockEx.objects.create(name="Paris",fees=f,ib_ticker="SBF",main_index=None,ib_auth=True)
        c=m.Currency.objects.create(name="euro")
        
        self.strategy=m.Strategy.objects.create(name="none",priority=10,target_order_size=1)
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
        
    def test_name_to_ust_or_presel(self):
        pr=presel.name_to_ust_or_presel("PreselWQ7",self.period,symbol_index=self.symbol_index)
        self.assertEqual( type(pr),presel.PreselWQ)
        pr=presel.name_to_ust_or_presel("PreselWQ7",self.period,symbol_index=self.symbol_index,it_is_index=True)
        self.assertEqual( pr,None)
        pr=presel.name_to_ust_or_presel("PreselDivergence",self.period,symbol_index=self.symbol_index)
        self.assertEqual( type(pr),presel.PreselDivergence)
        pr=presel.name_to_ust_or_presel("PreselDivergence",self.period,symbol_index=self.symbol_index,it_is_index=True)
        self.assertEqual( pr,None)        
        pr=presel.name_to_ust_or_presel("abcd",self.period,symbol_index=self.symbol_index)
        self.assertEqual( pr,None)  
        pr=presel.name_to_ust_or_presel("StratG",self.period,symbol_index=self.symbol_index)
        self.assertEqual( type(pr),strat.StratG)  
        pr=presel.name_to_ust_or_presel("StratG",self.period,symbol_index=self.symbol_index,it_is_index=True) #gives some warnings
        self.assertEqual( type(pr),strat.StratG)
        
    def test_get_order(self):
        self.bti=presel.Presel(self.period,symbol_index=self.symbol_index)
        self.assertEqual(self.bti.get_order("AC.PA","none"),None)
        
        o=m.Order.objects.create(action=self.a, strategy=self.strategy)
        self.assertEqual( self.bti.get_order("AC.PA","none"),o)

    def test_get_last_exit(self):
        self.ust=strat.StratDiv(self.period, symbol_index=self.symbol_index)
        self.ust.run()
        
        self.bti=presel.Presel(self.period,symbol_index=self.symbol_index,input_ust=self.ust)
        #ust has an exit for AC in 2022-08-19, no exit short
        d=datetime(2022,8,20,tzinfo=ZoneInfo('Europe/Paris'))
        #since 2022-08-20, no exit
        self.assertEqual(self.bti.get_last_exit(d,"AC","AC"),1)
        self.assertEqual(self.bti.get_last_exit(d,"AC","AC",short=True),-1)
        
        d=datetime(2022,8,18,tzinfo=ZoneInfo('Europe/Paris'))
        #since 2022-08-20, there was an exit
        self.assertEqual(self.bti.get_last_exit(d,"AC","AC"),0)
        self.assertEqual(self.bti.get_last_exit(d,"AC","AC",short=True),-1)
        
        d=datetime(2022,8,19,tzinfo=ZoneInfo('Europe/Paris'))
        #since 2022-08-19, limit case, we should not exit the day we enter
        self.assertEqual(self.bti.get_last_exit(d,"AC","AC"),1)
        self.assertEqual(self.bti.get_last_exit(d,"AC","AC",short=True),-1)
        
    def test_preselect_vol(self):
        self.bti=presel.PreselVol(self.period,symbol_index=self.symbol_index)
        self.bti.run()

        pf=vbt.Portfolio.from_signals(self.bti.close,
                                      self.bti.entries,
                                      self.bti.exits,
                                      short_entries=self.bti.entries_short,
                                      short_exits  =self.bti.exits_short,
                                      freq="1d",
                                      call_seq='auto',
                                      cash_sharing=True,
                             )

        self.assertEqual(round(pf.get_total_return(),2),-0.21)
        
    def test_preselect_retard(self):
        self.bti=presel.PreselRetard(self.period,symbol_index=self.symbol_index)
        self.bti.run()

        pf=vbt.Portfolio.from_signals(self.bti.close,
                                      self.bti.entries,
                                      self.bti.exits,
                                      short_entries=self.bti.entries_short,
                                      short_exits  =self.bti.exits_short,
                                      freq="1d",
                                      call_seq='auto',
                                      cash_sharing=True,
                             )

        self.assertEqual(round(pf.get_total_return(),2),17.97) 

    def test_preselect_macd_vol(self):
        self.bti=presel.PreselMacdVol(self.period,symbol_index=self.symbol_index)
        self.bti.run()

        pf=vbt.Portfolio.from_signals(self.bti.close,
                                      self.bti.entries,
                                      self.bti.exits,
                                      short_entries=self.bti.entries_short,
                                      short_exits  =self.bti.exits_short,
                                      freq="1d",
                                      call_seq='auto',
                                      cash_sharing=True,
                             )

        self.assertEqual(round(pf.get_total_return(),2),1.78) 
        
    def test_preselect_hist_vol(self):
        self.bti=presel.PreselHistVol(self.period,symbol_index=self.symbol_index)
        self.bti.run()

        pf=vbt.Portfolio.from_signals(self.bti.close,
                                      self.bti.entries,
                                      self.bti.exits,
                                      short_entries=self.bti.entries_short,
                                      short_exits  =self.bti.exits_short,
                                      freq="1d",
                                      call_seq='auto',
                                      cash_sharing=True,
                             )

        self.assertEqual(round(pf.get_total_return(),2),2.74) 
        
    def test_preselect_divergence(self):
        self.bti=presel.PreselDivergence(self.period,symbol_index=self.symbol_index)
        self.bti.run()

        pf=vbt.Portfolio.from_signals(self.bti.close,
                                      self.bti.entries,
                                      self.bti.exits,
                                      short_entries=self.bti.entries_short,
                                      short_exits  =self.bti.exits_short,
                                      freq="1d",
                                      call_seq='auto',
                                      cash_sharing=True,
                             )

        self.assertEqual(round(pf.get_total_return(),2),17.73)  
        
    def test_preselect_macd_vol_macro(self):
        self.bti=presel.PreselMacdVolMacro(self.period,symbol_index=self.symbol_index)
        self.bti.run()

        pf=vbt.Portfolio.from_signals(self.bti.close,
                                      self.bti.entries,
                                      self.bti.exits,
                                      short_entries=self.bti.entries_short,
                                      short_exits  =self.bti.exits_short,
                                      freq="1d",
                                      call_seq='auto',
                                      cash_sharing=True,
                             )

        self.assertEqual(round(pf.get_total_return(),2),2.74 ) 
        
    def test_preselect_retard_macro(self):
        self.bti=presel.PreselRetardMacro(self.period,symbol_index=self.symbol_index)
        self.bti.run()

        pf=vbt.Portfolio.from_signals(self.bti.close,
                                      self.bti.entries,
                                      self.bti.exits,
                                      short_entries=self.bti.entries_short,
                                      short_exits  =self.bti.exits_short,
                                      freq="1d",
                                      call_seq='auto',
                                      cash_sharing=True,
                             )

        self.assertEqual(round(pf.get_total_return(),2),23.68) 

    def test_preselect_divergence_blocked(self):
        self.bti=presel.PreselDivergenceBlocked(self.period,symbol_index=self.symbol_index)
        self.bti.run()

        pf=vbt.Portfolio.from_signals(self.bti.close,
                                      self.bti.entries,
                                      self.bti.exits,
                                      short_entries=self.bti.entries_short,
                                      short_exits  =self.bti.exits_short,
                                      freq="1d",
                                      call_seq='auto',
                                      cash_sharing=True,
                             )

        self.assertEqual(round(pf.get_total_return(),2),5.11) 

    def test_preselect_divergence_blocked_im(self):
        self.bti=presel.PreselDivergenceBlockedIm(self.period,symbol_index=self.symbol_index)
        self.bti.run()

        pf=vbt.Portfolio.from_signals(self.bti.close,
                                      self.bti.entries,
                                      self.bti.exits,
                                      short_entries=self.bti.entries_short,
                                      short_exits  =self.bti.exits_short,
                                      freq="1d",
                                      call_seq='auto',
                                      cash_sharing=True,
                             )

        self.assertEqual(round(pf.get_total_return(),2),8.14) 
        
    def test_preselect_vol_slow(self):
        self.bti=presel.PreselVolSlow(self.period,symbol_index=self.symbol_index)
        self.bti.run()

        pf=vbt.Portfolio.from_signals(self.bti.close,
                                      self.bti.entries,
                                      self.bti.exits,
                                      short_entries=self.bti.entries_short,
                                      short_exits  =self.bti.exits_short,
                                      freq="1d",
                                      call_seq='auto',
                                      cash_sharing=True,
                             )

        self.assertEqual(round(pf.get_total_return(),2),10.1)   
        
    def test_preselect_realmadrid(self):
        self.bti=presel.PreselRealMadrid(self.period,symbol_index=self.symbol_index)
        self.bti.run()

        pf=vbt.Portfolio.from_signals(self.bti.close,
                                       self.bti.entries,
                                       self.bti.exits,
                                       short_entries=self.bti.entries_short,
                                       short_exits  =self.bti.exits_short,
                                       freq="1d",
                                       call_seq='auto',
                                       cash_sharing=True,
                              )

        self.assertEqual(round(pf.get_total_return(),2),9.08 )     

    def test_preselect_realmadrid_blocked(self):
        self.bti=presel.PreselRealMadridBlocked(self.period,symbol_index=self.symbol_index)
        self.bti.run()

        pf=vbt.Portfolio.from_signals(self.bti.close,
                                       self.bti.entries,
                                       self.bti.exits,
                                       short_entries=self.bti.entries_short,
                                       short_exits  =self.bti.exits_short,
                                       freq="1d",
                                       call_seq='auto',
                                       cash_sharing=True,
                              )

        self.assertEqual(round(pf.get_total_return(),2),6.0) 


    def test_preselect_macd_vol_slow(self):
        self.bti=presel.PreselMacdVolSlow(self.period,symbol_index=self.symbol_index)
        self.bti.run()

        pf=vbt.Portfolio.from_signals(self.bti.close,
                                       self.bti.entries,
                                       self.bti.exits,
                                       short_entries=self.bti.entries_short,
                                       short_exits  =self.bti.exits_short,
                                       freq="1d",
                                       call_seq='auto',
                                       cash_sharing=True,
                              )

        self.assertEqual(round(pf.get_total_return(),2),-0.61) 

    def test_preselect_hist_vol_slow(self):
        self.bti=presel.PreselHistVolSlow(self.period,symbol_index=self.symbol_index)
        self.bti.run()

        pf=vbt.Portfolio.from_signals(self.bti.close,
                                       self.bti.entries,
                                       self.bti.exits,
                                       short_entries=self.bti.entries_short,
                                       short_exits  =self.bti.exits_short,
                                       freq="1d",
                                       call_seq='auto',
                                       cash_sharing=True,
                              )

        self.assertEqual(round(pf.get_total_return(),2),2.81)  
