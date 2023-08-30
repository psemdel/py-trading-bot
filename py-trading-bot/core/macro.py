#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 29 20:33:22 2022

@author: maxime
"""
import numbers
import vectorbtpro as vbt
import numpy as np
import talib
from numba import njit
from trading_bot.settings import _settings

@njit
def major_int_sub(
        kama: np.array, 
        init: int, 
        last_top_ind: int, 
        last_bot_ind: int, 
        threshold: numbers.Number, 
        threshold_uncertain: numbers.Number, 
        deadband: numbers.Number
        )-> (np.array, int, int):
    '''
    Determine when the trend is bull/bear or uncertain in order to improve the underlying strategy or
    to determine the ideal direction (long/short/both)
    
    The convention is -1=bull, 1=bear, 0=uncertain
    '''

    '''
    Determine the top and bottom from the KAMA function

    Arguments
    ----------
        kama: smoothed price (KAMA method)
        init: initial index
        last_top_ind: index of the last top
        last_bot_ind: index of the last bottom
        threshold: threshold to determine when there is a top or a bottom
        threshold_uncertain: threshold to determine when we are in an uncertain period
        deadband: deadband before changing the trend decision
    '''
    macro_trend_nouncertain= np.full(kama.shape, 0)
    macro_trend= np.full(kama.shape, 0)
    max_ind= np.full(kama.shape, 0)
    min_ind= np.full(kama.shape, 0)
    
    if init is None:
        return macro_trend, min_ind, max_ind
    
    for ii in range(init,len(kama)):
        macro_trend_nouncertain[ii]=macro_trend_nouncertain[ii-1] #init
        
        #since last extrema
        maximum=np.max(kama[max(last_top_ind,last_bot_ind):ii])
        maximum_ind=max(last_top_ind,last_bot_ind)+np.argmax(kama[max(last_top_ind,last_bot_ind):ii])

        #some checks without interest to avoid error
        if max(last_top_ind,last_bot_ind)==maximum_ind:
            left_min=kama[max(last_top_ind,last_bot_ind)]
        else:
            left_min=np.min(kama[max(last_top_ind,last_bot_ind):maximum_ind])
            
        if maximum_ind==ii:
            right_min=kama[ii]
        else:
            right_min=np.min(kama[maximum_ind:ii]) 

        minimum=np.min(kama[max(last_top_ind,last_bot_ind):ii])
        minimum_ind=max(last_top_ind,last_bot_ind)+np.argmin(kama[max(last_top_ind,last_bot_ind):ii])
        
        #some checks without interest to avoid error
        if max(last_top_ind,last_bot_ind)==minimum_ind:
            left_max=kama[max(last_top_ind,last_bot_ind)]
        else:
            left_max=np.max(kama[max(last_top_ind,last_bot_ind):minimum_ind])
            
        if maximum_ind==ii:
            right_max=kama[ii]
        else:
            right_max=np.max(kama[minimum_ind:ii])       

        #detection major extrema
        if left_min < maximum* (1-threshold) and right_min < maximum* (1-threshold):
            if maximum_ind != last_top_ind:
                last_top_ind=maximum_ind
                macro_trend_nouncertain[ii]=1
                if ii > len(kama)-2: #for alerting
                    max_ind[ii:ii+2]=1

        if left_max > minimum* (1+threshold) and right_max > minimum* (1+threshold):
            if minimum_ind !=last_bot_ind:
                last_bot_ind=minimum_ind  
                macro_trend_nouncertain[ii]=-1
                if ii > len(kama)-2: #for alerting
                    min_ind[ii:ii+2]=1

        #definition of uncertain state
        macro_trend[ii]=macro_trend_nouncertain[ii]
        #fast answer in uncertain
        if threshold_uncertain!=0:
            if macro_trend_nouncertain[ii]==-1 and kama[ii] < maximum* (1-threshold_uncertain):
                macro_trend[ii]=0
            elif macro_trend_nouncertain[ii]==1 and kama[ii] > minimum* (1+threshold_uncertain):
                macro_trend[ii]=0
        #deadband, when we are not perfectly sure
        if deadband!=0:
            if macro_trend_nouncertain[ii]==-1 and kama[ii] < kama[minimum_ind]*(1+deadband):
                macro_trend[ii]=0
            elif macro_trend_nouncertain[ii]==1 and kama[ii] > kama[maximum_ind]*(1-deadband):
                macro_trend[ii]=0
            
    return macro_trend, min_ind, max_ind

def major_int(
        close: np.array,
        threshold: numbers.Number=0.04, 
        threshold_uncertain: numbers.Number=0, 
        deadband: numbers.Number=0.1
        )-> (np.array, int, int):
    '''
    Determine the top and bottom from the KAMA function

    Arguments
    ----------
        close: close price
        threshold: threshold to determine when there is a top or a bottom
        threshold_uncertain: threshold to determine when we are in an uncertain period
        deadband: deadband before changing the trend decision
    '''
    kama=talib.KAMA(close,timeperiod=30)

    #by kama the begin is nan
    init=None
    last_top_ind=None
    last_bot_ind=None
    for ii in range(2,len(kama)):
        if not np.isnan(kama[ii]):
            last_top_ind=ii
            last_bot_ind=ii
            init=ii+2 #needs at least 2 to make a max
            break

    return major_int_sub(kama, init, last_top_ind, last_bot_ind, threshold, threshold_uncertain, deadband)

VBTMACROTREND= vbt.IF(
     class_name='Major',
     short_name='major',
     input_names=['close'],
     param_names=['threshold', 'threshold_uncertain', 'deadband'],
     output_names=['macro_trend', 'min_ind', 'max_ind']
).with_apply_func(
     major_int, 
     takes_1d=True,  
     threshold=0.04, #optimize parameters
     threshold_uncertain=0,
     deadband=0.1
     )  
  
def major_int_prd(close: np.array,
                  threshold: numbers.Number=0.04, 
                  threshold_uncertain: numbers.Number=0, 
                  deadband: numbers.Number=0.1
                  )-> (np.array, int, int):
    '''
    Like major_int but can be forced to a certain value
    '''  
    macro_trend, min_ind, max_ind=major_int(close,threshold,threshold_uncertain,deadband)
    if _settings["FORCE_MACRO_TO"]=="bear":
        macro_trend[-1]=1 
    elif _settings["FORCE_MACRO_TO"]=="bull":
        macro_trend[-1]=-1
    elif _settings["FORCE_MACRO_TO"]=="uncertain":
        macro_trend[-1]=0  
    return macro_trend, min_ind, max_ind

VBTMACROTRENDPRD= vbt.IF(
     class_name='Major',
     short_name='major',
     input_names=['close'],
     param_names=['threshold', 'threshold_uncertain', 'deadband'],
     output_names=['macro_trend', 'min_ind', 'max_ind']
).with_apply_func(
     major_int_prd, 
     takes_1d=True,  
     threshold=0.04, #optimize parameters
     threshold_uncertain=0,
     deadband=0.1
     )     

@njit        
def macro_mode(
        temp_ent: np.array,
        temp_ex: np.array, 
        macro_trend: np.array, 
        dir_bull: str, 
        dir_bear: str, 
        dir_uncertain: str) -> (np.array, np.array, np.array, np.array):
    '''
    Translate the entries and exits in entries, exits, entries_short, exits_short depending on the direction chosen 

    Arguments
    ----------
        temp_ent: entries but without consideration of the trend
        temp_ex: exits but without consideration of the trend
        macro_trend: trend for each symbols and moment in time
        dir_bull: direction to use during bull trend
        dir_bear: direction to use during bear trend
        dir_uncertain: direction to use during uncertain trend
    '''       
    entries= np.full(temp_ent.shape, False)   
    exits= np.full(temp_ent.shape, False)   
    entries_short= np.full(temp_ent.shape, False)   
    exits_short= np.full(temp_ent.shape, False)
    temp=2
    
    for ii in range(len(temp_ent)):
        if macro_trend[ii]==-1:
            #handle the transition from one macro trend to another
            if (temp!=0 and dir_bull not in ["both", "short"] and ii!=0):
                exits_short[ii] = True
            if (temp!=0 and dir_bull not in ["both", "long"] and ii!=0):
                exits[ii] = True

            if dir_bull in ["both", "short"]:
                entries_short[ii] = temp_ex[ii]
                exits_short[ii] = temp_ent[ii] 

            if dir_bull in ["both", "long"]:
                entries[ii] = temp_ent[ii]
                exits[ii] = temp_ex[ii]
            temp=0

        elif macro_trend[ii]==1:
            #handle the transition from one macro trend to another
            if (temp!=1 and dir_bear not in ["both", "short"] and ii!=0):
                exits_short[ii] = True
            if (temp!=1 and dir_bear not in ["both", "long"] and ii!=0):
                exits[ii] = True

            if dir_bear in ["both", "short"]:
                entries_short[ii] = temp_ex[ii]
                exits_short[ii] = temp_ent[ii] 

            if dir_bear in ["both", "long"]:
                entries[ii] = temp_ent[ii]
                exits[ii] = temp_ex[ii]
            temp=1

        else:
            #handle the transition from one macro trend to another
            if (temp!=2 and dir_uncertain not in ["both", "short"] and ii!=0):
                exits_short[ii] = True
            if (temp!=2 and dir_uncertain not in ["both", "long"] and ii!=0):
                exits[ii] = True

            if dir_uncertain in ["both", "short"]:
                entries_short[ii] = temp_ex[ii]
                exits_short[ii] = temp_ent[ii] 

            if dir_uncertain in ["both", "long"]:
                entries[ii] = temp_ent[ii]
                exits[ii] = temp_ex[ii]   
            temp=2
    return entries, exits, entries_short, exits_short

VBTMACROMODE= vbt.IF(
      class_name='VBTMacromode',
      short_name='macro_mode',
      input_names=['temp_ent','temp_ex', 'macro_trend'],
      param_names=['dir_bull','dir_bear', 'dir_uncertain'],
      output_names=['entries', 'exits', 'entries_short', 'exits_short']
 ).with_apply_func(
      macro_mode, 
      takes_1d=True, 
      dir_bull="long",
      dir_bear="both", #most of the time better than short as bear trend can quickly revert
      dir_uncertain="both"
 )    
    
def vbt_macro_filter(
        ent: np.array, 
        macro_trend: np.array, 
        mode: int
        ) -> np.array: 
    '''
    restrain to the correct period the entries or exits 

    Arguments
    ----------
        ent: entries or exits without consideration of the trend
        macro_trend: trend for each symbols and moment in time
        mode: mode to select: bull/bear/uncertain
    '''   
    out=np.full(ent.shape,False)
    try:
        ind=(macro_trend[:]==mode)
        out[ind]=ent[ind] #rest is false
    except:
        print("error in vbtagreg")
        print(ent)
        print(np.shape(ent))
        return ent        
    return out

VBTMACROFILTER= vbt.IF(
     class_name='VbtMacroFilter',
     short_name='macro_filter',
     input_names=['ent', 'macro_trend'],
     param_names=['mode'],
     output_names=['out'],
).with_apply_func(
     vbt_macro_filter, 
     takes_1d=True,  
     )    

def macro_vis( macro_trend: np.array, mode_to_vis:int ):
    '''
    Function to visualize macro_mode in vbt (will put an entry/exit when the mode is entered or exited)

    Arguments
    ----------
        macro_trend: trend for each symbols and moment in time
        mode: mode to select: bull/bear/uncertain
    '''  
    entries=(macro_trend[:]==mode_to_vis)
    exits=~entries
      
    return entries, exits

VBTMACROVIS= vbt.IF(
      class_name='VBTMacroVis',
      short_name='macro_vis',
      input_names=['macro_trend'],
      param_names=['mode_to_vis'],
      output_names=['entries', 'exits']
 ).with_apply_func(
      macro_vis, 
      takes_1d=True,  
 ) 