#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 23 17:03:49 2022

@author: maxime
"""
from django.test import TestCase
import core.indicators as ic
from core import strat
import math
import vectorbtpro as vbt

class TestIndicator(TestCase):
    @classmethod
    def setUpClass(self):  
        super().setUpClass()
        self.ust=strat.StratDiv2("2007_2023_08", symbol_index="CAC40")
        self.ust.run()

    def test_rel_dif(self):
        self.assertEqual(ic.rel_dif(float('nan'),1),0)
        self.assertEqual(ic.rel_dif(1,float('nan')),0)
        self.assertEqual(ic.rel_dif(1,1),0)
        self.assertEqual(ic.rel_dif(2,1),1)
        self.assertEqual(ic.rel_dif(1.1,1),0.1)
        self.assertEqual(ic.rel_dif(1.01,1),0.01)
        self.assertEqual(ic.rel_dif(2.2,2),0.1)
    
    def test_MACD(self):
        t=vbt.MACD.run(self.ust.close, macd_wtype='simple',signal_wtype='simple')
        
        self.assertEqual(round(t.macd[t.macd.columns[0]].values[-1],2),0.13)
        self.assertEqual(round(t.macd[t.macd.columns[1]].values[-1],2),0.38)
        self.assertEqual(round(t.macd[t.macd.columns[2]].values[-1],2),1.26)
        #self.assertEqual(round(t.macd[t.macd.columns[1]].values[-1],2),-0.36)
        
        self.assertEqual(round(t.hist[t.macd.columns[0]].values[-1],2),-0.09)
        self.assertEqual(round(t.hist[t.macd.columns[1]].values[-1],2),1.22)
        #self.assertEqual(round(t.hist[t.macd.columns[1]].values[-1],2),-0.14)
        self.assertEqual(round(t.hist[t.macd.columns[2]].values[-1],2),-0.37)
        
    def test_VBTSUPERTREND(self):
        t=ic.VBTSUPERTREND.run(self.ust.high,self.ust.low,self.ust.close)
        self.assertTrue(math.isnan(t.supert['AC.PA'].values[0]))
        self.assertTrue(t.supert['AC.PA'].values[-1]>0)
        self.assertEqual(t.superd['AC.PA'].values[0],1)
        self.assertEqual(t.superd['AC.PA'].values[-1],1)       
        self.assertTrue(math.isnan(t.superl['AC.PA'].values[0]))
        self.assertTrue(t.superl['AC.PA'].values[-1]>0)
        self.assertTrue(math.isnan(t.supers['AC.PA'].values[0]))
        self.assertTrue(math.isnan(t.supers['AC.PA'].values[-1]))    

    def test_VBTSUPERTRENDMA(self):
        t=ic.VBTSUPERTRENDMA.run(self.ust.high,self.ust.low,self.ust.close)
        
        self.assertFalse(t.entries['AIR.PA'].values[0])
        self.assertFalse(t.entries['AIR.PA'].values[-1])
        
        self.assertFalse(t.exits['AIR.PA'].values[0])
        self.assertFalse(t.exits['AIR.PA'].values[-1])     
        self.assertTrue(t.exits['AIR.PA'].values[-2])   
        self.assertFalse(t.exits['AIR.PA'].values[-3])   
        
        pf=vbt.Portfolio.from_signals(self.ust.close, t.entries,t.exits)
        self.assertEqual(round(pf.get_total_return()['AC.PA'],3),-0.448)
        self.assertEqual(round(pf.get_total_return()['BNP.PA'],3),0.02)

    def test_VBTMA(self):
        t=ic.VBTMA.run(self.ust.high,self.ust.low,self.ust.close)
        self.assertTrue(t.entries['BN.PA'].values[18])
        self.assertTrue(t.entries['BNP.PA'].values[20])
        self.assertFalse(t.exits['SAN.PA'].values[-2])     
        self.assertFalse(t.exits['SAN.PA'].values[-1])  
        self.assertFalse(t.exits['SU.PA'].values[-3])

        pf=vbt.Portfolio.from_signals(self.ust.close, t.entries,t.exits)
        self.assertEqual(round(pf.get_total_return()['AC.PA'],3),-0.187)
        self.assertEqual(round(pf.get_total_return()['BNP.PA'],3),-0.608)

    def test_VBTSTOCHKAMA(self):
        t=ic.VBTSTOCHKAMA.run(self.ust.high,self.ust.low,self.ust.close)

        self.assertFalse(t.entries['AIR.PA'].values[-1])
        self.assertFalse(t.entries_kama['AIR.PA'].values[-1])
        self.assertFalse(t.entries_stoch['AIR.PA'].values[-1])
        self.assertEqual(t.direction['AIR.PA'].values[-2],-1)
        self.assertEqual(t.direction['AIR.PA'].values[-1],-1)
        
        self.assertFalse(t.entries['SAN.PA'].values[-2])
        self.assertTrue(t.entries_kama['SAN.PA'].values[-1])
        self.assertFalse(t.entries_kama['SAN.PA'].values[-2])
        self.assertTrue(t.entries_kama['SAN.PA'].values[-3])
        self.assertFalse(t.entries_stoch['SAN.PA'].values[-2]) 
        self.assertEqual(t.direction['SAN.PA'].values[-3],-1)
        self.assertEqual(t.direction['SAN.PA'].values[-2],1)        

        self.assertTrue(t.entries['AIR.PA'].values[49])
        self.assertFalse(t.entries_kama['AIR.PA'].values[49])
        self.assertTrue(t.entries_stoch['AIR.PA'].values[49])
        
        self.assertTrue(t.stoch['AIR.PA'].values[48]>20)
        self.assertTrue(t.stoch['AIR.PA'].values[49]<20)
        
        self.assertFalse(t.exits['SAN.PA'].values[-1])
        self.assertFalse(t.exits_kama['SAN.PA'].values[-1])
        self.assertFalse(t.exits_stoch['SAN.PA'].values[-1])
        self.assertEqual(t.direction['SAN.PA'].values[-2],1)
        self.assertEqual(t.direction['SAN.PA'].values[-1],-1)           
        
        self.assertFalse(t.exits['CAP.PA'].values[-3])
        self.assertFalse(t.exits_kama['CAP.PA'].values[-3])
        self.assertFalse(t.exits_stoch['CAP.PA'].values[-3])      
        
        self.assertFalse(t.stoch['CAP.PA'].values[-4]>80)
        self.assertTrue(t.stoch['CAP.PA'].values[-3]<80)   
        
        pf=vbt.Portfolio.from_signals(self.ust.close, t.entries_kama,t.exits_kama)
        self.assertEqual(round(pf.get_total_return()['AC.PA'],3),-0.458)
        self.assertEqual(round(pf.get_total_return()['BNP.PA'],3),0.42)
        
        pf=vbt.Portfolio.from_signals(self.ust.close, t.entries_stoch,t.exits_stoch)
        self.assertEqual(round(pf.get_total_return()['AC.PA'],3),1.941)
        self.assertEqual(round(pf.get_total_return()['BNP.PA'],3),4.534)      

        pf=vbt.Portfolio.from_signals(self.ust.close, t.entries,t.exits)
        self.assertEqual(round(pf.get_total_return()['AC.PA'],3),1.95)
        self.assertEqual(round(pf.get_total_return()['BNP.PA'],3),7.065)

    def test_VBTKAMA(self):
        t=ic.VBTKAMA.run(self.ust.close)

        self.assertFalse(t.bot_ext['AIR.PA'].values[-2])
        self.assertFalse(t.bot_ext['AIR.PA'].values[-1])
        
        self.assertFalse(t.bot_ext['SAN.PA'].values[-2])
        self.assertTrue(t.bot_ext['SAN.PA'].values[-1])
        self.assertTrue(t.bot_ext['SAN.PA'].values[-3])
        self.assertFalse(t.top_ext['SAN.PA'].values[-1])
        
        self.assertEqual(t.direction['AIR.PA'].values[-2],-1)
        self.assertEqual(t.direction['AIR.PA'].values[-1],-1)
        self.assertEqual(t.direction['SAN.PA'].values[-3],-1)
        self.assertEqual(t.direction['SAN.PA'].values[-2],1)    
        self.assertEqual(t.direction['SAN.PA'].values[-2],1)
        self.assertEqual(t.direction['SAN.PA'].values[-1],-1)   
        
        self.assertTrue(math.isnan(t.kama['AC.PA'].values[0]))
        
        self.assertEqual(round(t.kama['AC.PA'].values[-1],2),33.11)
        self.assertEqual(round(t.kama['AC.PA'].values[-2],2),33.06)
        self.assertEqual(round(t.kama['AC.PA'].values[-3],2),33.03)
        self.assertEqual(round(t.kama['BN.PA'].values[-1],2),56.06)
        self.assertEqual(round(t.kama['MC.PA'].values[-1],2),847.39)
        self.assertEqual(round(t.kama['MC.PA'].values[-2],2),847.39)
        self.assertEqual(round(t.kama['MC.PA'].values[-3],2),847.46)
        
    def test_VBTVERYBEAR(self):
        t=ic.VBTVERYBEAR.run(self.ust.close)
        self.assertFalse(t.entries['AC.PA'].values[0])
        self.assertFalse(t.entries['AC.PA'].values[-1])
        self.assertTrue(t.exits['AC.PA'].values[0])
        self.assertTrue(t.exits['AC.PA'].values[-1])

    def test_VBTVERYBULL(self):
        t=ic.VBTVERYBULL.run(self.ust.close)
        self.assertTrue(t.entries['AC.PA'].values[0])
        self.assertTrue(t.entries['AC.PA'].values[-1])
        self.assertFalse(t.exits['AC.PA'].values[0])
        self.assertFalse(t.exits['AC.PA'].values[-1])

    def test_VBTKAMATREND(self):
        t=ic.VBTKAMATREND.run(self.ust.close)

        #direction should be same as for KAMA
        self.assertEqual(t.trend['AIR.PA'].values[-2],-1)
        self.assertEqual(t.trend['AIR.PA'].values[-1],-1)
        self.assertEqual(t.trend['SAN.PA'].values[-3],-1)
        self.assertEqual(t.trend['SAN.PA'].values[-2],1)    
        self.assertEqual(t.trend['SAN.PA'].values[-1],-1)   

        self.assertEqual(t.duration['AC.PA'].values[-1],-41)
        self.assertEqual(t.duration['AI.PA'].values[-1],-2)
        self.assertEqual(t.duration['ENGI.PA'].values[-1],0)
        self.assertEqual(t.duration['OR.PA'].values[-1],-1)    
        self.assertEqual(t.duration['ORA.PA'].values[-1],3)
        self.assertEqual(t.duration['SAN.PA'].values[-1],0) 
  
    def test_VBTPATTERN(self):   
        t=ic.VBTPATTERN.run(self.ust.open,self.ust.high,self.ust.low,self.ust.close)
        self.assertFalse(t.entries['AC.PA'].values[-2])
        self.assertTrue(t.entries['AC.PA'].values[-1])
        self.assertFalse(t.entries['BNP.PA'].values[-2])
        self.assertFalse(t.entries['CAP.PA'].values[-2])
        
        self.assertFalse(t.exits['AI.PA'].values[-1])
        self.assertTrue(t.exits['BN.PA'].values[-1])
        self.assertFalse(t.exits['SAN.PA'].values[-1])  
        self.assertFalse(t.exits['RI.PA'].values[-3])  
      
    def test_VBTBBANDSTREND(self):          
        t=ic.VBTBBANDSTREND.run(self.ust.close)
        
        #kama should be same as with kama
        self.assertEqual(round(t.kama['AC.PA'].values[-1],2),33.11)
        self.assertEqual(round(t.kama['AC.PA'].values[-2],2),33.06)
        self.assertEqual(round(t.kama['AC.PA'].values[-3],2),33.03)
        self.assertEqual(round(t.kama['BN.PA'].values[-1],2),56.06)
        self.assertEqual(round(t.kama['MC.PA'].values[-1],2),847.39)
        self.assertEqual(round(t.kama['MC.PA'].values[-2],2),847.39)
        self.assertEqual(round(t.kama['MC.PA'].values[-3],2),847.46)
    
        self.assertEqual(t.trend['AC.PA'].values[-1],0)
        self.assertEqual(t.trend['AI.PA'].values[-1],0)
        self.assertEqual(t.trend['AIR.PA'].values[-1],0)
        self.assertEqual(t.trend['ATO.PA'].values[-1],10)
        self.assertEqual(t.trend['BN.PA'].values[-1],0)

        self.assertEqual(round(t.bb_bw['AC.PA'].values[-1],2),0.02)
        self.assertEqual(round(t.bb_bw['AI.PA'].values[-1],2),0.04)
        self.assertEqual(round(t.bb_bw['AIR.PA'].values[-1],2),0.03)
        self.assertEqual(round(t.bb_bw['SLB.PA'].values[-1],2),0.07)

    def test_VBTMACDBBTREND(self):
        t=ic.VBTMACDBBTREND.run(self.ust.close)
        
        self.assertEqual(round(t.kama['AC.PA'].values[-1],2),33.11)
        self.assertEqual(round(t.kama['AC.PA'].values[-2],2),33.06)
        self.assertEqual(round(t.kama['AC.PA'].values[-3],2),33.03)
        self.assertEqual(round(t.kama['BN.PA'].values[-1],2),56.06)
        self.assertEqual(round(t.kama['MC.PA'].values[-1],2),847.39)
        self.assertEqual(round(t.kama['MC.PA'].values[-2],2),847.39)
        self.assertEqual(round(t.kama['MC.PA'].values[-3],2),847.46)
        
        self.assertEqual(round(t.bb_bw['AC.PA'].values[-1],2),0.02)
        self.assertEqual(round(t.bb_bw['AI.PA'].values[-1],2),0.04)
        self.assertEqual(round(t.bb_bw['AIR.PA'].values[-1],2),0.03)
        self.assertEqual(round(t.bb_bw['SLB.PA'].values[-1],2),0.07)
        self.assertEqual(round(t.bb_bw['MC.PA'].values[-1],2),0.09)
        self.assertEqual(round(t.bb_bw['MC.PA'].values[-2],2),0.09)
        self.assertEqual(round(t.bb_bw['MC.PA'].values[-3],2),0.09)

        self.assertEqual(t.trend['AC.PA'].values[-1],-2)
        self.assertEqual(t.trend['AI.PA'].values[-1],-1)
        self.assertEqual(t.trend['AIR.PA'].values[-1],-1)
        self.assertEqual(t.trend['ATO.PA'].values[-1],10)
        self.assertEqual(t.trend['BN.PA'].values[-1],-3)
        self.assertEqual(t.trend['MC.PA'].values[-1],-1)
        self.assertEqual(t.trend['MC.PA'].values[-2],-2)
        self.assertEqual(t.trend['MC.PA'].values[-3],-3)
        self.assertEqual(t.trend['MC.PA'].values[-4],-3)
        self.assertEqual(t.trend['MC.PA'].values[-5],-3)
        
    def test_VBTGROW(self):
        t=ic.VBTGROW.run(self.ust.close,distance=50, ma=True)
        
        self.assertEqual(round(t.out[(50,True,'AC.PA')].values[-1],2),7.76)
        self.assertEqual(round(t.out[(50,True,'AI.PA')].values[-1],2),0.87)
        self.assertEqual(round(t.out[(50,True,'SAN.PA')].values[-1],2),-0.64)

        t=ic.VBTGROW.run(self.ust.close,distance=50, ma=False)
        self.assertEqual(round(t.out[(50,False,'AC.PA')].values[-1],2),6.61)
        self.assertEqual(round(t.out[(50,False,'AI.PA')].values[-1],2),0.27)
        self.assertEqual(round(t.out[(50,False,'SAN.PA')].values[-1],2),-0.89)
 
    def test_VBTDIVERGENCE(self):
        t=ic.VBTDIVERGENCE.run(self.ust.close,self.ust.close_ind)
        self.assertEqual(round(t.out['AC.PA'].values[-1],3),-0.002)
        self.assertEqual(round(t.out['AI.PA'].values[-1],3),-0.000)
        self.assertEqual(round(t.out['SLB.PA'].values[-1],3),0.003)
        
    def test_VBTMINMAX(self):
        t=ic.VBTMINMAX.run(self.ust.close,distance=10)
        self.assertTrue(t.maximum[t.maximum.columns[0]].values[0]>t.minimum[t.minimum.columns[0]].values[0])
        self.assertTrue(t.maximum[t.maximum.columns[0]].values[1]>t.minimum[t.minimum.columns[0]].values[1])
        self.assertTrue(t.maximum[t.maximum.columns[0]].values[2]>t.minimum[t.minimum.columns[0]].values[2])
        self.assertTrue(t.maximum[t.maximum.columns[0]].values[-10]>t.minimum[t.minimum.columns[0]].values[-10])
        
        self.assertEqual(round(t.minimum[t.minimum.columns[0]].values[0],2),-0.59)
        self.assertEqual(round(t.minimum[t.minimum.columns[0]].values[1],2),0.0)
        self.assertEqual(round(t.minimum[t.minimum.columns[0]].values[2],2),-0.17)
        self.assertEqual(round(t.minimum[t.minimum.columns[0]].values[3],2),-0.17)
        
        self.assertEqual(round(t.maximum[t.maximum.columns[0]].values[0],2),6.4)
        self.assertEqual(round(t.maximum[t.maximum.columns[0]].values[1],2),7.03)
        self.assertEqual(round(t.maximum[t.maximum.columns[0]].values[2],2),6.85)
        self.assertEqual(round(t.maximum[t.maximum.columns[0]].values[3],2),7.35)           
