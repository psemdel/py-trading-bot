#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 23 17:03:49 2022

@author: maxime
"""
import unittest
import core.indicators as ic
from core import strat
import math
import vectorbtpro as vbt

class TestIndicator(unittest.TestCase):
    @classmethod
    def setUpClass(self):   
        self.st=strat.Strat("CAC40","2007_2009","test")    
    
    def test_rel_dif(self):
        self.assertEqual(ic.rel_dif(float('nan'),1),0)
        self.assertEqual(ic.rel_dif(1,float('nan')),0)
        self.assertEqual(ic.rel_dif(1,1),0)
        self.assertEqual(ic.rel_dif(2,1),1)
        self.assertEqual(ic.rel_dif(1.1,1),0.1)
        self.assertEqual(ic.rel_dif(1.01,1),0.01)
        self.assertEqual(ic.rel_dif(2.2,2),0.1)
    
    def test_MACD(self):
        t=vbt.MACD.run(self.st.close, macd_wtype='simple',signal_wtype='simple')
        
        self.assertEqual(round(t.macd[t.macd.columns[0]].values[-1],2),1.08)
        self.assertEqual(round(t.macd[t.macd.columns[1]].values[-1],2),0.17)
        self.assertEqual(round(t.macd[t.macd.columns[2]].values[-1],2),-0.26)
        #self.assertEqual(round(t.macd[t.macd.columns[1]].values[-1],2),-0.36)
        
        self.assertEqual(round(t.hist[t.macd.columns[0]].values[-1],2),-0.28)
        self.assertEqual(round(t.hist[t.macd.columns[1]].values[-1],2),0.09)
        #self.assertEqual(round(t.hist[t.macd.columns[1]].values[-1],2),-0.14)
        self.assertEqual(round(t.hist[t.macd.columns[2]].values[-1],2),-0.11)
        
    def test_VBTSUPERTREND(self):
        t=ic.VBTSUPERTREND.run(self.st.high,self.st.low,self.st.close)
        self.assertTrue(math.isnan(t.supert['AC'].values[0]))
        self.assertTrue(t.supert['AC'].values[-1]>0)
        self.assertEqual(t.superd['AC'].values[0],1)
        self.assertEqual(t.superd['AC'].values[-1],1)       
        self.assertTrue(math.isnan(t.superl['AC'].values[0]))
        self.assertTrue(t.superl['AC'].values[-1]>0)
        self.assertTrue(math.isnan(t.supers['AC'].values[0]))
        self.assertTrue(math.isnan(t.supers['AC'].values[-1]))    

    def test_VBTSUPERTRENDMA(self):
        t=ic.VBTSUPERTRENDMA.run(self.st.high,self.st.low,self.st.close)
        self.assertFalse(t.entries['AIR'].values[0])
        self.assertTrue(t.entries['AIR'].values[-1])
        self.assertFalse(t.exits['AIR'].values[0])
        self.assertTrue(t.exits['AIR'].values[-1])      
        self.assertTrue(t.exits['AIR'].values[-2])   
        self.assertTrue(t.exits['AIR'].values[-3])   
        
        pf=vbt.Portfolio.from_signals(self.st.close, t.entries,t.exits)
        self.assertEqual(round(pf.get_total_return()['AC'],3),-0.221)
        self.assertEqual(round(pf.get_total_return()['BNP'],3),-0.271)
        
    def test_VBTNATR(self):
        t=ic.VBTNATR.run(self.st.high,self.st.low,self.st.close).natr
        self.assertTrue(math.isnan(t['AC'].values[0]))
        self.assertEqual(round(t['AC'].values[-1],2),4.25)
        self.assertEqual(round(t['VIV'].values[-1],2),3.84)

    def test_VBTMA(self):
        t=ic.VBTMA.run(self.st.high,self.st.low,self.st.close)
        self.assertTrue(t.entries['BN'].values[18])
        self.assertTrue(t.entries['BNP'].values[20])
        self.assertFalse(t.exits['SAN'].values[-2])      
        self.assertTrue(t.exits['SAN'].values[-1])  
        self.assertTrue(t.exits['SU'].values[-3])

        pf=vbt.Portfolio.from_signals(self.st.close, t.entries,t.exits)
        self.assertEqual(round(pf.get_total_return()['AC'],3),-0.258)
        self.assertEqual(round(pf.get_total_return()['BNP'],3),-0.494)

    def test_VBTSTOCHKAMA(self):
        t=ic.VBTSTOCHKAMA.run(self.st.high,self.st.low,self.st.close)
        
        self.assertTrue(t.entries['AIR'].values[-1])
        self.assertTrue(t.entries_kama['AIR'].values[-1])
        self.assertFalse(t.entries_stoch['AIR'].values[-1])
        self.assertEqual(t.direction['AIR'].values[-2],1)
        self.assertEqual(t.direction['AIR'].values[-1],-1)
        
        self.assertTrue(t.entries['SAN'].values[-2])
        self.assertTrue(t.entries_kama['SAN'].values[-2])
        self.assertFalse(t.entries_stoch['SAN'].values[-2]) 
        self.assertEqual(t.direction['SAN'].values[-3],1)
        self.assertEqual(t.direction['SAN'].values[-2],-1)        

        self.assertTrue(t.entries['AIR'].values[49])
        self.assertFalse(t.entries_kama['AIR'].values[49])
        self.assertTrue(t.entries_stoch['AIR'].values[49])
        
        self.assertTrue(t.stoch['AIR'].values[48]>20)
        self.assertTrue(t.stoch['AIR'].values[49]<20)
        
        self.assertTrue(t.exits['SAN'].values[-1])
        self.assertTrue(t.exits_kama['SAN'].values[-1])
        self.assertFalse(t.exits_stoch['SAN'].values[-1])
        self.assertEqual(t.direction['SAN'].values[-2],-1)
        self.assertEqual(t.direction['SAN'].values[-1],1)           
        
        self.assertTrue(t.exits['CAP'].values[-3])
        self.assertFalse(t.exits_kama['CAP'].values[-3])
        self.assertTrue(t.exits_stoch['CAP'].values[-3])      
        
        self.assertTrue(t.stoch['CAP'].values[-4]>80)
        self.assertTrue(t.stoch['CAP'].values[-3]<80)   
        
        pf=vbt.Portfolio.from_signals(self.st.close, t.entries_kama,t.exits_kama)
        self.assertEqual(round(pf.get_total_return()['AC'],3),-0.230)
        self.assertEqual(round(pf.get_total_return()['BNP'],3),-0.301)
        
        pf=vbt.Portfolio.from_signals(self.st.close, t.entries_stoch,t.exits_stoch)
        self.assertEqual(round(pf.get_total_return()['AC'],3),0.075)
        self.assertEqual(round(pf.get_total_return()['BNP'],3),-0.466)      

        pf=vbt.Portfolio.from_signals(self.st.close, t.entries,t.exits)
        self.assertEqual(round(pf.get_total_return()['AC'],3),-0.093)
        self.assertEqual(round(pf.get_total_return()['BNP'],3),-0.174)

    def test_VBTKAMA(self):
        t=ic.VBTKAMA.run(self.st.close)
        
        self.assertFalse(t.bot_ext['AIR'].values[-2])
        self.assertTrue(t.bot_ext['AIR'].values[-1])
        
        self.assertTrue(t.bot_ext['SAN'].values[-2])
        self.assertTrue(t.top_ext['SAN'].values[-1])
        
        self.assertEqual(t.direction['AIR'].values[-2],1)
        self.assertEqual(t.direction['AIR'].values[-1],-1)
        self.assertEqual(t.direction['SAN'].values[-3],1)
        self.assertEqual(t.direction['SAN'].values[-2],-1)    
        self.assertEqual(t.direction['SAN'].values[-2],-1)
        self.assertEqual(t.direction['SAN'].values[-1],1)   
        
        self.assertTrue(math.isnan(t.kama['AC'].values[0]))
        
        self.assertEqual(round(t.kama['AC'].values[-1],2),16.84)
        self.assertEqual(round(t.kama['AC'].values[-2],2),16.68)
        self.assertEqual(round(t.kama['AC'].values[-3],2),16.55)
        self.assertEqual(round(t.kama['BN'].values[-1],2),27.42)
        self.assertEqual(round(t.kama['MC'].values[-1],2),36.11)
        self.assertEqual(round(t.kama['MC'].values[-2],2),36.11)
        self.assertEqual(round(t.kama['MC'].values[-3],2),36.13)
        
    def test_VBTVERYBEAR(self):
        t=ic.VBTVERYBEAR.run(self.st.close)
        self.assertFalse(t.entries['AC'].values[0])
        self.assertFalse(t.entries['AC'].values[-1])
        self.assertTrue(t.exits['AC'].values[0])
        self.assertTrue(t.exits['AC'].values[-1])

    def test_VBTVERYBULL(self):
        t=ic.VBTVERYBULL.run(self.st.close)
        self.assertTrue(t.entries['AC'].values[0])
        self.assertTrue(t.entries['AC'].values[-1])
        self.assertFalse(t.exits['AC'].values[0])
        self.assertFalse(t.exits['AC'].values[-1])

    def test_VBTKAMATREND(self):
        t=ic.VBTKAMATREND.run(self.st.close)

        #direction should be same as for KAMA
        self.assertEqual(t.trend['AIR'].values[-2],1)
        self.assertEqual(t.trend['AIR'].values[-1],-1)
        self.assertEqual(t.trend['SAN'].values[-3],1)
        self.assertEqual(t.trend['SAN'].values[-2],-1)    
        self.assertEqual(t.trend['SAN'].values[-2],-1)
        self.assertEqual(t.trend['SAN'].values[-1],1)   

        self.assertEqual(t.duration['AC'].values[-1],-15)
        self.assertEqual(t.duration['AI'].values[-1],34)
        self.assertEqual(t.duration['ENGI'].values[-1],-4)
        self.assertEqual(t.duration['OR'].values[-1],23)    
        self.assertEqual(t.duration['ORA'].values[-1],-25)
        self.assertEqual(t.duration['SAN'].values[-1],0) 
  
    def test_VBTPATTERN(self):   
        t=ic.VBTPATTERN.run(self.st.open,self.st.high,self.st.low,self.st.close,light=False)

        self.assertTrue(t.entries[(False,'AC')].values[-2])
        self.assertTrue(t.entries[(False,'BNP')].values[-2])
        self.assertTrue(t.entries[(False,'CAP')].values[-2])
        
        self.assertTrue(t.exits[(False,'AI')].values[-1])
        self.assertTrue(t.exits[(False,'BN')].values[-1])
        self.assertTrue(t.exits[(False,'SAN')].values[-1])  
        self.assertTrue(t.exits[(False,'RI')].values[-3])  
        
        t=ic.VBTPATTERN.run(self.st.open,self.st.high,self.st.low,self.st.close,light=True)
        
        self.assertTrue(t.entries[(True,'BNP')].values[-2])
        self.assertTrue(t.entries[(True,'BN')].values[-4])
        #exit should be identical to not light
        self.assertFalse(t.exits[(True,'AI')].values[-1])
        self.assertFalse(t.exits[(True,'BN')].values[-1])
        self.assertFalse(t.exits[(True,'SAN')].values[-1]) 

        self.assertTrue(t.exits[(True,'SAN')].values[-11])  
        self.assertTrue(t.exits[(True,'RI')].values[-3])
      
    def test_VBTBBANDSTREND(self):          
        t=ic.VBTBBANDSTREND.run(self.st.close)
        
        #kama should be same as with kama
        self.assertEqual(round(t.kama['AC'].values[-1],2),16.84)
        self.assertEqual(round(t.kama['AC'].values[-2],2),16.68)
        self.assertEqual(round(t.kama['AC'].values[-3],2),16.55)
        self.assertEqual(round(t.kama['BN'].values[-1],2),27.42)
        self.assertEqual(round(t.kama['MC'].values[-1],2),36.11)
        self.assertEqual(round(t.kama['MC'].values[-2],2),36.11)
        self.assertEqual(round(t.kama['MC'].values[-3],2),36.13)
    
        self.assertEqual(t.trend['AC'].values[-1],-10)
        self.assertEqual(t.trend['AI'].values[-1],0)
        self.assertEqual(t.trend['AIR'].values[-1],-10)
        self.assertEqual(t.trend['ATO'].values[-1],10)
        self.assertEqual(t.trend['BN'].values[-1],0)
        
        self.assertEqual(round(t.bb_bw['AC'].values[-1],2),0.22)
        self.assertEqual(round(t.bb_bw['AI'].values[-1],2),0.09)
        self.assertEqual(round(t.bb_bw['AIR'].values[-1],2),0.13)
        self.assertEqual(round(t.bb_bw['SLB'].values[-1],2),0.27)

    def test_VBTMACDBBTREND(self):
        t=ic.VBTMACDBBTREND.run(self.st.close)
        
        self.assertEqual(round(t.kama['AC'].values[-1],2),16.84)
        self.assertEqual(round(t.kama['AC'].values[-2],2),16.68)
        self.assertEqual(round(t.kama['AC'].values[-3],2),16.55)
        self.assertEqual(round(t.kama['BN'].values[-1],2),27.42)
        self.assertEqual(round(t.kama['MC'].values[-1],2),36.11)
        self.assertEqual(round(t.kama['MC'].values[-2],2),36.11)
        self.assertEqual(round(t.kama['MC'].values[-3],2),36.13)
        
        self.assertEqual(round(t.bb_bw['AC'].values[-1],2),0.22)
        self.assertEqual(round(t.bb_bw['AI'].values[-1],2),0.09)
        self.assertEqual(round(t.bb_bw['AIR'].values[-1],2),0.13)
        self.assertEqual(round(t.bb_bw['SLB'].values[-1],2),0.27)
        self.assertEqual(round(t.bb_bw['MC'].values[-1],2),0.17)
        self.assertEqual(round(t.bb_bw['MC'].values[-2],2),0.17)
        self.assertEqual(round(t.bb_bw['MC'].values[-3],2),0.17)

        self.assertEqual(t.trend['AC'].values[-1],-1)
        self.assertEqual(t.trend['AI'].values[-1],-3)
        self.assertEqual(t.trend['AIR'].values[-1],3)
        self.assertEqual(t.trend['ATO'].values[-1],10)
        self.assertEqual(t.trend['BN'].values[-1],3)
        self.assertEqual(t.trend['MC'].values[-1],-1)
        self.assertEqual(t.trend['MC'].values[-2],-1)
        self.assertEqual(t.trend['MC'].values[-3],-1)
        self.assertEqual(t.trend['MC'].values[-4],-3)
        self.assertEqual(t.trend['MC'].values[-5],10)
        
    def test_VBTGROW(self):
        t=ic.VBTGROW.run(self.st.close,distance=50, ma=True)
        
        self.assertEqual(round(t.res[(50,True,'AC')].values[-1],2),-15.82)
        self.assertEqual(round(t.res[(50,True,'AI')].values[-1],2),-17.43)
        self.assertEqual(round(t.res[(50,True,'SAN')].values[-1],2),-3.30)

        t=ic.VBTGROW.run(self.st.close,distance=50, ma=False)
        self.assertEqual(round(t.res[(50,False,'AC')].values[-1],2),15.08)
        self.assertEqual(round(t.res[(50,False,'AI')].values[-1],2),-1.34)
        self.assertEqual(round(t.res[(50,False,'SAN')].values[-1],2),-2.37)
 
    def test_VBTDIVERGENCE(self):
        t=ic.VBTDIVERGENCE.run(self.st.close,self.st.close_ind)
        self.assertEqual(round(t.out['AC'].values[-1],3),0.007)
        self.assertEqual(round(t.out['AI'].values[-1],3),0.001)
        self.assertEqual(round(t.out['SLB'].values[-1],3),-0.007)
        
if __name__ == '__main__':
    unittest.main()
