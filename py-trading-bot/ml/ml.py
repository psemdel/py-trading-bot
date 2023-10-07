#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 30 20:28:39 2023

@author: maxime
"""
from core.data_manager import retrieve_data_offline 
from core.constants import BEAR_PATTERNS, BULL_PATTERNS
from core import indicators as ic
from core import macro
from core.presel import Presel
from core.common import remove_multi
import vectorbtpro as vbt
import gc
import numbers

import pandas as pd
import numpy as np
from numba import njit
import joblib

from sklearn.neural_network import MLPClassifier, MLPRegressor
from sklearn.preprocessing import StandardScaler 
from sklearn.model_selection import train_test_split
from sklearn import metrics
from sklearn.ensemble import RandomForestRegressor

import pickle

from core import strat, stratL, constants, common, presel
import math

#Object to train the models offline
def defi_x_single_preprocessing(
      open_: pd.core.frame.DataFrame,
      high: pd.core.frame.DataFrame, 
      low: pd.core.frame.DataFrame, 
      close: pd.core.frame.DataFrame,  
      close_ind: pd.core.frame.DataFrame,
      volume: pd.core.frame.DataFrame,
      ):
    
    all_x={}
    t=ic.VBTMA.run(close)
    all_x['MA_ent']=t.entries.astype(float)
    all_x['MA_ex']=t.exits.astype(float)
    
    t=ic.VBTSTOCHKAMA.run(high,low,close)
    all_x['STOCH_ent']=t.entries_stoch.astype(float)
    all_x['STOCH_ex']=t.exits_stoch.astype(float)
    all_x['STOCH_v']=t.stoch
    
    all_x['KAMA_ent']=t.entries_kama.astype(float)
    all_x['KAMA_ex']=t.exits_kama.astype(float)

    t=ic.VBTSUPERTREND.run(high,low,close)
    all_x['SUPERTREND_ent']=t.entries.astype(float)
    all_x['SUPERTREND_ex']=t.exits.astype(float)
                    
    t=vbt.BBANDS.run(close)
    all_x['BBANDS_ent']=t.lower_above(close).astype(float)
    all_x['BBANDS_ex']=t.upper_below(close).astype(float)
    all_x["bandwidth"]=t.bandwidth
    all_x["bandwidth_above"]=t.bandwidth_above(close)
    all_x["bandwidth_below"]=t.bandwidth_below(close)
    
    t=vbt.RSI.run(close,wtype='simple')
    all_x['RSI']=t.rsi
    all_x['RI20_ent']=t.rsi_crossed_below(20).astype(float)
    all_x['RI20_ex']=t.rsi_crossed_above(80).astype(float)
    
    all_x['RI30_ent']=t.rsi_crossed_below(30).astype(float)
    all_x['RI30_ex']=t.rsi_crossed_above(70).astype(float)

    t=ic.VBTWILLR.run(high,low, close)
    all_x["WILLR"]=t.out
    
    #for func_name in BULL_PATTERNS:
    #    all_x[func_name+'_ent']=ic.VBTPATTERNONE.run(open_,high,low,close,func_name, "ent").out.astype(float)
        
    #for func_name in BEAR_PATTERNS:
    #    all_x[func_name+'ex']=ic.VBTPATTERNONE.run(open_,high,low,close,func_name, "ex").out.astype(float)
    
    all_x["GROW_30"]=ic.VBTGROW.run(close,distance=30, ma=False).out
    all_x["GROW_30_rank"]=all_x["GROW_30"].rank(axis=1, ascending=False)
    all_x["GROW_30_ma"]=ic.VBTGROW.run(close,distance=30, ma=True).out
    all_x["GROW_30_ma_rank"]=all_x["GROW_30_ma"].rank(axis=1, ascending=False)
    all_x["GROW_30_dema"]=ic.VBTGROW.run(close,distance=30, dema=True).out
    all_x["GROW_30_dema_rank"]=all_x["GROW_30_dema"].rank(axis=1, ascending=False)

    all_x["GROW_50"]=ic.VBTGROW.run(close,distance=50, ma=False).out
    all_x["GROW_50_rank"]=all_x["GROW_50"].rank(axis=1, ascending=False)
    all_x["GROW_50_ma"]=ic.VBTGROW.run(close,distance=50, ma=True).out
    all_x["GROW_50_ma_rank"]=all_x["GROW_50_ma"].rank(axis=1, ascending=False)
    all_x["GROW_50_dema"]=ic.VBTGROW.run(close,distance=50, dema=True).out
    all_x["GROW_50_dema_rank"]=all_x["GROW_50_dema"].rank(axis=1, ascending=False)
  
    t=ic.VBTMA.run(close)
    all_x["MA_ent"]=t.entries.astype(float)
    all_x["MA_ex"]=t.exits.astype(float)
    all_x["MA_fast_over_slow"]=t.fast_over_slow.astype(float)
    
    all_x["KAMA_duration"]=ic.VBTKAMATREND.run(close).duration
    all_x["KAMA_duration_rank"]=all_x["KAMA_duration"].rank(axis=1, ascending=False)

    all_x["volatility"]=ic.VBTNATR.run(high, low, close).natr
    
    macd=vbt.MACD.run(close, macd_wtype='simple',signal_wtype='simple')
    all_x["hist"]=macd.hist
    all_x["macd"]=macd.macd

    all_x["divergence"]=ic.VBTDIVERGENCE.run(close,close_ind).out
    all_x["std"]=close.rolling(5).std()
    all_x["macro_trend"]=macro.VBTMACROTREND.run(close).macro_trend    

    del t
    gc.collect()
    
    return all_x

def defi_x_single_direct(
      open_: pd.core.frame.DataFrame,
      high: pd.core.frame.DataFrame, 
      low: pd.core.frame.DataFrame, 
      close: pd.core.frame.DataFrame,  
      close_ind: pd.core.frame.DataFrame,
      volume: pd.core.frame.DataFrame,
      sample_size:int=50
      ):
    # Use x[n-1], x[n-2]... as input
    all_x={}
     
    for jj in range(1,sample_size+1):
        all_x["price_past"+str(jj)]=close.shift(jj)   
        
    return all_x
        

class ML():
    def __init__(
            self,
            period: str,
            indexes: list=["CAC40", "DAX", "NASDAQ"], #,"NYSE",,"FIN","HEALTHCARE","IT"
            ):

        #init
        for k in ["indexes"]:
            setattr(self,k,locals()[k])
        
        for key in ["close","open","low","high","data","volume"]:
            setattr(self,key+"_dic",{})
            setattr(self,key+"_ind_dic",{})

        for ind in self.indexes:
            retrieve_data_offline(self,ind,period)                
            self.data_dic[ind]=self.data
            for d in ["Close","Open","Low","High","Volume"]:
                getattr(self,d.lower()+"_dic")[ind]=self.data_dic[ind].get(d)   
                getattr(self,d.lower()+"_ind_dic")[ind]=self.data_ind.get(d)   
            
    def prepare(self,
               test_size:numbers.Number=0.2,
               data_name:str=None,
               preprocessing:bool=True,
               next_day_price:bool=True,
               distance:int=30
               ):
        
        
        if data_name is None:
            self.defi_x(preprocessing=preprocessing)
            self.x_df, self.x_train, self.x_test=self.flatten(self.all_x)
            self.defi_y(next_day_price=next_day_price, distance=distance)
            self.y_df, self.y_train, self.y_test=self.flatten(self.all_y)
        else:
            self.x_df=pd.read_csv("x_"+data_name+".csv",index_col=[0,1,2],parse_dates=True)
            self.y_df=pd.read_csv("y_"+data_name+".csv",index_col=[0,1,2],parse_dates=True)
            self.x_train=pd.read_csv("x_train_"+data_name+".csv",index_col=[0,1,2],parse_dates=True)
            self.y_train=pd.read_csv("y_train_"+data_name+".csv",index_col=[0,1,2],parse_dates=True)
            self.x_test=pd.read_csv("x_test_"+data_name+".csv",index_col=[0,1,2],parse_dates=True)
            self.y_test=pd.read_csv("y_test_"+data_name+".csv",index_col=[0,1,2],parse_dates=True)
        print("preparation finished")
        
    def save(self,data_name:str):
        self.x_df.to_csv("x_"+data_name+".csv")
        self.y_df.to_csv("y_"+data_name+".csv")
        self.x_train.to_csv("x_train_"+data_name+".csv")
        self.y_train.to_csv("y_train_"+data_name+".csv")        
        self.x_test.to_csv("x_test_"+data_name+".csv")
        self.y_test.to_csv("y_test_"+data_name+".csv")
        
    def defi_x(
        self,
        preprocessing:bool=True,
        sample_size:int=50
    ):
        self.all_x={}
        for ind in self.indexes: #CAC, DAX, NASDAQ
            if preprocessing:
                self.all_x[ind]=defi_x_single_preprocessing(
                    self.open_dic[ind].shift(1),
                    self.high_dic[ind].shift(1),
                    self.low_dic[ind].shift(1),
                    self.close_dic[ind].shift(1),
                    self.close_ind_dic[ind].shift(1),
                    self.volume_dic[ind].shift(1)
                    )
            else:
                self.all_x[ind]=defi_x_single_direct(
                    self.open_dic[ind].shift(1),
                    self.high_dic[ind].shift(1),
                    self.low_dic[ind].shift(1),
                    self.close_dic[ind].shift(1),
                    self.close_ind_dic[ind].shift(1),
                    self.volume_dic[ind].shift(1),
                    sample_size=sample_size
                    )                
 
    def defi_y(
        self,
        next_day_price:bool=True,
        distance:int=30
    ):
        self.all_y={}
        for ind in self.indexes: #CAC, DAX, NASDAQ
            all_y={}
            close=self.close_dic[ind]  
            
            if next_day_price:
                all_y["price_rise"]=100*(np.divide(close,close.shift(1))-1)
            else:    
                t=ic.VBTMINMAX.run(close,distance=distance)
                all_y['max_3mo']=t.maximum
                all_y['min_3mo']=t.minimum 
            
            self.all_y[ind]=all_y
        
    def create_empty_x_df(self, ind, s):
        return pd.MultiIndex.from_arrays([
            self.close_dic[ind].index,  #list(
            [s for ii in self.close_dic[ind].index],
            [ind for ii in self.close_dic[ind].index]
        ])
        
    def flatten(
        self, 
        input_arr,
        test_size:numbers.Number=0.2,
        ):
        
        df_total=None
        df_train=None
        df_test=None
        ts={}
        
        if "window_start" not in self.__dir__():
            self.window_start={}

        #remove the multiindex only once
        for ind in self.indexes: #CAC, DAX, NASDAQ    
            ts[ind]={}
            for col in input_arr[ind]:
                ts[ind][col]=remove_multi(input_arr[ind][col])
           
        #somehow vbt is designed with the columns in the other orders so to say, which lead to this very computer intensive function
        for ind in self.indexes: #CAC, DAX, NASDAQ
            total_len=len(self.close_dic[ind].index)
            
            learn_len=int(math.floor((1-test_size)*total_len))
            test_len=total_len-learn_len
            
            #put the window at the same place for x and y
            if ind in self.window_start:
                test_window_start=self.window_start[ind]
            else:
                test_window_start=0 # np.random.randint(0,learn_len)
                                    #random has the advantage of the variation but we then need to reload this info if we want to test our model later, it
                                    #makes also the comparison between models more difficult
                self.window_start[ind]=test_window_start
            
            test_window_end=test_window_start+test_len
            
            learn_range=[i for i in range(0,test_window_start)]+[i for i in range(test_window_end,total_len)]
            for s in self.close_dic[ind].columns:
                dfs=[]
                for col in input_arr[ind]:
                    dfs.append(ts[ind][col][s].rename(col))
                #put columns together
                df=pd.concat(dfs,axis=1)
                #clean
                df=df.fillna(0)
                df=df.replace([np.inf, -np.inf], 0)   
                #get the index
                df.set_index(self.create_empty_x_df(ind,s) ,inplace=True)
                
                #put rows together
                df_total=pd.concat([df_total,df])
                
                #split train and test
                df_test=pd.concat([df_test,df.iloc[test_window_start:test_window_end]])
                df_train=pd.concat([df_train,df.iloc[learn_range]])         

        return df_total, df_train, df_test
    
    def unflatten(self, df, col: str=None) -> dict:
        indexes=pd.unique(df.index.get_level_values(2))
        out={}
        out2={}
        
        if col is None:
            if len(df.columns)==1:
                col=df.columns[0]
            else:
                raise ValueError("Define a column for unflatten")

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
        model_name:str="model",
        model_type:str="NN"
        ):
        
        self.model_name=model_name
        
        if model_type=="NN":
            self.scaler = StandardScaler()  
            self.scaler.fit(self.x_train)
            scaled_x_train=self.scaler.transform(self.x_train)
            self.clf =  MLPRegressor(
                               # solver='lbfgs',  #lbfgs
                                alpha=1e-5,  #1e-5
                                hidden_layer_sizes=(40, 4), 
                
                #activation{‘identity’, ‘logistic’, ‘tanh’, ‘relu’}, default=’relu’
                                #random_state=1,
                                max_iter=10000)
        else:
            scaled_x_train=self.x_train
            self.clf= RandomForestRegressor(max_depth=10)
        print("starting the fitting")
        self.clf.fit(scaled_x_train, self.y_train)
        with open("models/"+model_name+".pickle", "wb") as f:
            pickle.dump(self.clf, f)
        if model_type=="NN":   
            joblib.dump(self.scaler, "models/scaler_"+self.model_name+".save") 
        print("model saved, starting the testing")
        acc=self.test()

    def test(self, model_name:str="model",force:bool=False):
        self.load_model(model_name,force=force)

        if self.clf.__class__ == MLPRegressor:
            scaled_x_test=self.scaler.transform(self.x_test)
            scaled_x_train=self.scaler.transform(self.x_train)
            scaled_x_df=self.scaler.transform(self.x_df)
        else:
            scaled_x_test=self.x_test
            scaled_x_train=self.x_train
            scaled_x_df=self.x_df
        acc_test = self.clf.score(scaled_x_test, self.y_test)
        print("accurary test: "+str(acc_test))
        acc_train = self.clf.score(scaled_x_train, self.y_train)
        print("accurary train: "+str(acc_train))
        acc_total = self.clf.score(scaled_x_df, self.y_df)
        print("accurary total: "+str(acc_total))

    def load_model(self, model_name:str="model",force:bool=False):
        self.model_name=model_name
        if "clf" not in self.__dir__() or force:   
            with open("models/"+model_name+".pickle", 'rb') as pickle_file:
                self.clf = pickle.load(pickle_file)
        if self.clf.__class__ == MLPRegressor and "scaler" not in self.__dir__():
            self.scaler = joblib.load("models/scaler_"+self.model_name+".save")
    
    def use(self,model_name:str, x_df,force:bool=False):
        self.load_model(model_name,force=force)

        if self.clf.__class__ == MLPRegressor:
            scaled_x_df=self.scaler.transform(x_df)
        else:
            scaled_x_df=x_df
        y=self.clf.predict(scaled_x_df)
        
        if self.clf.n_outputs_ == 1:
            return y, pd.DataFrame(data=y,columns=['price_rise'],index=x_df.index)  
        elif self.clf.n_outputs_ == 2:
            return y, pd.DataFrame(data=y,columns=['max_3mo','min_3mo'],index=x_df.index)    
    
class MLLive(ML):
    def __init__(
            self,
            period: str,
            input_ust
            ):
        
        self.indexes=["all"]
        self.ust=input_ust
        for k, v in self.ust.__dict__.items():
            if k not in self.__dict__ or getattr(self, k) is None:
                setattr(self,k,v)
                
        for key in ["close","open","low","high","data","volume"]:
            setattr(self,key+"_dic",{})
            getattr(self,key+"_dic")["all"]=getattr(self,key)
        
            setattr(self,key+"_ind_dic",{})
            getattr(self,key+"_ind_dic")["all"]=getattr(self,key+"_ind")

#For real use
class PreselML(Presel):
    def __init__(
            self,
            period:str,
            **kwargs):
        super().__init__(period,**kwargs)
        
        self.model_name=None
        self.model_type="NN"
        self.max_candidates_nb=1
        self.no_ust=True
        self.strategy="ml"
    
    def defi(self):
        all_x=defi_x_single_preprocessing(self.open, self.high, self.low, self.close, self.close_ind, self.volume)
        est=self.clf.feature_names_in_
        all_x_filter={}           
        
        for c in all_x:
            if c in est:
                all_x_filter[c]=all_x[c]
        self.x_df=self.flatten(all_x_filter)     
                   
    def use(self):
        self.load_model(self.model_name,model_type=self.model_type)
        
        if self.model_type=="NN":
            scaled_x_df=self.scaler.transform(self.x_df)
        else:
            scaled_x_df=self.x_df
        y=self.clf.predict(scaled_x_df)
        self.y_df=pd.DataFrame(data=y,columns=['max_3mo','min_3mo'],index=self.x_df.index) 
    
    def prerun(self):
        self.defi()
        self.use()
        self.unflatten_y_df=self.unflatten("max_3mo")

    def sorting(self,i: str,**kwargs):
        v={}
        for symbol in self.close.columns.values:
            v[symbol]=self.unflatten_y_df[symbol].loc[i]
        self.sorted=sorted(v.items(), key=lambda tup: tup[1], reverse=True)

    def unflatten(self, col: str) -> dict:
        out={}

        for s in pd.unique(self.y_df.index.get_level_values(1)):
            sub_df2=self.y_df[self.y_df.index.get_level_values(1)==s]
            out[s]=sub_df2[col].values
    
        return pd.DataFrame(data=out,index=pd.unique(self.y_df.index.get_level_values(0)))  
     
    def create_empty_x_df(self, ind, s):
        return pd.MultiIndex.from_arrays([
            self.close_dic[ind].index,  #list(
            [s for ii in self.close_dic[ind].index],
            [ind for ii in self.close_dic[ind].index]
        ])
    
    #to be rewritten
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
                #clean
                df=df.fillna(0)
                df=df.replace([np.inf, -np.inf], 0)   
                #get the index
                df.set_index(self.create_empty_x_df(ind,s) ,inplace=True)
                
                #put rows together
                if df_total is None:
                    df_total=df
                else:
                    df_total=pd.concat([df_total,df])
        return df_total           
               
    def load_model(self, model_name:str="model", model_type:str="NN"):
        self.model_name=model_name
        if model_type=="NN" and "scaler" not in self.__dir__():
            self.scaler = joblib.load("models/scaler_"+self.model_name+".save")
        if "clf" not in self.__dir__():   
            with open("models/"+model_name+".pickle", 'rb') as pickle_file:
                self.clf = pickle.load(pickle_file)           
                
class PreselML_Forest(PreselML):
    def __init__(
            self,
            period:str,
            **kwargs):
        super().__init__(period,**kwargs)  
        self.model_name="Bbla"
        self.model_type="bbb"
                      