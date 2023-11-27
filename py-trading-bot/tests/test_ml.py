#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov 20 21:33:19 2023

@author: maxime
"""

from django.test import TestCase
from ml import ml
from orders import models as m
    
class TestML(TestCase):
    def setUp(self):
        self.period="2007_2022_08"
        self.symbol_index="CAC40"
        
        self.features_name=['STOCH', 'RSI',"WILLR","MFI",'BBANDS_BANDWIDTH','ULTOSC',"OBV","AD",
               "GROW_30","GROW_30_RANK","GROW_30_MA","GROW_30_MA_RANK","GROW_30_DEMA","GROW_30_DEMA_RANK",
               "GROW_50","GROW_50_RANK","GROW_50_MA","GROW_50_MA_RANK","GROW_50_DEMA","GROW_50_DEMA_RANK",
               "GROW_200","GROW_200_RANK","GROW_200_MA","GROW_200_MA_RANK","GROW_200_DEMA","GROW_200_DEMA_RANK",
               "KAMA_DURATION","KAMA_DURATION_RANK","NATR","HIST","MACD","DIVERGENCE","STD","MACRO_TREND",
               "PU_RESISTANCE","PU_SUPPORT"]
        
        f=m.Fees.objects.create(name="zero",fixed=0,percent=0)
        cat=m.ActionCategory.objects.create(name="actions",short="ACT")
        
        self.e=m.StockEx.objects.create(name="Paris",fees=f,ib_ticker="SBF",main_index=None,ib_auth=True)
        c=m.Currency.objects.create(name="euro")
        
        self.m=ml.ML(self.period)
        
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
        
    def test_several_index(self):
        m=ml.ML(self.period,indexes=['CAC40','NASDAQ'])
        m.prepare(preprocessing=True, 
          next_day_price=False, 
          distance=10,
          model_type="MLP",
          steps=10,
          features_name=self.features_name)   
        self.assertEqual(self.m.x_df.shape,(429787, 36))

    def test_several_index_LSTM(self):
        m=ml.ML(self.period,indexes=['CAC40','NASDAQ'])
        m.prepare(preprocessing=True, 
          next_day_price=False, 
          distance=10,
          model_type="LSTM",
          steps=10,
          features_name=self.features_name)        
        self.assertEqual(self.m.x_df.shape,(109, 3933, 10, 36))
        
    def test_prepare_MLP(self):
        self.m.prepare(preprocessing=True, 
          next_day_price=False, 
          distance=10,
          model_type="MLP",
          steps=10,
          features_name=self.features_name)    
        
        self.assertEqual(self.m.x_df.shape,(156156, 36))
        self.assertEqual(self.m.x_train.shape,(124917, 36))
        self.assertEqual(self.m.x_test.shape,(31239, 36))
        self.assertEqual(self.m.y_df.shape,(156156, 1))
        self.assertEqual(self.m.y_train.shape,(124917, 1))
        self.assertEqual(self.m.y_test.shape,(31239, 1))
        
        self.m.prepare(preprocessing=False, 
          next_day_price=False, 
          distance=10,
          model_type="MLP",
          steps=10,
          features_name=self.features_name)    
        
        self.assertEqual(self.m.x_df.shape,(156156, 1))
        self.assertEqual(self.m.x_train.shape,(124917, 1))
        self.assertEqual(self.m.x_test.shape,(31239, 1))
        self.assertEqual(self.m.y_df.shape,(156156, 1))
        self.assertEqual(self.m.y_train.shape,(124917, 1))
        self.assertEqual(self.m.y_test.shape,(31239, 1))
        
        self.m.prepare(preprocessing=True, 
          next_day_price=True, 
          distance=10,
          model_type="MLP",
          steps=10,
          features_name=self.features_name)   
        
        self.assertEqual(self.m.x_df.shape,(156156, 36))
        self.assertEqual(self.m.x_train.shape,(124917, 36))
        self.assertEqual(self.m.x_test.shape,(31239, 36))
        self.assertEqual(self.m.y_df.shape,(156156, 1))
        self.assertEqual(self.m.y_train.shape,(124917, 1))
        self.assertEqual(self.m.y_test.shape,(31239, 1))

        self.m.prepare(preprocessing=False, 
          next_day_price=True, 
          distance=10,
          model_type="MLP",
          steps=10,
          features_name=self.features_name)  
        
        self.assertEqual(self.m.x_df.shape,(156156, 1))
        self.assertEqual(self.m.x_train.shape,(124917, 1))
        self.assertEqual(self.m.x_test.shape,(31239, 1))
        self.assertEqual(self.m.y_df.shape,(156156, 1))
        self.assertEqual(self.m.y_train.shape,(124917, 1))
        self.assertEqual(self.m.y_test.shape,(31239, 1))
        
        self.m.train("test_mlp1",n_epochs=10)
        
    def test_prepare_LSTM(self):
        self.m.prepare(preprocessing=True, 
          next_day_price=False, 
          distance=10,
          model_type="LSTM",
          steps=10,
          features_name=self.features_name)
        self.assertEqual(self.m.x_df.shape,(39, 3994, 10, 36))
        
        self.m.train("test_lstm1",n_epochs=10)

    def test_prepare_LSTM2(self):       
        self.m.prepare(preprocessing=False, 
          next_day_price=False, 
          distance=10,
          model_type="LSTM",
          steps=10,
          features_name=self.features_name)
        self.assertEqual(self.m.x_df.shape,(39, 3994, 10, 1))
        
        self.m.train("test_lstm2",n_epochs=10)
        
    def test_load_model_docu(self):
        self.m.load_model_docu("mlp_test")
        
        self.assertEqual(self.m.model_type,"MLP")

        self.m.load_model_docu("lstm_test")

        self.assertEqual(self.m.model_type,"LSTM")


    def test_load_model(self):
        self.m.load_model("mlp_test")
        
        self.assertEqual(self.m.model_type,"MLP")

        self.m.load_model("lstm_test",force=True)

        self.assertEqual(self.m.model_type,"LSTM")        

    def test_use_MLP(self):
        y=self.m.use("mlp_test","total")
        self.assertEqual(y.shape,(156156,1))
        self.assertEqual(round(y[0,0],2),-2.09)
        self.assertEqual(round(y[-1,0],2),-2.09)

        y=self.m.use("mlp_test","test")
        self.assertEqual(y.shape,(31239,1))
        self.assertEqual(round(y[0,0],2),-2.09)
        self.assertEqual(round(y[-1,0],2),-2.09)
        
        y=self.m.use("mlp_test","train")
        self.assertEqual(y.shape,(124917,1))
        self.assertEqual(round(y[0,0],2),-2.09)
        self.assertEqual(round(y[-1,0],2),-2.09)
        
    def test_use_LSTM(self):
        y=self.m.use("lstm_test","total")
        self.assertEqual(y.shape,(39,3994,1 ))
        self.assertEqual(round(y[0,0,0].item(),2),-0.92)
        self.assertEqual(round(y[0,-1,0].item(),2),-4.32)
        
        y=self.m.use("lstm_test","test")
        self.assertEqual(y.shape,(39,791,1 ))
        self.assertEqual(round(y[0,0,0].item(),2),-0.92)
        self.assertEqual(round(y[0,-1,0].item(),2),-2.88)
        
        y=self.m.use("lstm_test","train")
        self.assertEqual(y.shape,(39,3193,1 ))
        self.assertEqual(round(y[0,0,0].item(),2),-2.17)
        self.assertEqual(round(y[0,-1,0].item(),2),-4.32)    
      
        
        
        
        