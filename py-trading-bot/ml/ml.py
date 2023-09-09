#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 30 20:28:39 2023

@author: maxime
"""
from core.data_manager import retrieve_data_offline 
from core.constants import BEAR_PATTERNS, BULL_PATTERNS
from core import indicators as ic
from core.common import remove_multi
import vectorbtpro as vbt
import pandas as pd
import numpy as np
import gc
import numbers
import joblib

from sklearn.neural_network import MLPClassifier, MLPRegressor
from sklearn.preprocessing import StandardScaler 
from sklearn.model_selection import train_test_split
from sklearn import metrics

import pickle

class ML():
    def __init__(
            self,
            period: str,
            indexes: list=["CAC40", "DAX", "NASDAQ"], #,"NYSE"
            ):

        #init
        for k in ["indexes"]:
            setattr(self,k,locals()[k])
        
        for key in ["close","open","low","high","data"]:
            setattr(self,key+"_dic",{})

        for ind in self.indexes:
            retrieve_data_offline(self,ind,period)                
            self.data_dic[ind]=self.data
            for d in ["Close","Open","Low","High"]:
                getattr(self,d.lower()+"_dic")[ind]=self.data_dic[ind].get(d)   
                
    def prepare(self,
               test_size:numbers.Number=0.2,
               data_name:str=None,
               ):
        if data_name is None:
            self.defi_x()
            self.x_df=self.flatten(self.all_x)
            self.defi_y()
            self.y_df=self.flatten(self.all_y)
        else:
            self.x_df=pd.read_csv("x_"+data_name+".csv",index_col=[0,1,2])
            self.y_df=pd.read_csv("y_"+data_name+".csv",index_col=[0,1,2])
            
        self.x_train, self.x_test, self.y_train, self.y_test = train_test_split(
            self.x_df, 
            self.y_df, 
            test_size=test_size, 
        )
        print("preparation finished")
        
    def save(self,data_name:str):
        self.x_df.to_csv("x_"+data_name+".csv")
        self.y_df.to_csv("y_"+data_name+".csv")

    def defi_x(self):
        self.all_x={}
        for ind in self.indexes: #CAC, DAX, NASDAQ
            all_x={}
            open_=self.open_dic[ind]
            high=self.high_dic[ind]
            low=self.low_dic[ind]
            close=self.close_dic[ind]
            
            t=ic.VBTMA.run(close)
            all_x['MA_ent']=t.entries.astype(float)
            all_x['MA_ex']=t.exits.astype(float)
            
            t=ic.VBTSTOCHKAMA.run(high,low,close)
            all_x['STOCH_ent']=t.entries_stoch.astype(float)
            all_x['STOCH_ex']=t.exits_stoch.astype(float)
            t2=t.stoch.fillna(0)
            t2=t2.replace([np.inf, -np.inf], 0)
            all_x['STOCH_v']=t2
            
            all_x['KAMA_ent']=t.entries_kama.astype(float)
            all_x['KAMA_ex']=t.exits_kama.astype(float)

            t=ic.VBTSUPERTREND.run(high,low,close)
            all_x['SUPERTREND_ent']=t.entries.astype(float)
            all_x['SUPERTREND_ex']=t.exits.astype(float)
                            
            t=vbt.BBANDS.run(close)
            all_x['BBANDS_ent']=t.lower_above(close).astype(float)
            all_x['BBANDS_ex']=t.upper_below(close).astype(float)

            t=vbt.RSI.run(close,wtype='simple')
            all_x['RI20_ent']=t.rsi_crossed_below(20).astype(float)
            all_x['RI20_ex']=t.rsi_crossed_above(80).astype(float)
            
            all_x['RI30_ent']=t.rsi_crossed_below(30).astype(float)
            all_x['RI30_ex']=t.rsi_crossed_above(70).astype(float)

            for func_name in BULL_PATTERNS:
                all_x[func_name+'_ent']=ic.VBTPATTERNONE.run(open_,high,low,close,func_name, "ent").out.astype(float)
                
            for func_name in BEAR_PATTERNS:
                all_x[func_name+'ex']=ic.VBTPATTERNONE.run(open_,high,low,close,func_name, "ex").out.astype(float)
            
            all_x["GROW_30"]=ic.VBTGROW.run(close,distance=30, ma=False).out
            all_x["GROW_50"]=ic.VBTGROW.run(close,distance=50, ma=False).out
          
            t=ic.VBTMA.run(close)
            all_x["MA_ent"]=t.entries.astype(float)
            all_x["MA_ex"]=t.exits.astype(float)
            all_x["MA_fast_over_slow"]=t.fast_over_slow.astype(float)
            
            duration=ic.VBTKAMATREND.run(close).duration
            all_x["KAMA_duration"]=duration
            all_x["KAMA_duration_rank"]=ic.VBTRANK.run(duration).rank_arr
            
            t=ic.VBTNATR.run(high, low, close).natr
            t=t.fillna(0)
            t=t.replace([np.inf, -np.inf], 0)
            all_x["volatility"]=t
            self.all_x[ind]=all_x

        del t
        gc.collect()
        
    def defi_y(self):
        self.all_y={}
        for ind in self.indexes: #CAC, DAX, NASDAQ
            all_y={}
            open_=self.open_dic[ind]
            high=self.high_dic[ind]
            low=self.low_dic[ind]
            close=self.close_dic[ind]  
            
            t=ic.VBTMINMAX.run(close)
            all_y['max_3mo']=t.maximum
            all_y['min_3mo']=t.minimum 
            
            self.all_y[ind]=all_y
        
    def create_empty_x_df(self, ind, s):
        return pd.MultiIndex.from_arrays([
            self.close_dic[ind].index,  #list(
            [s for ii in self.close_dic[ind].index],
            [ind for ii in self.close_dic[ind].index]
        ])
        
    def flatten(self, input_arr):
        df_total=None
        ts={}

        #remove the multiindex only once
        for ind in self.indexes: #CAC, DAX, NASDAQ    
            ts[ind]={}
            for col in input_arr[ind]:
                ts[ind][col]=remove_multi(input_arr[ind][col])
           
        #somehow vbt is designed with the columns in the other orders so to say, which lead to this very computer intensive function
        for ind in self.indexes: #CAC, DAX, NASDAQ
            for s in self.close_dic[ind].columns:
                dfs=[]
                for col in input_arr[ind]:
                    dfs.append(ts[ind][col][s].rename(col))
                #put columns together
                df=pd.concat(dfs,axis=1)
                #get the index
                df.set_index(self.create_empty_x_df(ind,s) ,inplace=True)
                
                #put rows together
                if df_total is None:
                    df_total=df
                else:
                    df_total=pd.concat([df_total,df])
        return df_total
    
    def unflatten(self, df, col: str) -> dict:
        indexes=pd.unique(df.index.get_level_values(2))
        out={}
        out2={}

        for ind in indexes:
            sub_df=df[df.index.get_level_values(2)==ind]
            out[ind]={}

            for s in pd.unique(sub_df.index.get_level_values(1)):
                sub_df2=sub_df[sub_df.index.get_level_values(1)==s]
                out[ind][s]=sub_df2[col].values
        
            out2[ind]=pd.DataFrame(data=out[ind],index=pd.unique(sub_df.index.get_level_values(0)))  
        return out2
    
    def train(
        self,
        model_name:str="model"
        ):
        
        self.model_name=model_name
        self.scaler = StandardScaler()  
        self.scaler.fit(self.x_train)
        scaled_x_train=self.scaler.transform(self.x_train)
        self.clf =  MLPRegressor(solver='lbfgs', 
                            alpha=1e-5, 
                            hidden_layer_sizes=(10, 2), 
                            random_state=1,
                            max_iter=10000)
        print("starting the fitting")
        self.clf.fit(scaled_x_train, self.y_train)
        with open("models/"+model_name+".pickle", "wb") as f:
            pickle.dump(self.clf, f)
            
        joblib.dump(self.scaler, "models/scaler_"+self.model_name+".save") 
        print("model saved, starting the testing")
        acc=self.test()

    def test(self, model_name:str="model"):
        self.load_model(model_name)
        scaled_x_test=self.scaler.transform(self.x_test)
        acc = self.clf.score(scaled_x_test, self.y_test)
        print("accurary: "+str(acc))
        return acc  
    
    def load_model(self, model_name:str="model"):
        self.model_name=model_name
        if "scaler" not in self.__dir__():
            self.scaler = joblib.load("models/scaler_"+self.model_name+".save")
        if "clf" not in self.__dir__():   
            with open("models/"+model_name+".pickle", 'rb') as pickle_file:
                self.clf = pickle.load(pickle_file)
    
    def use(self,model_name:str, x_df):
        self.load_model(model_name)
        scaled_x_df=self.scaler.transform(x_df)
        y=self.clf.predict(scaled_x_df)
        return y, pd.DataFrame(data=y,columns=['max_3mo','min_3mo'],index=x_df.index)    
           