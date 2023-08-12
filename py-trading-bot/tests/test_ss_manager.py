#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 12 21:59:42 2023

@author: maxime
"""
import numpy as np
from django.test import TestCase
from orders import ss_manager
from orders import models as m
import pandas as pd
import reporting.models as m2

class TestSSManager(TestCase):
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
        self.strategy=m.Strategy.objects.create(name="none",priority=10,target_order_size=1)
        self.strategy2=m.Strategy.objects.create(name="strat2",priority=20,target_order_size=1)
        self.strategy3=m.Strategy.objects.create(name="retard_keep",priority=30,target_order_size=1)
        
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
        
        etf1=m.Action.objects.create(
            symbol='BNP.PA',
            #ib_ticker='AC',
            name="bbs",
            stock_ex=self.e,
            currency=c,
            category=cat3,
            #strategy=strategy,
            )   
        
        etf2=m.Action.objects.create(
            symbol='KER.PA',
            #ib_ticker='AC',
            name="KER",
            stock_ex=self.e,
            currency=c,
            category=cat3,
            #strategy=strategy,
            )         
        
        self.a5=m.Action.objects.create(
            symbol='^FCHI',
            ib_ticker_explicit='CAC40',
            name='Cac40',
            stock_ex=self.e,
            currency=c,
            category=cat2,
            etf_long=etf1,
            etf_short=etf2,
            ) 
        self.a6=m.Action.objects.create(
            symbol='MC.PA',
            #ib_ticker='AC',
            name="LVMH",
            stock_ex=self.e,
            currency=c,
            category=cat,
            #strategy=strategy,
            sector=self.s,
            )
        
        ss1=m.StockStatus.objects.get(action=self.a)
        ss1.strategy=self.strategy
        ss1.save()
        
        ss2=m.StockStatus.objects.get(action=self.a2)
        ss2.strategy=self.strategy
        ss2.save()
        
        ss3=m.StockStatus.objects.get(action=self.a3)
        ss3.strategy=self.strategy2
        ss3.save()
        
        ss4=m.StockStatus.objects.get(action=self.a4)
        ss4.strategy=self.strategy2
        ss4.save()
        
        ss5=m.StockStatus.objects.get(action=self.a6)
        ss5.strategy=None
        ss5.save()
        
        self.r=m2.Report.objects.create()
        self.ss_m=ss_manager.StockStatusManager(self.r,"Paris")
            
    def test_init(self):
        self.assertEqual(len(m.StockStatus.objects.all()),8)    
        self.assertTrue(np.equal(self.ss_m.target_ss_by_st.columns,["category_id","none","retard_keep","strat2"]).all())
        self.assertTrue(np.equal(self.ss_m.present_ss.columns,["quantity","strategy_id","order_in_ib","etf_long_id","etf_short_id"]).all())
        self.assertEqual(self.ss_m.present_ss.loc["AC.PA","quantity"],0)
        self.assertEqual(self.ss_m.present_ss.loc["AC.PA","strategy_id"],self.strategy.id)
        self.assertTrue(self.ss_m.present_ss.loc["AC.PA","order_in_ib"])
        
        self.assertTrue(np.equal(self.ss_m.target_ss.columns,["quantity","strategy_id","order_in_ib","etf_long_id","etf_short_id","priority"]).all())
        self.assertEqual(self.ss_m.target_ss.loc["AC.PA","quantity"],0)
        self.assertEqual(self.ss_m.target_ss.loc["AC.PA","strategy_id"],self.strategy.id)
        self.assertTrue(self.ss_m.target_ss.loc["AC.PA","order_in_ib"])
        self.assertTrue(np.isnan(self.ss_m.target_ss.loc["AC.PA","priority"]))
        
        self.assertTrue(np.equal(self.ss_m.priority_st_lookup.columns,["name","priority"]).all())
        self.assertEqual(self.ss_m.priority_st_lookup.loc[self.strategy.id,"name"],"none")
        self.assertEqual(self.ss_m.priority_st_lookup.loc[self.strategy.id,"priority"],10)
        self.assertEqual(self.ss_m.priority_st_lookup.loc[self.strategy2.id,"name"],"strat2")
        self.assertEqual(self.ss_m.priority_st_lookup.loc[self.strategy2.id,"priority"],20)

    def test_determine_target_sub(self):
        df=pd.DataFrame(data=[["AC.PA",1,np.nan],["AIR.PA",np.nan,np.nan]],columns=["index","none","strat2"])
        df.set_index("index",inplace=True)
        self.ss_m.determine_target_sub(df, False)
        
        self.assertEqual(self.ss_m.target_ss.loc["AC.PA","norm_delta_quantity"],1)
        self.assertEqual(self.ss_m.target_ss.loc["AC.PA","norm_quantity"],1)
        self.assertEqual(self.ss_m.target_ss.loc["AC.PA","priority"],10)
        self.assertEqual(self.ss_m.target_ss.loc["AIR.PA","norm_quantity"],0)
        self.assertTrue(np.isnan(self.ss_m.target_ss.loc["AIR.PA","norm_delta_quantity"]))
        self.assertEqual(self.ss_m.target_ss.loc["AIR.PA","priority"],1000)
        self.assertEqual(self.ss_m.target_ss.loc["KER.PA","norm_quantity"],0)
        
        df=pd.DataFrame(data=[["MC.PA",1,np.nan],["AIR.PA",np.nan,np.nan]],columns=["index","none","strat2"])
        df.set_index("index",inplace=True)
        self.ss_m.determine_target_sub(df, False)

    def test_determine_target_sub2(self):    
        '''
        If the priority is lower, we expect no change
        except if the present quantity is NaN
        '''
        
        ss1=m.StockStatus.objects.get(action=self.a)
        ss1.quantity=100
        ss1.strategy=self.strategy
        ss1.save()
        r=m2.Report.objects.create()
        self.ss_m=ss_manager.StockStatusManager(r,"Paris")
        #low priority 
        df=pd.DataFrame(data=[["AC.PA",np.nan,1],["AIR.PA",np.nan,1]],columns=["index","none","strat2"])
        df.set_index("index",inplace=True)
        self.ss_m.determine_target_sub(df, False)
        self.assertTrue(np.isnan(self.ss_m.target_ss.loc["AC.PA","norm_delta_quantity"]))
        self.assertEqual(self.ss_m.target_ss.loc["AC.PA","norm_quantity"],1)
        self.assertEqual(self.ss_m.target_ss.loc["AC.PA","priority"],10)
        
        self.assertEqual(self.ss_m.target_ss.loc["AIR.PA","norm_delta_quantity"],1)
        self.assertEqual(self.ss_m.target_ss.loc["AIR.PA","norm_quantity"],1)
        self.assertEqual(self.ss_m.target_ss.loc["AIR.PA","priority"],20)
        
    def test_determine_target_sub3(self):    
        '''
        Check if the algo could "pump" in case of equal priority
        '''
        strategy3=m.Strategy.objects.create(name="strat3",priority=10)
        
        ss1=m.StockStatus.objects.get(action=self.a)
        ss1.quantity=100
        ss1.strategy=self.strategy
        ss1.save()
        r=m2.Report.objects.create()
        self.ss_m=ss_manager.StockStatusManager(r,"Paris")
        #low priority 
        df=pd.DataFrame(data=[["AC.PA",np.nan,1, 1],["AIR.PA",np.nan,1,np.nan]],columns=["index","none","strat2","strat3"])
        df.set_index("index",inplace=True)
        self.ss_m.determine_target_sub(df, False)
        self.assertTrue(np.isnan(self.ss_m.target_ss.loc["AC.PA","norm_delta_quantity"]))
        self.assertEqual(self.ss_m.target_ss.loc["AC.PA","norm_quantity"],1)
        self.assertEqual(self.ss_m.target_ss.loc["AC.PA","priority"],10)
        
        self.assertEqual(self.ss_m.target_ss.loc["AIR.PA","norm_delta_quantity"],1)
        self.assertEqual(self.ss_m.target_ss.loc["AIR.PA","norm_quantity"],1)
        self.assertEqual(self.ss_m.target_ss.loc["AIR.PA","priority"],20)      
        
    def test_determine_target_sub4(self):    
        '''
        Strategy with lower priority, but no change in the quantity --> only the strategy should change
        '''
        strategy3=m.Strategy.objects.create(name="strat3",priority=9)
        
        ss1=m.StockStatus.objects.get(action=self.a)
        ss1.quantity=100
        ss1.strategy=self.strategy
        ss1.save()
        r=m2.Report.objects.create()
        self.ss_m=ss_manager.StockStatusManager(r,"Paris")
        #low priority 
        df=pd.DataFrame(data=[["AC.PA",np.nan,1, 1],["AIR.PA",np.nan,1,np.nan]],columns=["index","none","strat2","strat3"])
        df.set_index("index",inplace=True)
        self.ss_m.determine_target_sub(df, False)
        
        self.assertEqual(self.ss_m.target_ss.loc["AC.PA","norm_delta_quantity"],0)
        self.assertEqual(self.ss_m.target_ss.loc["AC.PA","norm_quantity"],1)
        self.assertEqual(self.ss_m.target_ss.loc["AC.PA","priority"],9)
        
        self.assertEqual(self.ss_m.target_ss.loc["AIR.PA","norm_delta_quantity"],1)
        self.assertEqual(self.ss_m.target_ss.loc["AIR.PA","norm_quantity"],1)
        self.assertEqual(self.ss_m.target_ss.loc["AIR.PA","priority"],20)           
        #print(self.ss_m.target_ss)
        
    def test_determine_target_sub5(self):          
        df=pd.DataFrame(data=[["^FCHI",1]],columns=["index","none"])
        df.set_index("index",inplace=True)
        self.ss_m.determine_target_sub(df, True)

        self.assertEqual(self.ss_m.target_ss.loc["^FCHI","norm_delta_quantity"],0)
        self.assertEqual(self.ss_m.target_ss.loc["^FCHI","norm_quantity"],0)
        self.assertEqual(self.ss_m.target_ss.loc["^FCHI","priority"],10)
        
        self.assertEqual(self.ss_m.target_ss.loc["BNP.PA","norm_delta_quantity"],1)
        self.assertEqual(self.ss_m.target_ss.loc["BNP.PA","norm_quantity"],1)
        self.assertEqual(self.ss_m.target_ss.loc["BNP.PA","priority"],10)      
        
    def test_determine_target_sub6(self):          
        df=pd.DataFrame(data=[["^FCHI",-1]],columns=["index","none"])
        df.set_index("index",inplace=True)
        self.ss_m.determine_target_sub(df, True)

        self.assertEqual(self.ss_m.target_ss.loc["^FCHI","norm_delta_quantity"],0)
        self.assertEqual(self.ss_m.target_ss.loc["^FCHI","norm_quantity"],0)
        self.assertEqual(self.ss_m.target_ss.loc["^FCHI","priority"],10)
        
        self.assertEqual(self.ss_m.target_ss.loc["KER.PA","norm_delta_quantity"],-1)
        self.assertEqual(self.ss_m.target_ss.loc["KER.PA","norm_quantity"],-1)
        self.assertEqual(self.ss_m.target_ss.loc["KER.PA","priority"],10)  
        
    def test_determine_target(self):          
        self.ss_m.determine_target()           

    def test_perform_orders(self):
        ss1=m.StockStatus.objects.get(action=self.a)
        self.assertEqual(ss1.quantity,0)

        df=pd.DataFrame(data=[["AC.PA",0,self.strategy.id,True,10,1,1]],
                        columns=["symbol","quantity","strategy_id","order_in_ib","priority","norm_quantity","norm_delta_quantity"],
                        )
        df.set_index("symbol",inplace=True)
        self.ss_m.target_ss=df
        self.ss_m.perform_orders(testing=True)
        
        ss1=m.StockStatus.objects.get(action=self.a) #need to be called again otherwise not actualized somehow
        self.assertEqual(ss1.quantity,1)
        ent_ex_symbols=m2.ListOfActions.objects.get(report=self.r,used_api="YF",entry=True,buy=True)
        self.assertTrue(np.equal(ent_ex_symbols.actions.all(),[self.a]).all())
    
        self.r=m2.Report.objects.create()
        self.ss_m=ss_manager.StockStatusManager(self.r,"Paris")
        df=pd.DataFrame(data=[["AI.PA",0,self.strategy.id,True,10,-1,-1]],
                        columns=["symbol","quantity","strategy_id","order_in_ib","priority","norm_quantity","norm_delta_quantity"],
                        )
        df.set_index("symbol",inplace=True)
        self.ss_m.target_ss=df
        self.ss_m.perform_orders(testing=True) 
        
        ss1=m.StockStatus.objects.get(action=self.a2)
        self.assertEqual(ss1.quantity,-1)
        ent_ex_symbols=m2.ListOfActions.objects.get(report=self.r,used_api="YF",entry=True,buy=False)
        self.assertTrue(np.equal(ent_ex_symbols.actions.all(),[self.a2]).all())

    def test_perform_orders2(self):  
        df=pd.DataFrame(data=[["AI.PA",0,self.strategy.id,True,10,1,2]],
                        columns=["symbol","quantity","strategy_id","order_in_ib","priority","norm_quantity","norm_delta_quantity"],
                        )
        df.set_index("symbol",inplace=True)
        self.ss_m.target_ss=df
        self.ss_m.perform_orders(testing=True) 
        
        ss1=m.StockStatus.objects.get(action=self.a2)
        self.assertEqual(ss1.quantity,1)
        
    def test_add_target_quantity(self):
        
        self.assertTrue(np.isnan(self.ss_m.target_ss_by_st.loc['AC.PA',"none"]))
        
        self.ss_m.add_target_quantity('AC.PA',"none",1)
        self.assertEqual(self.ss_m.target_ss_by_st.loc['AC.PA',"none"],1)
        
        self.ss_m.add_target_quantity('AC.PA',"none",-1)
        self.assertTrue(np.isnan(self.ss_m.target_ss_by_st.loc['AC.PA',"none"]))

        self.ss_m.add_target_quantity('AC.PA',"strat2",-1)
        self.assertEqual(self.ss_m.target_ss_by_st.loc['AC.PA',"strat2"],-1)
        
        self.ss_m.add_target_quantity('AC.PA',"strat2",-1000)
        self.assertEqual(self.ss_m.target_ss_by_st.loc['AC.PA',"strat2"],-1)
        
    def test_cand_to_quantity(self):
        cands=["AC.PA"]
        self.ss_m.cand_to_quantity(cands,"none",False)
        self.assertEqual(self.ss_m.target_ss_by_st.loc["AC.PA","none"],1)
        self.assertEqual(self.ss_m.target_ss_by_st.loc["AI.PA","none"],0)
        self.assertTrue(np.isnan(self.ss_m.target_ss_by_st.loc["AIR.PA","none"]))
        cands=["AI.PA"]
        self.ss_m.cand_to_quantity(cands,"none",False)
        self.assertEqual(self.ss_m.target_ss_by_st.loc["AC.PA","none"],0)
        self.assertEqual(self.ss_m.target_ss_by_st.loc["AI.PA","none"],1)
        self.assertTrue(np.isnan(self.ss_m.target_ss_by_st.loc["AIR.PA","none"]))
        cands=["AIR.PA"]
        self.ss_m.cand_to_quantity(cands,"none",True)
        self.assertEqual(self.ss_m.target_ss_by_st.loc["AC.PA","none"],0)
        self.assertEqual(self.ss_m.target_ss_by_st.loc["AI.PA","none"],0)
        self.assertEqual(self.ss_m.target_ss_by_st.loc["AIR.PA","none"],-1)     
        
    def test_clean_wrong_direction(self):   
         self.ss_m.present_ss.loc["AC.PA","quantity"]=1
         self.ss_m.present_ss.loc["AI.PA","quantity"]=0
         self.ss_m.present_ss.loc["AIR.PA","quantity"]=-1
         self.ss_m.present_ss.loc["AIR.PA","strategy_id"]=self.strategy.id
  
         self.ss_m.clean_wrong_direction("none",True) #going to short, we clean long
         self.assertEqual(self.ss_m.target_ss_by_st.loc["AC.PA","none"],0)
         self.assertTrue(np.isnan(self.ss_m.target_ss_by_st.loc["AI.PA","none"]))
         self.assertTrue(np.isnan(self.ss_m.target_ss_by_st.loc["AIR.PA","none"]))
         
         self.r=m2.Report.objects.create()
         self.ss_m=ss_manager.StockStatusManager(self.r)
         
         self.ss_m.present_ss.loc["AC.PA","quantity"]=1
         self.ss_m.present_ss.loc["AI.PA","quantity"]=0
         self.ss_m.present_ss.loc["AIR.PA","quantity"]=-1
         self.ss_m.present_ss.loc["AIR.PA","strategy_id"]=self.strategy.id
         
         self.ss_m.clean_wrong_direction("none",False) #going to short, we clean long
         self.assertTrue(np.isnan(self.ss_m.target_ss_by_st.loc["AC.PA","none"]))
         self.assertTrue(np.isnan(self.ss_m.target_ss_by_st.loc["AI.PA","none"]))
         self.assertEqual(self.ss_m.target_ss_by_st.loc["AIR.PA","none"],0)
         
    def test_order_nosubstrat(self):
        cands=["AC.PA"]
        self.ss_m.order_nosubstrat(cands,"Paris","none",False,keep=True)
        self.assertEqual(self.ss_m.target_ss_by_st.loc["AC.PA","none"],1)
        self.assertEqual(self.ss_m.target_ss_by_st.loc["AI.PA","none"],0)
        self.assertTrue(np.isnan(self.ss_m.target_ss_by_st.loc["AIR.PA","none"]))
        self.ss_m.present_ss.loc["AC.PA","quantity"]=1
        cands=["AI.PA"]
        self.ss_m.order_nosubstrat(cands,"Paris","none",False,keep=True)
        self.assertEqual(self.ss_m.target_ss_by_st.loc["AC.PA","none"],0)
        self.assertEqual(self.ss_m.target_ss_by_st.loc["AC.PA","retard_keep"],1)
        self.assertEqual(self.ss_m.target_ss_by_st.loc["AI.PA","none"],1)
        self.assertTrue(np.isnan(self.ss_m.target_ss_by_st.loc["AIR.PA","none"]))
        self.ss_m.present_ss.loc["AC.PA","quantity"]=0
        self.ss_m.present_ss.loc["AI.PA","quantity"]=1
        cands=["AIR.PA"]
        self.ss_m.order_nosubstrat(cands,"Paris","none",True,keep=True)
        self.assertEqual(self.ss_m.target_ss_by_st.loc["AC.PA","none"],0)
        self.assertEqual(self.ss_m.target_ss_by_st.loc["AI.PA","none"],0)
        self.assertEqual(self.ss_m.target_ss_by_st.loc["AIR.PA","none"],-1)   
        self.assertEqual(self.ss_m.target_ss_by_st.loc["AC.PA","retard_keep"],1)
        self.assertEqual(self.ss_m.target_ss_by_st.loc["AI.PA","retard_keep"],0)         

    def test_cand_to_quantity_entry(self):
        self.ss_m.cand_to_quantity_entry([],"none", False)
        self.assertTrue(np.isnan(self.ss_m.target_ss_by_st.loc["AC.PA","none"]))
        self.assertTrue(np.isnan(self.ss_m.target_ss_by_st.loc["AI.PA","none"]))
        self.assertTrue(np.isnan(self.ss_m.target_ss_by_st.loc["AIR.PA","none"]))

        cands=["AC.PA"]
        self.ss_m.cand_to_quantity_entry(cands,"none", False)
        self.assertEqual(self.ss_m.target_ss_by_st.loc["AC.PA","none"],1)
        self.assertTrue(np.isnan(self.ss_m.target_ss_by_st.loc["AI.PA","none"]))
        self.assertTrue(np.isnan(self.ss_m.target_ss_by_st.loc["AIR.PA","none"]))

        cands=["AI.PA"]
        self.ss_m.cand_to_quantity_entry(cands,"none", False)
        self.assertEqual(self.ss_m.target_ss_by_st.loc["AC.PA","none"],1)
        self.assertEqual(self.ss_m.target_ss_by_st.loc["AI.PA","none"],1)
        self.assertTrue(np.isnan(self.ss_m.target_ss_by_st.loc["AIR.PA","none"]))
        
    def test_ex_ent_to_target(self):
        self.ss_m.ex_ent_to_target(False,False,False,False,"AC.PA","none")
        self.assertTrue(np.isnan(self.ss_m.target_ss_by_st.loc["AC.PA","none"]))
        self.ss_m.ex_ent_to_target(True,False,False,False,"AC.PA","none")
        self.assertEqual(self.ss_m.target_ss_by_st.loc["AC.PA","none"],1)
        #contradiction
        self.ss_m.ex_ent_to_target(False,True,False,False,"AC.PA","none")
        
        self.assertTrue(np.isnan(self.ss_m.target_ss_by_st.loc["AC.PA","none"]))
        self.assertTrue(np.isnan(self.ss_m.target_ss_by_st.loc["AC.PA","none"]))
        
        self.ss_m.ex_ent_to_target(False,True,False,False,"AI.PA","none")
        self.assertEqual(self.ss_m.target_ss_by_st.loc["AI.PA","none"],0)
        
        self.ss_m.ex_ent_to_target(False,False,True,False,"AIR.PA","none")
        self.assertEqual(self.ss_m.target_ss_by_st.loc["AIR.PA","none"],-1)
        
        self.ss_m.ex_ent_to_target(False,False,False,True,"KER.PA","none")
        self.assertEqual(self.ss_m.target_ss_by_st.loc["KER.PA","none"],0)        
        
    def test_scan_removed_strat(self):
        self.ss_m.present_ss.loc["AC.PA","quantity"]=1
        #none is not listed in the strat for Paris
        self.ss_m.scan_removed_strat()
        self.assertEqual(self.ss_m.target_ss_by_st.loc["AC.PA","none"],0)
        self.assertTrue(np.isnan(self.ss_m.target_ss_by_st.loc["AIR.PA","none"]))     
        
    def test_display_target_ss_by_st(self):
        df=pd.DataFrame(data=[["AC.PA","ACT",np.nan,1, 1],["AIR.PA","ACT",np.nan,1,np.nan],
                              ["^FCHI","IND",np.nan,1, 1],["KER.PA","ACT",np.nan,np.nan,np.nan],],
                        columns=["symbol","category_id","none","strat2","strat3"])
        df.set_index("symbol",inplace=True)
        self.ss_m.target_ss_by_st=df
        
        out=self.ss_m.display_target_ss_by_st()
        expected="AC.PA\nstrat2 strat3 \n1.0    1.0    \r\n\nAIR.PA\nstrat2 \n1.0    \r\n\n"
        self.assertEqual(out,expected)
        
        out=self.ss_m.display_target_ss_by_st(it_is_index=True)
        expected="^FCHI\nstrat2 strat3 \n1.0    1.0    \r\n\n"
        self.assertEqual(out,expected)