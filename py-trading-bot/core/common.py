#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan  9 13:09:58 2022

@author: maxime
"""
import numbers
from datetime import datetime
from core.constants import INTRO, DELIST
import pandas as pd

from core.data_manager import retrieve_data_offline

class VBTfunc():
    def __init__(self,symbol_index: str,period: numbers.Number):
        '''
        Parent class for all preselections and underlying strategies

        Arguments
        ----------
           symbol_index: main index to be retrieved
           period: period of time in year for which we shall retrieve the data
        '''
        self.period=period
        self.symbol_index=symbol_index
        retrieve_data_offline(self,symbol_index,period)

def filter_intro_symbol_sub(s: str,y_period: numbers.Number)-> bool:
    '''
    Filter not introduced or delisted products from a list. Here outside of Django execution, to be called within Jupyter

    Arguments
    ----------
           s: YF ticker of the product to be tested
           y_period: period of time in year where we need to check backward from now
    ''' 
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

def filter_intro_symbol(input_symbols: list,y_period: numbers.Number) -> list:
    '''
    Filter not introduced or delisted products from a list. Here outside of Django execution, to be called within Jupyter

    Arguments
    ----------
           input_symbols: list if symbols to be tested
           y_period: period of time in year where we need to check backward from now
    '''  
    symbols=[]
    for s in input_symbols:
        if filter_intro_symbol_sub(s,y_period):
            symbols.append(s)   
    return symbols   

def save(x_df: pd.core.frame.DataFrame,filename: str):
    '''
    Save a dataframe to a file

    Arguments
    ----------
           x_df: a dataframe to be saved
           filename: name of the file where to save the dataframe
    '''
    x_df.to_csv(''+filename)

def save_vbt_both(
        cours: pd.core.frame.DataFrame, 
        entries: pd.core.frame.DataFrame, 
        exits: pd.core.frame.DataFrame,
        entries_short: pd.core.frame.DataFrame,
        exits_short: pd.core.frame.DataFrame,
        suffix:str=""
        ):
    '''
    Save some dataframes, useful for debugging
    '''
    save(entries,"entries"+suffix)
    save(exits, "exits"+suffix)
    save(entries_short,"entries_short"+suffix)
    save(exits_short, "exits_short"+suffix)    
    save(cours,"cours"+suffix)
    
def intersection(lst1: list, lst2: list) -> list:
    '''
    Perform an intersection between two lists

    Arguments
    ----------
           list1: a list
           list1: another list
    '''  
    lst3 = [value for value in lst1 if value in lst2]
    return lst3 

def remove_multi(df: pd.core.frame.DataFrame)-> pd.core.frame.DataFrame:
    '''
    Remove the multi index from the dataframe, to allow futher operations

    Arguments
    ----------
           df: a dataframe
    ''' 
    if type(df)==pd.core.frame.DataFrame:
        multi=df.columns 
        if type(multi)==pd.core.indexes.multi.MultiIndex:
            l=len(multi[0])
    
            for ii in range(l-2,-1,-1):
                multi=multi.droplevel(ii)
            df=pd.DataFrame(data=df.values,index=df.index,columns=multi)
    return df