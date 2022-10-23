#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 29 20:33:22 2022

@author: maxime
"""
import vectorbtpro as vbt
import numpy as np
import talib
from numba import njit
from trading_bot.settings import FORCE_MACRO_TO

#Determine when the trend is bull/bear or uncertain in order to improve the underlying strategy or
#to determine the ideal direction (long/short/both)

@njit
def major_int_sub(kama, init, last_top_ind, last_bot_ind, threshold, threshold_uncertain, deadband):
    macro_trend_nouncertain= np.full(kama.shape, 0)
    macro_trend= np.full(kama.shape, 0)
    max_ind= np.full(kama.shape, 0)
    min_ind= np.full(kama.shape, 0)
    
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

def major_int(close,threshold=0.04, threshold_uncertain=0, deadband=0.1):
    kama=talib.KAMA(close,timeperiod=30)

    #by kama the begin is nan
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
    
def major_int_prd(close,threshold=0.04, threshold_uncertain=0, deadband=0.1):
    macro_trend, min_ind, max_ind=major_int(close,threshold,threshold_uncertain,deadband)
    if FORCE_MACRO_TO=="bear":
        macro_trend[-1]=1 
    elif FORCE_MACRO_TO=="bull":
        macro_trend[-1]=-1
    elif FORCE_MACRO_TO=="uncertain":
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

##Old one, only temporarily for comparison
def major_int_sub_old(kama):
    threshold=0.03
    ll=1-threshold
    lu=1+threshold
    window=150
    deadband=0.1

    macro_trend= np.full(kama.shape, 0)
    macro_trend_raw= np.full(kama.shape, 0)
    max_ind= np.full(kama.shape, 0)
    min_ind= np.full(kama.shape, 0)
    
    ext=[]
    ext_bot=[]
    max_arr=[]
    min_arr=[]
    
    for ii in range(2,len(kama)):
        win_start=max(0,ii-window)
        win_end=ii  #min(len(self.res),ii)
        change=0

        if not np.isnan(kama[win_start]) and not np.isnan(kama[win_end]):
            maximum=np.max(kama[win_start:win_end+1])
            ind=win_start+np.argmax(kama[win_start:win_end+1])
            
            if ind==win_start:
                local_min=kama[win_start]
            else:
                local_min=np.min(kama[win_start:ind])
           
            minimum=np.min(kama[win_start:win_end+1])
            ind_bot=win_start+np.argmin(kama[win_start:win_end+1]) 

            if ind_bot==win_start:
                local_max=kama[win_start]
            else:
                local_max=np.max(kama[win_start:ind_bot])

            if local_min<ll*maximum and kama[win_end]<ll*maximum:
                if ind not in ext:
                    ext.append(ind)
                    max_arr.append(maximum)
                    change=1
                    macro_trend_raw[ii]=1
                    if ii > len(kama)-2: #for alerting
                        max_ind[-1]=ind
            
            if local_max>lu*minimum and kama[win_end]>lu*minimum:
                if ind_bot not in ext_bot:
                    ext_bot.append(ind_bot)  
                    min_arr.append(minimum)
                    change=1
                    macro_trend_raw[ii]=-1
                    if ii > len(kama)-2: #for alerting
                        min_ind[-1]=ind
   
        if change==0:
            macro_trend_raw[ii]=macro_trend_raw[ii-1]
        macro_trend[ii]=macro_trend_raw[ii]
            
        if deadband!=0:
            #the max or min were exceeded, correction of the direction
            if macro_trend[ii]==1 and kama[ii]>max_arr[-1]:
                macro_trend[ii]=-1
            elif macro_trend[ii]==-1 and kama[ii]<min_arr[-1]:
                macro_trend[ii]=1
            #uncertain, as in a small band around the min/max
            elif macro_trend[ii]==1 and kama[ii]/max_arr[-1]>(1-deadband):
                macro_trend[ii]=0
            elif macro_trend[ii]==-1 and kama[ii]/min_arr[-1]<(1+deadband):
                macro_trend[ii]=0
   
    return macro_trend, min_ind, max_ind    

def major_int_old(close,threshold=0.04, threshold_uncertain=0, deadband=0.1):
    kama=talib.KAMA(close,timeperiod=30)
    
    return major_int_sub_old(kama)

VBTMACROTRENDOLD= vbt.IF(
     class_name='Major',
     short_name='major',
     input_names=['close'],
     output_names=['macro_trend', 'min_ind', 'max_ind']
).with_apply_func(
     major_int_old, 
     takes_1d=True,  
     ) 

#Translate the entries and exits in entries, exits, entries_short, exits_short depending on the direction chosen 
    
@njit        
def macro_mode(temp_ent,temp_ex, macro_trend, macro_trend_bull, macro_trend_bear, macro_trend_uncertain):
    entries= np.full(temp_ent.shape, False)   
    exits= np.full(temp_ent.shape, False)   
    entries_short= np.full(temp_ent.shape, False)   
    exits_short= np.full(temp_ent.shape, False)
    temp=2
    
    for ii in range(len(temp_ent)):
        if macro_trend[ii]==-1:
            if (temp!=0 and macro_trend_bull not in ["both", "short"]):
                exits_short[ii] = True
            if (temp!=0 and macro_trend_bull not in ["both", "long"]):
                exits[ii] = True

            if macro_trend_bull in ["both", "short"]:
                entries_short[ii] = temp_ex[ii]
                exits_short[ii] = temp_ent[ii] 

            if macro_trend_bull in ["both", "long"]:
                entries[ii] = temp_ent[ii]
                exits[ii] = temp_ex[ii]
            temp=0

        elif macro_trend[ii]==1:
            if (temp!=1 and macro_trend_bear not in ["both", "short"]):
                exits_short[ii] = True
            if (temp!=1 and macro_trend_bear not in ["both", "long"]):
                exits[ii] = True

            if macro_trend_bear in ["both", "short"]:
                entries_short[ii] = temp_ex[ii]
                exits_short[ii] = temp_ent[ii] 

            if macro_trend_bear in ["both", "long"]:
                entries[ii] = temp_ent[ii]
                exits[ii] = temp_ex[ii]
            temp=1

        else:
            if (temp!=2 and macro_trend_uncertain not in ["both", "short"]):
                exits_short[ii] = True
            if (temp!=2 and macro_trend_uncertain not in ["both", "long"]):
                exits[ii] = True

            if macro_trend_uncertain in ["both", "short"]:
                entries_short[ii] = temp_ex[ii]
                exits_short[ii] = temp_ent[ii] 

            if macro_trend_uncertain in ["both", "long"]:
                entries[ii] = temp_ent[ii]
                exits[ii] = temp_ex[ii]   
            temp=2
    return entries, exits, entries_short, exits_short

VBTMACROMODE= vbt.IF(
      class_name='VBTMacromode',
      short_name='macro_mode',
      input_names=['temp_ent','temp_ex', 'macro_trend'],
      param_names=['macro_trend_bull','macro_trend_bear', 'macro_trend_uncertain'],
      output_names=['entries', 'exits', 'entries_short', 'exits_short']
 ).with_apply_func(
      macro_mode, 
      takes_1d=True, 
      macro_trend_bull="long",
      macro_trend_bear="both", #most of the time better than short as bear trend can quickly revert
      macro_trend_uncertain="both"
 )    
    
    
#restrain to the correct period the entries and exits
def vbt_macro_filter(ent, macro_trend, mode): 
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

#only to visualize macro_mode
def macro_vis( macro_trend, mode_to_vis ):
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