#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan  9 13:09:58 2022

@author: maxime
"""
import math
import numpy as np

from core.data_manager import retrieve

class VBTfunc():
    def __init__(self,symbol_index,period):
        self.period=period
        self.symbol_index=symbol_index
                    
        self.high, self.low, self.close, self.open,self.volume,\
        self.high_ind, self.low_ind, self.close_ind, self.open_ind,\
        self.volume_ind=retrieve(symbol_index,period)
    
    def rel_dif(self,n,d): #for instance to calculate distance between MA and signal
        if d==0 or math.isnan(n) or math.isnan(d):
            return 0
        else:
            return round(n/d-1,4) 
    
def save(x_df,filename):
    x_df.to_csv('data/'+filename)

def save_vbt_both(cours, entries, exits, entries_short, exits_short, **kwargs):
    suffix=kwargs.get("suffix","")
    
    save(entries,"entries"+suffix)
    save(exits, "exits"+suffix)
    save(entries_short,"entries_short"+suffix)
    save(exits_short, "exits_short"+suffix)    
    save(cours,"cours"+suffix)
    
def empty_append(x, v, axis, **kwargs):
    try:
        """
        if axis==0:
            print("v")
            print(np.shape(v))
            print("x")
            print(np.shape(x))
        """
        if v==[]:
            return x
        else:
            av=np.array(v)
    
            if len(av.shape)==1:
                #print("av shape 1")
                if axis==1:
                   av=av.reshape(-1, 1)
                else:
                   av=av.reshape(-1, 1)
                   #av=np.transpose(av)
                #print(np.shape(av))
                
            if type(x) is np.ndarray:
                temp=np.append(x,av,axis=axis)
                return temp
            else:
                return av
    except Exception as msg:
        print("error by append " +str(msg))
        print("shape x: " + str(np.shape(x)))
        print("shape v: " + str(np.shape(v)))
        return x     