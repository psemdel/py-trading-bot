#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 30 20:28:39 2023

@author: maxime
"""
from core.data_manager import retrieve_data_offline 
from core.constants import BEAR_PATTERNS, BULL_PATTERNS
from core.common import candidates_to_YF, remove_multi
from core import indicators as ic
from core import macro
from core.presel import Presel

import vectorbtpro as vbt
import pickle, math, json, gc, numbers
import pandas as pd
import numpy as np
import joblib
from datetime import datetime
import os

from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler 
from sklearn import metrics
from sklearn.ensemble import RandomForestRegressor

from keras import Sequential
from keras.layers import LSTM, Dense

#Object to train the models offline
class MLPreparator():
    def __init__(self,
                open_: pd.core.frame.DataFrame,
                high: pd.core.frame.DataFrame, 
                low: pd.core.frame.DataFrame, 
                close: pd.core.frame.DataFrame,  
                close_ind: pd.core.frame.DataFrame,
                volume: pd.core.frame.DataFrame,
                preprocessing:bool=True,
                features_name:list=None,
                lag:int=0,                
                 ):
        '''
        Calculate with vbt the different signals depending on the content of features_name
        
        Arguments
       	----------
           open_: opening price
           high: highest price
           low: lowest price
           close: closing price
           close_ind: closing price of the main index
           volume: trading volume
           preprocessing: if set to true preprocessed data will be used (STOCH, RSI), otherwise the raw price will be used as input features (x)
           features_name: explicit features name list
           lag: create supplementary features as copy of the original but with a time delay. If lag=2, it will create 2 supplementary features: day-1 and day-2
                it allows using previous time steps with a MLP
        '''
        self.all_x_single={}
        if preprocessing:
            if features_name is None:
                raise ValueError("define features_name for preprocessing")
            self.features_name=features_name
            
            if self.in_features_name(['MA_ex','MA_ent']):
                t=ic.VBTMA.run(close)
                self.defi_x_sub('MA_ent', t.entries)
                self.defi_x_sub('MA_ex', t.exits)
            
            if self.in_features_name(['STOCH','STOCH_ex','STOCH_ent','KAMA_ent','KAMA_ex']):
                t=ic.VBTSTOCHKAMA.run(high,low,close)
                self.defi_x_sub('STOCH', t.stoch)
                self.defi_x_sub('STOCH_ent', t.entries_stoch)
                self.defi_x_sub('STOCH_ex', t.exits_stoch)
                self.defi_x_sub('KAMA_ent', t.entries_kama)
                self.defi_x_sub('KAMA_ex', t.exits_kama)
                
            if self.in_features_name(['SUPERTREND_ent','SUPERTREND_ex']):    
                t=ic.VBTSUPERTREND.run(high,low,close)
                self.defi_x_sub('SUPERTREND_ent', t.entries)
                self.defi_x_sub('SUPERTREND_ex', t.exits)
        
            if self.in_features_name(['BBANDS_ent','BBANDS_ex','BBANDS_BANDWIDTH']):
                t=vbt.BBANDS.run(close)
                self.defi_x_sub('BBANDS_ent', t.lower_above(close))
                self.defi_x_sub('BBANDS_ex', t.upper_below(close))       
                self.defi_x_sub('BBANDS_BANDWIDTH', t.bandwidth)      

            if self.in_features_name(['RSI','RI20_ent','RI20_ex','RI30_ent','RI30_ex']):
                t=vbt.RSI.run(close,wtype='simple')
                self.defi_x_sub('RSI', t.rsi)
                self.defi_x_sub('RI20_ent', t.rsi_crossed_below(20))
                self.defi_x_sub('RI20_ex', t.rsi_crossed_above(80))
                self.defi_x_sub('RI30_ent', t.rsi_crossed_below(30))
                self.defi_x_sub('RI30_ex', t.rsi_crossed_above(70))

            if self.in_features_name(['WILLR']):
                t=vbt.talib("WILLR").run(high, low, close)
                self.defi_x_sub('WILLR', t.real)

            if self.in_features_name(['ULTOSC']):
                t=vbt.talib("ULTOSC").run(high, low, close)
                self.defi_x_sub('ULTOSC', t.real)
                
            if self.in_features_name(['MFI']):
                t=vbt.talib("MFI").run(high, low, close, volume)
                self.defi_x_sub('MFI', t.real)                
        
            for func_name in BULL_PATTERNS:
                if self.in_features_name([func_name]):
                    self.defi_x_sub(func_name, ic.VBTPATTERNONE.run(open_,high,low,close,func_name, "ent").out)  
                
            for func_name in BEAR_PATTERNS:
                if self.in_features_name([func_name]):
                    self.defi_x_sub(func_name, ic.VBTPATTERNONE.run(open_,high,low,close,func_name, "ent").out)  

            for dist in [30, 50 ,200]:
                if self.in_features_name(['GROW_'+str(dist),"GROW_"+str(dist)+"_RANK"]):
                    t=ic.VBTGROW.run(close,distance=dist, ma=False).out
                    self.defi_x_sub('GROW_'+str(dist), t) 
                    self.defi_x_sub("GROW_"+str(dist)+"_RANK", t.rank(axis=1, ascending=False)) 
                    
                if self.in_features_name(['GROW_'+str(dist)+'_MA',"GROW_"+str(dist)+"_MA_RANK"]):
                    t=ic.VBTGROW.run(close,distance=dist, ma=True).out
                    self.defi_x_sub('GROW_'+str(dist)+'_MA', t) 
                    self.defi_x_sub("GROW_"+str(dist)+"_MA_RANK", t.rank(axis=1, ascending=False))  
                    
                if self.in_features_name(['GROW_'+str(dist)+'_DEMA',"GROW_"+str(dist)+"_DEMA_RANK"]):
                    t=ic.VBTGROW.run(close,distance=dist, dema=True).out
                    self.defi_x_sub('GROW_'+str(dist)+'_DEMA', t) 
                    self.defi_x_sub("GROW_"+str(dist)+"_DEMA_RANK", t.rank(axis=1, ascending=False))                 

            if self.in_features_name(['OBV']):
                t=vbt.talib("OBV").run(close,volume)
                self.defi_x_sub('OBV', t.real)         
                
            if self.in_features_name(['AD']):
                t=vbt.talib("AD").run(high,low,close,volume)
                self.defi_x_sub('AD', t.real)                   
                
            if self.in_features_name(["KAMA_DURATION","KAMA_DURATION_RANK"]):
                t=ic.VBTKAMATREND.run(close).duration
                self.defi_x_sub("KAMA_DURATION", t)   
                self.defi_x_sub("KAMA_DURATION_RANK", t.rank(axis=1, ascending=False)) 
                
            if self.in_features_name(['NATR']):   
                t=vbt.talib("NATR").run(high, low, close)
                self.defi_x_sub("NATR", t.real)  
                
            if self.in_features_name(['MACD','HIST']):       
                t=vbt.MACD.run(close, macd_wtype='simple',signal_wtype='simple')
                self.defi_x_sub("HIST", t.hist)  
                self.defi_x_sub("MACD", t.macd)  
        
            if self.in_features_name(['DIVERGENCE']):   
                t=ic.VBTDIVERGENCE.run(close,close_ind)
                self.defi_x_sub('DIVERGENCE', t.out) 
                
            if self.in_features_name(['STD']):                   
                t=close.rolling(5).std()
                self.defi_x_sub('STD', t)
                
            if self.in_features_name(['HT_TRENDMODE']):      
                t=vbt.talib("HT_TRENDMODE").run(close)
                self.defi_x_sub('HT_TRENDMODE', t.integer)

            if self.in_features_name(['MACRO_TREND']):                 
                t=macro.VBTMACROTREND.run(close)
                self.defi_x_sub('MACRO_TREND', t.macro_trend)
                
            if self.in_features_name(["PU_RESISTANCE","PU_SUPPORT"]):                 
                t=ic.VBTSUPPORTRESISTANCE.run(close)
                self.defi_x_sub('PU_RESISTANCE', t.pu_resistance)
                self.defi_x_sub('PU_SUPPORT', t.pu_support)
                
            del t
            gc.collect()
        else:
            self.all_x_single["price_past"]=close.shift(1)
            
        cols=list(self.all_x_single.keys())
        for l in range(1,lag):
            for col in cols:
                self.all_x_single[col+"_"+str(l)]=self.all_x_single[col].shift(l)            

    #return all_x
    def defi_x_sub(self, c:str, v: pd.DataFrame):
        if len(self.features_name)==0 or c in self.features_name:
            self.all_x_single[c]=v.astype(float)
    
    def in_features_name(self,l:list):
        if len(self.features_name)==0:
            return True
        
        for e in l:
            if e in self.features_name:
                return True
        return False

class ML():
    def __init__(
            self,
            period: str,
            indexes: list=["CAC40",] #,"NYSE",,"FIN","HEALTHCARE","IT", "DAX", "NASDAQ","FIN","HEALTHCARE", "DAX","NASDAQ"]
            ):
        '''
        Class to perform machine learning: prepare the data, train the model, test it and use it
        
        Arguments
       	----------
           period: period of time for which we shall retrieve the data
           indexes: main indexes used to download local data
        '''
        for k in ["indexes"]:
            setattr(self,k,locals()[k])
        
        for key in ["close","open","low","high","data","volume"]:
            setattr(self,key+"_dic",{})
            setattr(self,key+"_ind_dic",{})

        #len_min save the minimum length for all data 
        len_min=None 
        for ind in self.indexes:
            retrieve_data_offline(self,ind,period)                
            self.data_dic[ind]=self.data
            for d in ["Close","Open","Low","High","Volume"]:
                getattr(self,d.lower()+"_dic")[ind]=self.data_dic[ind].get(d)   
                getattr(self,d.lower()+"_ind_dic")[ind]=self.data_ind.get(d) 
            self.len_min=len(self.close_dic[ind]) if len_min is None else min(self.close_dic[ind], self.len_min) 
            
        self.features_name=[]
        self.prod=False
        self.steps=None
    
    def load_model_docu(self,
                        model_name:str
                        ):
        '''
        Read documentation file for a model
        '''
        with open(os.path.dirname(__file__)+"/models/"+model_name+".json") as f:
            d = json.load(f)
            for k in d:
                setattr(self,k,d[k])
        
        if "clf" in self.__dir__():
            if self.clf.__class__ == Sequential:
                self.model_type="LSTM"
            elif self.clf.__class__ == MLPRegressor:
                self.model_type="MLP"
            else:
                self.model_type="Forest"
        else:
            print("model type not loaded by docu loading, import the model first using load_model")
        
    def save_model_docu(self,
                        model_name:str
                        ):
        d={}
        for k in ["features_name","model_type", "preprocessing", "next_day_price","distance","lag"]:
            try:
                d[k]=getattr(self,k)
            except:
                print(k+" not found")
        if self.steps is not None: #no point saving info that makes no sense
            d["steps"]=self.steps
        d["training_date"]=datetime.now().strftime("%d.%m.%y")
        
        with open(os.path.dirname(__file__)+"/models/"+model_name+".json", "w") as outfile:
           outfile.write(json.dumps(d, indent=4))

    def prepare(self,
               test_size:numbers.Number=0.2,
               data_name:str=None,
               preprocessing:bool=True,
               next_day_price:bool=True,
               distance:int=30,
               lag:int=0,
               model_type:str="MLP",
               steps:int=200,
               features_name:list=None,
               prod:bool=False
               ):
        '''
        Prepare the data for the training, or load it
        
        Arguments
       	----------
           test_size: proportion of the data to be used for the test
           data_name: instead of preparing it, it is possible to load it from a file named data_name
           preprocessing: if set to true preprocessed data will be used (STOCH, RSI), otherwise the raw price will be used as input features (x)
           next_day_price: if set to true, the price of next day will be used as output (y), otherwise the maximum price in the next "distance" days
           distance: if next_day_price is False, determine the number of days in the future where to look for the maximum price
           lag: create supplementary features as copy of the original but with a time delay. If lag=2, it will create 2 supplementary features: day-1 and day-2
                it allows using previous time steps with a MLP
           model_type: what kind of model should be trained?
           steps: similar to lag but for LSTM model. So number of timesteps to consider for the training of the model
           features_name: explicit features name list
           prod: to be used for production
        '''
        
        for k in ["test_size","preprocessing","next_day_price","distance", "model_type","features_name","lag", "prod"]:
            setattr(self,k,locals()[k])
        if  model_type=="LSTM":
            self.steps=steps
        else:
            self.steps=None

        if data_name is None:
            self.defi_x()
            self.x_df, self.x_train, self.x_test, self.x_scaling=self.flatten(self.all_x)
            self.defi_y()
            self.y_df, self.y_train, self.y_test, self.y_scaling=self.flatten(self.all_y, y_bool=True)
        else:
            self.x_df=pd.read_csv("x_"+data_name+".csv",index_col=[0,1,2],parse_dates=True)
            self.y_df=pd.read_csv("y_"+data_name+".csv",index_col=[0,1,2],parse_dates=True)
            self.x_train=pd.read_csv("x_train_"+data_name+".csv",index_col=[0,1,2],parse_dates=True)
            self.y_train=pd.read_csv("y_train_"+data_name+".csv",index_col=[0,1,2],parse_dates=True)
            self.x_test=pd.read_csv("x_test_"+data_name+".csv",index_col=[0,1,2],parse_dates=True)
            self.y_test=pd.read_csv("y_test_"+data_name+".csv",index_col=[0,1,2],parse_dates=True)
        print("preparation finished")
        
    def save(self,data_name:str):
        '''
        Save the prepared data
        
        Arguments
           data_name: name of the file where to save the data
        '''
        self.x_df.to_csv("x_"+data_name+".csv")
        self.y_df.to_csv("y_"+data_name+".csv")
        self.x_train.to_csv("x_train_"+data_name+".csv")
        self.y_train.to_csv("y_train_"+data_name+".csv")        
        self.x_test.to_csv("x_test_"+data_name+".csv")
        self.y_test.to_csv("y_test_"+data_name+".csv")
        
    def defi_x(self):
        '''
        Create the input (x) for the model
        '''
        self.all_x={}
        for ind in self.indexes: #CAC, DAX, NASDAQ
            ml_prep=MLPreparator(
                self.open_dic[ind].shift(1),
                self.high_dic[ind].shift(1),
                self.low_dic[ind].shift(1),
                self.close_dic[ind].shift(1),
                self.close_ind_dic[ind].shift(1),
                self.volume_dic[ind].shift(1),
                preprocessing=self.preprocessing,
                features_name=self.features_name,
                lag=self.lag)
            self.all_x[ind]=ml_prep.all_x_single
 
    def defi_y(self):
        '''
        Create the output (y) for the model
        
        Arguments
        ----------        
           next_day_price: if set to true, the price of next day will be used as output (y), otherwise the maximum price in the next "distance" days
           distance: if next_day_price is False, determine the number of days in the future where to look for the maximum price
        '''
        self.all_y={}
        for ind in self.indexes: #CAC, DAX, NASDAQ
            all_y={}
            close=self.close_dic[ind]  
            
            if self.next_day_price:
                all_y["price_rise"]=100*(np.divide(close,close.shift(1))-1)
            else:    
                t=ic.VBTMINMAX.run(close,distance=self.distance)
                all_y['max_3mo']=t.maximum
                #all_y['min_3mo']=t.minimum 
            
            self.all_y[ind]=all_y
        
    def create_empty_x_df(self, ind:str, s:str):
        '''
        Create the multiindex for the flatten in the shape (date, symbol, index)
        
        Arguments
        ---------- 
            ind: index name
            s: symbol (ticker)
        '''
        return pd.MultiIndex.from_arrays([
            self.close_dic[ind].index,  #list(
            [s for ii in self.close_dic[ind].index],
            [ind for ii in self.close_dic[ind].index]
        ])
    
    def create_timesteps(self, arr_total, df, y_bool:bool=False):
        '''
        Function for LSTM to create the timesteps, it means slide a window over the signal
        
        Arguments
        ---------- 
            arr_total: array containing all batches
            df: dataframe to add to the arr_total
            y_bool: is it for the output?                   
        '''
        arr_total_3d=None
        
        if y_bool:
            arr_temp_total=np.reshape(df.values[self.steps:],(1,df[self.steps:].shape[0], df[self.steps:].shape[1]))
        else:
            for ii in range(df.shape[0]-self.steps):
                arr_temp_total=np.reshape(df.values[ii:ii+self.steps],(1, self.steps, df.shape[1]))
                arr_total_3d = np.vstack((arr_total_3d,arr_temp_total)) if arr_total_3d is not None else arr_temp_total
            arr_temp_total=np.reshape(arr_total_3d,(1,arr_total_3d.shape[0],arr_total_3d.shape[1],arr_total_3d.shape[2]))
            
            del arr_total_3d
        arr_total= np.vstack((arr_total, arr_temp_total)) if arr_total is not None else arr_temp_total

        del arr_temp_total 
        return arr_total   
    
    def flatten(
        self, 
        input_arr,
        y_bool:bool=False,
        ) -> (np.array, np.array, np.array, np.array):
        '''
        Function to put the input in the right shape for the training.
        
        For MLP, it means in the shape (batch, features)
        For LSTM, it means in the shape (batch, time steps, features). In this case we also create a different arr_scaling
        as the scaler needs a 2d array.
        
        Arguments
       	----------
           input_arr: output of defi_x or defi_y
           y_bool: is it for the output?            
        '''
        arr_total=None
        arr_train=None
        arr_test=None
        arr_scaling=None
        ts={}
        
        if "window_start" not in self.__dir__():
            self.window_start={}

        #remove the multiindex only once
        for ind in self.indexes: #CAC, DAX, NASDAQ    
            ts[ind]={}
            for col in input_arr[ind]:
                ts[ind][col]=remove_multi(input_arr[ind][col])
        
        #for lstm all indexes should have same length
        if self.model_type=="LSTM":
            for ind in self.indexes:   
                self.close_dic[ind]=self.close_dic[ind].iloc[:self.len_min]         
        
        #somehow vbt is designed with the columns in the other orders so to say, which lead to this very computer intensive function
        for ind in self.indexes: #CAC, DAX, NASDAQ
            total_len=len(self.close_dic[ind].index)
            
            if not self.prod:
                learn_len=int(math.floor((1-self.test_size)*total_len))
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
                learn_range=[i for i in range(0,test_window_start)]+[i for i in range(test_window_end,self.len_min)]
            
            for s in self.close_dic[ind].columns:
                dfs=[]
                for col in input_arr[ind]:
                    dfs.append(ts[ind][col][s].rename(col))
                #put columns together
                df=pd.concat(dfs,axis=1)
                #clean
                df=df.fillna(0)
                df=df.replace([np.inf, -np.inf], 0)   
                df=df.iloc[:self.len_min]
                #put rows together
                if not self.prod:
                    df_temp_test=df.iloc[test_window_start:test_window_end]
                    df_temp_train=df.iloc[learn_range]
                
                if self.model_type=="LSTM":
                    #the different symbols needs to be separated to avoid that the last samples of one symbol are used for the next symbol eval
                    arr_total=self.create_timesteps(arr_total, df, y_bool=y_bool)

                    if not self.prod:
                        arr_test=self.create_timesteps(arr_test, df_temp_test,  y_bool=y_bool)
                        arr_train=self.create_timesteps(arr_train, df_temp_train, y_bool=y_bool)
                        arr_scaling=np.vstack((arr_scaling,df.values)) if arr_scaling is not None else df.values
                else:
                    #for MLP, there is dependency between the steps, so we can put all indexes together in one df
                    arr_total=np.vstack((arr_total,df.values)) if arr_total is not None else df.values
                    if not self.prod:
                        arr_test=np.vstack((arr_test,df_temp_test.values)) if arr_test is not None else df_temp_test.values
                        arr_train=np.vstack((arr_train,df_temp_train.values)) if arr_train is not None else df_temp_train.values

            if self.model_type!="LSTM":
                arr_scaling=arr_total
              
        del df
        if not self.prod:
            df_temp_test, df_temp_train
        
        return arr_total, arr_train, arr_test, arr_scaling
    
    def unflatten(self, 
                  df: pd.DataFrame, 
                  col: str=None) -> dict:
        '''
        Function to unflatten the result of model and bring it to a vbt like format
       
        Arguments
        ----------
           df: output of use, dataframe to unflatten
           col: columns to select from df, in case there are several       
        '''
        out={}
        out2={}
        
        if self.clf.__class__ == Sequential:
            for ind in self.indexes:
                out[ind]={}
                for i, s in enumerate(self.close_dic[ind].columns):
                    out[ind][s]=df[i,:,0]
                    
                out2[ind]=pd.DataFrame(data=out[ind],index=self.close.index[:df.shape[1]]) 
        else:
            indexes=pd.unique(df.index.get_level_values(2))
            
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

    def scale(
        self,
        input_arr,
        y_bool:bool=False,
        inverse: bool=False,
        predict: bool=False,
        model=None
        ):
        '''
        Scale or descaled arrays that are in dimension 3 or 4
        
        Arguments
        ----------
           input_arr: array to scale/unscale
           y_bool: is this array for the output?
           inverse: should we unscale instead of scale?
           predict: should we make a prediction?
           model: model to be used for the prediction
        '''
        scaled=None
        
        if y_bool or predict:
            scaler=self.scaler_y    
            
            for j in range(input_arr.shape[0]):  
                if inverse or predict:
                    if predict:
                        arr=model.predict(input_arr[j,:,:,:],batch_size=input_arr.shape[1])
                        t=scaler.inverse_transform(arr)
                    else:
                        t=scaler.inverse_transform(input_arr[j,:,:])
                else:
                    t=scaler.transform(input_arr[j,:,:])
                t=np.reshape(t, (1, t.shape[0], t.shape[1]))
                scaled=np.vstack((scaled,t)) if scaled is not None else t 
            del t
        else:
            scaler=self.scaler_x        
        
            for i in range(input_arr.shape[0]):       
                scaled_3d=None                  
                for j in range(input_arr.shape[1]):
                    if inverse:
                        t=scaler.inverse_transform(input_arr[i,j,:,:])
                    else:
                        t=scaler.transform(input_arr[i,j,:,:])
                    t=np.reshape(t, (1, t.shape[0], t.shape[1]))
                    scaled_3d=np.vstack((scaled_3d,t)) if scaled_3d is not None else t
                scaled_3d=np.reshape(scaled_3d,(1,scaled_3d.shape[0], scaled_3d.shape[1], scaled_3d.shape[2]))                       
                scaled=np.vstack((scaled,scaled_3d)) if scaled is not None else scaled_3d
            del scaled_3d, t
        
        return scaled

    def train(
        self,
        model_name:str,
        n_epochs: int=100
        ):
        '''
        Train and save the machine learning model
        
        Arguments
        ----------
           model_name: how do we want to name the model?
           n_epochs: number of epochs for the training        
        '''
        self.model_name=model_name
        
        if self.model_type in ["MLP","LSTM"]:
            self.scaler_x = StandardScaler()  
            self.scaler_x.fit(self.x_scaling)

            if self.model_type=="LSTM":
                scaled_x_train=self.scale(self.x_train)
            else:
                scaled_x_train=self.scaler_x.transform(self.x_train)    

            self.scaler_y = StandardScaler()  
            self.scaler_y.fit(self.y_scaling)
              
            if self.model_type=="LSTM":   
                scaled_y_train=self.scale(self.y_train, y_bool=True)     
            else:                                 
                scaled_y_train=self.scaler_y.transform(self.y_train)
          
            #free memory
            self.x_scaling=None
            self.y_scaling=None
        
        if self.model_type=="MLP":
            self.clf =  MLPRegressor(
                                #activation="tanh",
                                # solver='lbfgs',
                                alpha=1e-5,
                                hidden_layer_sizes=(40, 4), 
                                #activation{‘identity’, ‘logistic’, ‘tanh’, ‘relu’}, default=’relu’
                                #random_state=1,
                                max_iter=10000)
        elif self.model_type=="LSTM":
            self.clf = Sequential()
            self.clf.add(LSTM(4,  batch_input_shape=(scaled_x_train.shape[1], scaled_x_train.shape[2], scaled_x_train.shape[3]), stateful=True))
            self.clf.add(Dense(1))
            self.clf.compile(loss='mean_squared_error', optimizer='adam')
        else:
            self.model_type="Forest"
            scaled_x_train=self.x_train
            scaled_y_train=self.y_train
            self.clf= RandomForestRegressor(max_depth=10)
        
        print("starting the fitting")
        if self.model_type=="LSTM":
            for i in range(n_epochs):
                if i%100==0:
                    print("n_epochs: "+str(i))
                for k in range(self.x_train.shape[0]): #for each symbol
                    self.clf.fit(scaled_x_train[k,:,:,:], scaled_y_train[k,:,:], batch_size=self.x_train.shape[1],epochs=1, shuffle=False, verbose=0) #
                    self.clf.reset_states()
        else:
            self.clf.fit(scaled_x_train, scaled_y_train)
        
        with open(os.path.dirname(__file__)+"/models/"+self.model_name+".pickle", "wb") as f:
            pickle.dump(self.clf, f)
        self.save_model_docu(self.model_name)
            
        if self.model_type in ["MLP","LSTM"]:   
            joblib.dump(self.scaler_x, os.path.dirname(__file__)+"/models/scaler_x_"+self.model_name+".save") 
            joblib.dump(self.scaler_y, os.path.dirname(__file__)+"/models/scaler_y_"+self.model_name+".save") 
        
        print("model saved, starting the testing")
        self.test()
        
        del scaled_x_train, scaled_y_train
        gc.collect()

    def test(
            self, 
            model_name:str=None,
            ):
        '''
        Test the model, print the r2 score
        
        Arguments
        ----------
           model_name: how is the model named?
        '''
        if model_name is not None:
            self.load_model(model_name,force=True)
            
        self.yhat_test = self.use(self.model_name, selector="test")
        self.yhat_train=self.use(self.model_name, selector="train")
        self.yhat_total=self.use(self.model_name, selector="total")
        if self.clf.__class__ == Sequential:
            r2_score_test=[]
            r2_score_train=[] 
            r2_score_total=[] 

            for k in range(self.x_test.shape[0]):
                r2_score_test.append(metrics.r2_score(self.yhat_test[k,:,:],self.y_test[k,:,:]))
            for k in range(self.x_train.shape[0]):    
                r2_score_train.append(metrics.r2_score(self.yhat_train[k,:,:],self.y_train[k,:,:]))
            for k in range(self.x_df.shape[0]):    
                r2_score_total.append(metrics.r2_score(self.yhat_total[k,:,:],self.y_df[k,:,:]))    
            print("mean r2 score test: "+str(np.mean(r2_score_test)))
            print("mean r2 score train: "+str(np.mean(r2_score_train)))
            print("mean r2 score total: "+str(np.mean(r2_score_total)))                
        else:
            r2_score_test = metrics.r2_score(self.yhat_test, self.y_test)
            r2_score_train = metrics.r2_score(self.yhat_train, self.y_train)
            r2_score_total = metrics.r2_score(self.yhat_total, self.y_df)
            print("r2 score test: "+str(r2_score_test))
            print("r2 score train: "+str(r2_score_train))
            print("r2 score total: "+str(r2_score_total))

    def load_model(
            self, 
            model_name:str="model",
            force:bool=False
            ):
        '''
        Load the model and the associated scalers
        
        Arguments
        ----------
           model_name: how is the model named?
           force: should we reload the model is one is already loaded
        '''        
        self.model_name=model_name
        
        import os
        print(os.getcwd())
        
        if "clf" not in self.__dir__() or force:   
            with open(os.path.dirname(__file__)+"/models/"+self.model_name+".pickle", 'rb') as pickle_file:
                self.clf = pickle.load(pickle_file)
            #must be after loading clf
            self.load_model_docu(model_name)
        if self.clf.__class__ in [MLPRegressor,Sequential]  and "scaler_x" not in self.__dir__():
            self.scaler_x = joblib.load(os.path.dirname(__file__)+"/models/scaler_x_"+self.model_name+".save")
            self.scaler_y = joblib.load(os.path.dirname(__file__)+"/models/scaler_y_"+self.model_name+".save")
            
    def predict_lstm(
        self,
        x: np.array,
        model:str
        )-> np.array:
        '''
        Function to predict with a LSTM model, include the scaling part
        
        Arguments
        ----------
           x: input array, unscaled
           model: model to be used for the prediction
        '''
        x_scaled=self.scale(x)
        print("scaling of x for predicting finished")
        return self.scale(x_scaled, predict=True, model=model)
    
    def use(
            self,
            model_name:str, 
            selector:str,
            force:bool=False,
            prod: bool=None):
        '''
        Use the model to predict. Contains all steps to make it easy to use.
        
        Arguments
        ----------
            selector: string to decide if we want to calculate with test, train or the whole input
            force: should we reload the model is one is already loaded
            prod: to be used for production
        '''
        if prod is not None:
            self.prod=prod
        
        self.load_model(model_name,force=force)
        
        prepare=False
        selector=str(selector)
        if selector=="test" and "x_test" not in self.__dir__() or\
           selector=="train" and "x_train" not in self.__dir__():
            prepare=True
            self.prod=False
        if selector=="total" and "x_df" not in self.__dir__():
            prepare=True 
        
        if prepare: 
            #prepare depending on the model parameters read in load_model
            self.prepare(
                preprocessing=self.preprocessing, 
                next_day_price=self.next_day_price,
                distance=self.distance,
                lag=self.lag,
                model_type=self.model_type,
                steps=self.steps,
                features_name=self.features_name,
                prod=self.prod
                )
            
        if selector=="test":
            x_df=self.x_test
        elif selector=="train":
            x_df=self.x_train
        else:
            x_df=self.x_df

        if self.clf.__class__ == MLPRegressor:
            scaled_x_df=self.scaler_x.transform(x_df)
        elif self.clf.__class__ == Sequential:
            #for LSTM we need to create a new model because the batch size must be equal to x_df.shape[1], otherwise it will crash
            model = Sequential()
            model.add(LSTM(4,  batch_input_shape=(x_df.shape[1], x_df.shape[2], x_df.shape[3]), stateful=True))
            model.add(Dense(1))
            old_weights = self.clf.get_weights()
            model.set_weights(old_weights)
            #scaling in self.predict here
        else:
            #no scaling for forest
            scaled_x_df=x_df
            
        if self.clf.__class__ == Sequential:
            y=self.predict_lstm(x_df, model)
        else:
            y=self.clf.predict(scaled_x_df)
            y=self.scaler_y.inverse_transform(np.reshape(y,(y.shape[0],1)))
        return y

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
        self.len_min=len(self.close_dic["all"]) 
        self.prod=True #normally we don't want to test with MLLive


class MLforPresel(ML):
    def __init__(
            self,
            data,
            open_: pd.core.frame.DataFrame,
            high: pd.core.frame.DataFrame, 
            low: pd.core.frame.DataFrame, 
            close: pd.core.frame.DataFrame,  
            close_ind: pd.core.frame.DataFrame,
            volume: pd.core.frame.DataFrame,
            ):
        '''
        Modification of ML to use input from Presel
        
        Arguments
       	----------
           data: as formated by vbt
           open_: opening price
           high: highest price
           low: lowest price
           close: closing price
           close_ind: closing price of the main index
           volume: trading volume
        '''
        self.indexes=["all"]
        for key in ["close","open","low","high","data","volume"]:
            setattr(self,key+"_dic",{})
            if key!="open":
                getattr(self,key+"_dic")['all']=locals()[key]
        self.open_dic['all']=open_
        self.close_ind_dic={'all':close_ind}
        self.len_min=len(close)

#For real use
class PreselML(Presel):
    def __init__(
            self,
            period:str,
            **kwargs):
        super().__init__(period,**kwargs)
        
        self.m=MLforPresel(
            self.data,
            self.open,
            self.high,
            self.low,
            self.close,
            self.close_ind,
            self.volume
            )

        self.max_candidates_nb=1
        self.no_ust=True
        self.strategy="ml"
        self.reduce_trades_number=True
        self.threshold_cand=1 #percent
        
    def end_init(self):
        if "model_name" not in self.__dir__():
            raise ValueError("model_name is not defined yet")
        
        yhat=self.m.use(
            model_name=self.model_name,
            selector="total",
            prod=True
            )
        
        #unflatten
        if self.m.model_type=="LSTM":
            self.yhat=pd.DataFrame(
                data=np.transpose(yhat[:,:,0]),
                columns=self.close.columns,
                index=self.close.index[self.m.steps:])  
        else:
            out={}        
            l=len(self.close.index)
            
            for k, s in enumerate(self.close.columns):
                if len(yhat.shape)==1: #forest
                    out[s]=yhat[k*l:(k+1)*l][:]
                else: #MLP
                    out[s]=yhat[k*l:(k+1)*l][:,0]

            self.yhat=pd.DataFrame(
                data=out,
                index=self.close.index)       

    def sorting(
            self,
            i: str, 
            short: bool=False,
            **kwargs
            ):
        
        if "yhat" not in self.__dir__():
            raise ValueError("PreselML is an abstract class, it cannot be used directly")
        
        if self.reduce_trades_number: #otherwise use sorting_g
            present_index_nb=self.close.index.get_loc(i)
        
            if present_index_nb<self.m.steps: #steps that cannot be calculated, as too soon
                p=self.yhat.columns[0] #convention
                v=0
                self.sorted=[(p, v)]
            else:
                p=self.yhat.loc[i].idxmax() #potential candidate
                v=self.yhat.loc[i].max()
                if present_index_nb==self.m.steps:
                    self.sorted=[(p, v)]
                else:
                    previous_index=self.close.index[present_index_nb-1]
                    pres_cand=self.candidates['long'][previous_index][0]
                    pres_cand_v=self.yhat[pres_cand].loc[i]
                    if v-pres_cand_v>=self.threshold_cand: #change candidate only if the difference is significative
                        self.sorted=[(p, v)]
                    else:
                        self.sorted=[(pres_cand, pres_cand_v)]

    def sorting_g(self):
        if not self.reduce_trades_number: #otherwise use sorting
            self.sorted_rank=self.yhat.rank(axis=1, ascending=False)
            self.sorting_criterium=self.yhat

    def perform(self, r, **kwargs):
        candidates, _=self.get_candidates()
        r.ss_m.order_nosubstrat(candidates_to_YF(self.ust.symbols_to_YF,candidates), self.ust.exchange, self.strategy, False,keep=False)

class PreselMLCustom(PreselML):
    def __init__(
            self,
            period:str,
            model_name:str,
            **kwargs):    
        super().__init__(period,**kwargs)    
        self.model_name=model_name
        self.end_init()

class PreselLSTM_A(PreselML):
    def __init__(
            self,
            period:str,
            **kwargs):    
        super().__init__(period,**kwargs)    
    
        self.model_name="lstm_new"
        self.strategy="lstm_A"
        self.end_init()
        
if __name__=="__main__":
    period="2007_2023_08"
    m=ML(period,indexes=['CAC40', "DAX", "NASDAQ"])  #,"NYSE",,"FIN","HEALTHCARE","IT", "DAX", "NASDAQ","FIN","HEALTHCARE", "DAX","NASDAQ"]
    features_name=['STOCH', 'RSI',"WILLR","MFI",'BBANDS_BANDWIDTH','ULTOSC',"OBV","AD",
               "GROW_30","GROW_30_RANK","GROW_30_MA","GROW_30_MA_RANK","GROW_30_DEMA","GROW_30_DEMA_RANK",
               "GROW_50","GROW_50_RANK","GROW_50_MA","GROW_50_MA_RANK","GROW_50_DEMA","GROW_50_DEMA_RANK",
               "GROW_200","GROW_200_RANK","GROW_200_MA","GROW_200_MA_RANK","GROW_200_DEMA","GROW_200_DEMA_RANK",
               "KAMA_DURATION","KAMA_DURATION_RANK","NATR","HIST","MACD","DIVERGENCE","STD","MACRO_TREND","HT_TRENDMODE",
               "PU_RESISTANCE","PU_SUPPORT"]
    
    m.prepare(preprocessing=True, 
          next_day_price=False, 
          distance=10,
          model_type="MLP",
          #steps=10,
          features_name=features_name)
    
    m.train("231219_mlp_epoch1000_future10_CAC_DAX_NASDAQ",n_epochs=1000)
             
