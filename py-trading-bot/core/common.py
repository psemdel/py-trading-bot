#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan  9 13:09:58 2022

@author: maxime
"""
import math
import numpy as np
from datetime import datetime
from core.constants import INTRO, DELIST
import pandas as pd

from core.data_manager import retrieve

class VBTfunc():
    def __init__(self,symbol_index,period):
        self.period=period
        self.symbol_index=symbol_index
        retrieve(self,symbol_index,period)
    
    def rel_dif(self,n,d): #for instance to calculate distance between MA and signal
        if d==0 or math.isnan(n) or math.isnan(d):
            return 0
        else:
            return round(n/d-1,4) 

def copy_attr(o1,o2):
    for suffix in ["","_ind"]:
        for l in ["high","low","close","open","volume","data"]:
            setattr(o1,l+suffix, getattr(o2,l+suffix))

def filter_intro_symbol_sub(s,y_period):
    td=datetime.today()
    min_y=td.year-y_period
    limit_date=str(min_y)+"-" + str(td.month) + "-" + str(td.day)

    if s in DELIST:
        return False
    if s in INTRO: #should come from database
        if INTRO[s]<limit_date:
            return True
    else:
        return True

    return False

def filter_intro_symbol(input_symbols,y_period):
    symbols=[]
    for s in input_symbols:
        if filter_intro_symbol_sub(s,y_period):
            symbols.append(s)   
    return symbols   

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
    
def intersection(lst1, lst2):
    lst3 = [value for value in lst1 if value in lst2]
    return lst3   

def remove_multi(t2):
    if type(t2)==pd.core.frame.DataFrame:
        multi=t2.columns 
        if type(multi)==pd.core.indexes.multi.MultiIndex:
            l=len(multi[0])
    
            for ii in range(l-2,-1,-1):
                multi=multi.droplevel(ii)
            t2=pd.DataFrame(data=t2.values,index=t2.index,columns=multi)
    return t2