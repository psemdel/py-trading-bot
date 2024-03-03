#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 16 08:27:34 2022

@author: maxime
"""
import numbers
import vectorbtpro as vbt
import talib
from talib.abstract import *
import numpy as np
from numba import njit

import logging
logger = logging.getLogger(__name__)

from core import constants

from trading_bot.settings import _settings

### General functions ###
@njit 
def rel_dif(n: numbers.Number,d: numbers.Number): #for instance to calculate distance between MA and signal
    '''
    Perform a division
    '''
    if d==0 or np.isnan(n) or np.isnan(d):
        return 0
    else:
        return round(n/d-1,4)

def func_name_to_res(
        f_name: str, 
        open_: np.array, 
        high: np.array, 
        low: np.array, 
        close: np.array,
        volume: np.array= None
        ):
    '''
    Wrapper for talib functions

    Arguments
    ----------
        f_name: name of the function in indicators
        open_: open prices
        high: high prices
        low: low prices
        close: close prices
    '''
    try:
        if f_name[-4:]=="_INV":
            f_name=f_name[:-4]
            inputs={
                'open': open_,
                'high': low, #error that makes different patterns actually
                'low': high,
                'close': close,
            }        
        else:
            if volume is None:
                inputs={
                    'open': open_,
                    'high': high,
                    'low': low,
                    'close': close,
                }
            else:
                inputs={
                    'open': open_,
                    'high': high,
                    'low': low,
                    'close': close,
                    'volume': volume
                }                

        f=getattr(talib.abstract,f_name)
        return f(inputs)
    
    except Exception as e:
        logger.error(e, stack_info=True, exc_info=True)   
        pass 

'''
Or function
'''
VBTOR= vbt.IF(
     class_name='VbtOr',
     short_name='or',
     input_names=['b1', 'b2'],
     output_names=['out'],
).with_apply_func(
     np.logical_or, 
     takes_1d=True,  
     )
   
'''
And function
'''    
VBTAND= vbt.IF(
     class_name='VbtOr',
     short_name='or',
     input_names=['b1', 'b2'],
     output_names=['out'],
).with_apply_func(
     np.logical_and, 
     takes_1d=True,  
     )
    
'''
Super trend function

See definition of this function.
'''     
def get_basic_bands(
        med_price: numbers.Number, 
        atr: numbers.Number,
        multiplier: numbers.Number
        )-> (numbers.Number, numbers.Number):
    matr = multiplier * atr
    upper = med_price + matr
    lower = med_price - matr
    return upper, lower

@njit
def get_final_bands_nb(
        close: np.array, 
        upper: np.array, 
        lower: np.array
        ) -> (np.array, np.array, np.array, np.array, np.array, np.array, np.array): 
    trend = np.full(close.shape, np.nan)  

    dir_ = np.full(close.shape, 1)
    long=  np.full(close.shape, np.nan)
    short = np.full(close.shape, np.nan)
    entries=  np.full(close.shape, False)
    exits = np.full(close.shape, False) #needed if combined with other methods.
    duration=np.full(close.shape, 0)

    for i in range(1, close.shape[0]):
         if close[i] > upper[i - 1]:  
             dir_[i] = 1
             entries[i]=True
             duration[i]=0
         elif close[i] < lower[i - 1]:
             dir_[i] = -1
             exits[i]=True
             duration[i]=0
         else:
             dir_[i] = dir_[i - 1]
             if dir_[i] > 0 and lower[i] < lower[i - 1]:
                 lower[i] = lower[i - 1]
                 duration[i]=duration[i-1]-1
             if dir_[i] < 0 and upper[i] > upper[i - 1]:
                 upper[i] = upper[i - 1]
                 duration[i]=duration[i-1] + 1
 
         if dir_[i] > 0:
             trend[i] = long[i] = lower[i]
         else:
             trend[i] = short[i] = upper[i]
             
    return trend, dir_, long, short, entries, exits, duration

def faster_supertrend(
        high: np.array, 
        low: np.array, 
        close: np.array, 
        multiplier=3
        )-> (np.array, np.array, np.array, np.array, np.array, np.array):
    medprice=talib.MEDPRICE(high, low)
    atr=talib.ATR(high, low, close)

    upper, lower = get_basic_bands(medprice, atr, multiplier)
    return get_final_bands_nb(close, upper, lower)

VBTSUPERTREND = vbt.IF(
     class_name='SuperTrend',
     short_name='st',
     input_names=['high', 'low', 'close'],
     param_names=['multiplier'],
     output_names=['supert', 'superd', 'superl', 'supers','entries','exits','duration']
).with_apply_func(
     faster_supertrend, 
     takes_1d=True,  
     multiplier=3)

'''
Strategy that base on the crossing of the MA function and the supertrend

Arguments
----------
    high: high prices
    low: low prices
    close: close prices
'''     
def supertrend_ma(
        high: np.array,
        low: np.array,
        close: np.array
        ) -> (np.array, np.array):
    fast_ma = vbt.MA.run(close, 5)
    slow_ma = vbt.MA.run(close, 15)
    ent =  fast_ma.ma_crossed_above(slow_ma)
    ex = fast_ma.ma_crossed_below(slow_ma)
    _, _, _, supers, _, _, _=faster_supertrend(high, low, close)

    for ii in range(len(supers)):
        if not np.isnan(supers[ii]):
            ex[ii]=True #ex or ex2 
    
    return ent, ex

VBTSUPERTRENDMA = vbt.IF(
     class_name='SuperTrendMa',
     short_name='st_ma',
     input_names=['high', 'low', 'close'],
     output_names=['entries', 'exits']
).with_apply_func(
     supertrend_ma, 
     takes_1d=True,  
     )
 
'''
Strategy where the exit and entries depends on the crossing of moving average with 5 and 15 days period

Arguments
----------
    close: close prices
'''
def ma(close: np.array)-> (np.array, np.array):    
    fast_ma = vbt.MA.run(close, 5)
    slow_ma = vbt.MA.run(close, 15)
        
    entries =  fast_ma.ma_crossed_above(slow_ma)
    exits = fast_ma.ma_crossed_below(slow_ma)
    fast_over_slow =  fast_ma.ma_above(slow_ma)
    
    return entries, exits, fast_over_slow
 
VBTMA = vbt.IF( #just to keep everything the same shape... but useless here
     class_name='MA',
     short_name='ma',
     input_names=['close'],
     output_names=['entries', 'exits','fast_over_slow']
).with_apply_func(
     ma, 
     takes_1d=True,  
     )

'''
Strategy that combines entry and exits based on KAMA extrema on one side, and on the crossing of STOCH value of predefined thresholds

Arguments
----------
    high: high prices
    low: low prices
    close: close prices
'''
@njit
def stoch_kama_sub(
        close: np.array,
        top_ext: np.array,
        ex_stoch: np.array,
        bot_ext: np.array,
        ent_stoch: np.array
        )-> (np.array, np.array):
    entries= np.full(close.shape, False)
    exits= np.full(close.shape, False)       
    
    for ii in range(len(close)):
        if top_ext[ii] or ex_stoch[ii]:
            exits[ii]=True 
        if bot_ext[ii] or ent_stoch[ii]:
            entries[ii]=True
    return entries, exits
            
def stoch_kama(
        high: np.array,
        low: np.array,
        close: np.array
        )->(np.array, np.array, np.array, np.array, np.array, np.array, np.array):
    
    _, direction, top_ext, bot_ext=kama_f(close)

    stoch = vbt.STOCH.run(high,low,close)
    ent_stoch =  stoch.slow_k_crossed_below(_settings["STOCH_LL"])
    ex_stoch  =stoch.slow_k_crossed_below(_settings["STOCH_LU"])
    
    entries, exits=stoch_kama_sub(close, top_ext, ex_stoch.values, bot_ext, ent_stoch.values)

    return entries, exits, ent_stoch, ex_stoch, bot_ext, top_ext, stoch.slow_k, direction  

VBTSTOCHKAMA = vbt.IF(
     class_name='StochKama',
     short_name='stochkama',
     input_names=['high', 'low', 'close'],
     output_names=['entries', 'exits','entries_stoch', 'exits_stoch',
                   'entries_kama', 'exits_kama','stoch','direction']
).with_apply_func(
     stoch_kama, 
     takes_1d=True,  
     )

'''
Strategy that perform entry and exits based on KAMA extrema
It also define the direction, depending on those extrema

Arguments
----------
    close: close prices
'''    
def kama_f(close: np.array) -> (np.array, np.array, np.array, np.array):
    kama=talib.KAMA(close,timeperiod=30)
    return kama_f_sub(kama)
    
@njit
def kama_f_sub(kama: np.array) -> (np.array, np.array, np.array, np.array):
    direction = np.full(kama.shape, np.nan)
    top_ext= np.full(kama.shape, False)
    bot_ext= np.full(kama.shape, False)
    
    for ii in range(len(kama)):
        if ii==0 or kama[ii]>=kama[ii-1]:
            direction[ii]=-1
        else:
            direction[ii]=1
            
        if ii>=2: 
            if kama[ii-1]>kama[ii-2] and kama[ii-1]>kama[ii]:
                top_ext[ii]=True 
                #note that the extremum is in ii-1, 
                #but setting it to ii would lead to backtesting "looking into the future"
            if kama[ii-1]<kama[ii-2] and kama[ii-1]<kama[ii]:
                bot_ext[ii]=True

    return kama, direction, top_ext, bot_ext

VBTKAMA = vbt.IF(
     class_name='VBTKama',
     short_name='kama',
     input_names=['close'],
     output_names=['kama','direction', 'top_ext', 'bot_ext']
).with_apply_func(
     kama_f, 
     takes_1d=True,  
)

'''
Set all points to false

Arguments
----------
    close: close prices
''' 
def false_1d(close: np.array)-> np.array:
    ent= np.full(close.shape, False)
    return ent
        
VBTFALSE = vbt.IF(
      class_name='VBTFalse',
      short_name='false',
      input_names=['close'],
      output_names=["out"]
 ).with_apply_func(
      false_1d, 
      takes_1d=True,  
 )  
     
'''
Forbid any entry if the trend is bear

Arguments
----------
    close: close prices
''' 
def very_bear_1d(close:np.array)-> (np.array, np.array):
    ent= np.full(close.shape, False)
    ex= np.full(close.shape, True)   
    return ent, ex
        
VBTVERYBEAR = vbt.IF(
      class_name='VBTVeryBear',
      short_name='very_bear',
      input_names=['close'],
      output_names=["entries","exits"]
 ).with_apply_func(
      very_bear_1d, 
      takes_1d=True,  
 )       

'''
Forbid any exit if the trend is bull 

Arguments
----------
    close: close prices
'''      
def very_bull_1d(close: np.array)-> (np.array, np.array):
    ent= np.full(close.shape, True)
    ex= np.full(close.shape, False)   
    return ent, ex
    
VBTVERYBULL = vbt.IF(
      class_name='VBTVeryBull',
      short_name='very_bull',
      input_names=['close'],
      output_names=["entries","exits"]
 ).with_apply_func(
      very_bull_1d, 
      takes_1d=True,  
 )      
    
'''
Calculate the duration of a trend based on the KAMA
So if the KAMA of an action decreases since 20 days, it will return 20

Arguments
----------
    close: close prices
'''        
def kama_trend(close: np.array)->(np.array, np.array):
    kama=talib.KAMA(close,timeperiod=30)
    return kama_trend_sub(kama)
    
@njit    
def kama_trend_sub(kama: np.array)->(np.array, np.array): 
    trend=np.full(kama.shape, 0.0)
    duration=np.full(kama.shape, 0.0)

    for ii in range(len(kama)):
        if ii==0:
            trend[ii]=0
            duration[ii]=0
        else:
            if np.isnan(kama[ii]):
                trend[ii]=0 #undefined
                delta=0
            else:
                if kama[ii]>kama[ii-1]:
                    trend[ii]=-1
                    delta=-1
                else:
                    trend[ii]=1
                    delta=1
            if trend[ii]==trend[ii-1]:
                duration[ii]=duration[ii-1]+delta
            else:
                duration[ii]=0

    return trend, duration
VBTKAMATREND = vbt.IF(
      class_name='VBTKamaTrend',
      short_name='kama_trend',
      input_names=['close'],
      output_names=['trend','duration']
 ).with_apply_func(
      kama_trend, 
      takes_1d=True,  
 )  
    
    
  
     
'''
Calculate entry and exit signals based on candlelight patterns
Calculate for a list of patterns and give the result for all

Arguments
----------
    open_: open prices
    high: high prices
    low: low prices
    close: close prices
    light: reduce the number of patterns considered
'''       
def pattern(
        open_: np.array,
        high: np.array,
        low: np.array,
        close: np.array,
        )-> (np.array, np.array): 
    

    arr=[constants.BEAR_PATTERNS, constants.BULL_PATTERNS]
    entries=np.full(close.shape, False)
    exits=np.full(close.shape, False)

    for kk, pat in enumerate(arr):
        for func_name in pat:
            res=func_name_to_res(func_name, open_, high, low, close)
            if type(pat[func_name])==int:
                values=[pat[func_name]]
            else:
                values=pat[func_name]
            
            for v in values:
                if kk==0:
                    exits=np.logical_or((res==v), exits)
                else:
                    entries=np.logical_or((res==v), entries)
                    
    return entries, exits
                    
VBTPATTERN = vbt.IF(
      class_name='VBTPattern',
      short_name='pattern',
      input_names=['open_','high', 'low', 'close'],
      output_names=['entries','exits']
 ).with_apply_func(
      pattern, 
      takes_1d=True,  
 )  
      
   
'''
For only one pattern

Arguments
----------
    open_: open prices
    high: high prices
    low: low prices
    close: close prices
    f_name: name of the function in indicators
    ent_or_ex: the function should return entries or exit
'''  
def pattern_one(
        open_: np.array,
        high: np.array,
        low: np.array,
        close: np.array,
        f_name: str,
        ent_or_ex: str,
        second: bool=False
        ):
    try:

        if ent_or_ex=="ent":
            arr=constants.BULL_PATTERNS
        else:
            arr=constants.BEAR_PATTERNS
        
        res=func_name_to_res(f_name, open_, high, low, close)
        
        if f_name not in arr:
            raise ValueError(f_name +" not in the BEAR_PATTERNS or BULL_PATTERNS defined in constants")
        
        if type(arr[f_name])==int:
            return res==arr[f_name]
        else:
            entex=np.full(close.shape, False)
            for v in arr[f_name]:
                entex=np.logical_or((res==v), entex)
            return entex

    except Exception as e:
        logger.error(e, stack_info=True, exc_info=True)  
        pass 
                    
VBTPATTERNONE = vbt.IF(
      class_name='VBTPatternOne',
      short_name='pattern_one',
      input_names=['open_','high', 'low', 'close'],
      param_names=['func_name','ent_or_ex'],
      output_names=['out']
 ).with_apply_func(
      pattern_one, 
      takes_1d=True,  
 )       
 
'''
Bbands trend

Determine the strenght of a trend based on the value of the bbands bandwidth
The direction is determined by kama_f
This trend tends to work in bang-bang alterning between -10 and 10

Arguments
----------
    close: close prices
''' 
def bbands_trend(close: np.array) -> (np.array, np.array, np.array):
    kama, direction, _, _=kama_f(close)
    bbands=vbt.BBANDS.run(close)
    
    trend=bbands_trend_sub(close,bbands.bandwidth, direction)
    
    return trend, kama, bbands.bandwidth

def bbands_trend_sub(
        close: np.array,
        bb_bw: np.array,
        direction: np.array
        )->np.array:
    trend= np.full(close.shape, 0.0)  
    for ii in range(len(close)):
        if bb_bw[ii]>0.1:
            if direction[ii]==1: #kama_dic.
                trend[ii]=10  
            else:
                trend[ii]=-10
    return trend

VBTBBANDSTREND = vbt.IF(
      class_name='VBTBbandsTrend',
      short_name='bbands_trend',
      input_names=['close'],
      output_names=['trend','kama','bb_bw']
 ).with_apply_func(
      bbands_trend, 
      takes_1d=True,  
 ) 

'''
Bbands MACD trend

Determine the strenght of a trend based on the value of the bbands bandwidth and the MACD
This trend is more smooth than the previous one, however the result on the strategy is not always better

Arguments
----------
    close: close prices
''' 
def macd_trend_sub(
        close: np.array,
        macd: np.array,
        hist: np.array,
        lim1: numbers.Number,
        lim2: numbers.Number
        )-> np.array:
    trend= np.full(close.shape, 0.0)  
     
    for ii in range(len(macd)):
        t=trend[ii]
        e=macd[ii]
        h=hist[ii]

        if e>lim1:
            t-=1
            if e>lim2 and h>-lim2:
                t-=1
            if e>lim2 and h>lim1:
                t-=1
        elif e<-lim1:
            t+=1
            if e<-lim2 and h<lim2:
                t+=1
            if e<-lim2 and h<-lim1:
                t+=1 
        trend[ii]=t
    return trend 

def macd_trend_sub2(
        close: np.array,
        bb_bw: np.array,
        direction: np.array
        )-> np.array:   

    trend= np.full(close.shape, 0.0)  
    bband_lim=_settings["BBAND_THRESHOLD"]
    trend_dir_arr=0
    trend_dir_arr_dim=0 #append to table perf very bad so we make a work around

    for ii in range(1,len(bb_bw)):     
        e=bb_bw[ii]   
        e1=bb_bw[ii-1]
        d=direction[ii]
        t=0
        
        #0.1 is a bit low, 0.15 a bit high
        if e>bband_lim and e>e1:
            #avoid reversal from extreme bear to extreme bull without sense
            #Determine the initial direction on 4 first days
            if trend_dir_arr_dim<5:
                trend_dir_arr+=d
                trend_dir_arr_dim+=1
   
            if trend_dir_arr>0 and d==1:
                t=10
            elif trend_dir_arr<=0 and d==-1:
                t=-10
                 
        if e<bband_lim: #reset
            trend_dir_arr=0
            trend_dir_arr_dim=0
        if t!=0:
            trend[ii]=t
    return trend  
              
@njit 
def trend_or(
        trend1: np.array,
        trend2: np.array
        )-> np.array:
    for ii in range(len(trend1)):
        if trend2[ii]!=0:
            trend1[ii]=trend2[ii]
    return trend1

def macdbb_trend(close: np.array)-> (np.array, np.array, np.array):
    #settings
    factor=960/(close[0]+close[-1])
    lim1=1/factor
    lim2=2*lim1
    
    macd=vbt.MACD.run(close, macd_wtype='simple',signal_wtype='simple')
    kama, direction, _, _=kama_f(close)
    bbands=vbt.BBANDS.run(close)
    #norming
    trend1=macd_trend_sub(close,macd.macd, macd.hist, lim1, lim2)
    trend2=macd_trend_sub2(close, bbands.bandwidth, direction)
    trend=trend_or(trend1, trend2)

    return trend, kama, bbands.bandwidth
      
VBTMACDBBTREND = vbt.IF(
      class_name='VBTMACDBbandsTrend',
      short_name='macd_bb_trend',
      input_names=['close'],
      output_names=['trend','kama','bb_bw']
 ).with_apply_func(
      macdbb_trend, 
      takes_1d=True,  
 ) 
        
'''
Grow

Calculate the grow of an action over past period

Arguments
----------
    close: close prices
''' 
@njit 
def grow_sub(
        close: np.array,
        dis: numbers.Number
        )-> np.array:
    res=np.full(close.shape, 0.0)
    #ii=len(close)-1    #we only need the last
    for ii in range(len(close)): 
        if ii<dis:
            res[ii]=rel_dif(close[ii],close[0])*100
        else:
            res[ii]=rel_dif(close[ii],close[ii-dis])*100
    return res

def grow(
        close: np.array,
        distance: int=50,
        ma: bool=False,
        dema: bool=False
        )-> np.array:
    dis=min(distance,len(close)-1)
    
    if ma:
        close=talib.MA(close, timeperiod=30, matype=0)
    elif dema:
        close=talib.DEMA(close, timeperiod=30)

    return grow_sub(close,dis)

VBTGROW = vbt.IF(
      class_name='VBTGrow',
      short_name='vbt_grow',
      input_names=['close',],
      param_names=['distance','ma','dema'],
      output_names=["out"]
 ).with_apply_func(
      grow, 
      distance=50,
      ma=False,
      dema=False,
      takes_1d=True,  
 ) 

'''
Divergence

Calculate the difference between variation of an action and the index  

Arguments
----------
    close: close prices
'''        
@njit
def divergence_f_sub(
        close: np.array,
        close_ind: np.array
        )-> np.array:
    out= np.full(close.shape, 0.0)

    for ii in range(2,len(close)):
        if np.isnan(close[ii]) or np.isnan(close[ii-1]) or np.isnan(close_ind[ii-1]):
            out[ii]=0
        else:
            p1=close[ii]/close[ii-1]
            p1_ind=close_ind[ii]/close_ind[ii-1]
            out[ii]=p1-p1_ind
        
    return out

def divergence_f(
        close: np.array,
        close_ind: np.array
        )-> np.array:
    window=15
    ma = vbt.MA.run(close, window).ma
    ma_ind = vbt.MA.run(close_ind, window).ma
    
    return divergence_f_sub(ma.values,ma_ind.values) 

VBTDIVERGENCE = vbt.IF(
      class_name='VBTDivergence',
      short_name='divergence',
      input_names=['close','close_ind'],
      output_names=['out']
 ).with_apply_func(
      divergence_f, 
      takes_1d=True,  
 ) 
     
'''
Multiply and array by an entries array

Arguments
----------
    ent: entries
    k: 1 or 0
'''  
@njit     
def sum_ent(
        ent: np.array,
        k: int
        )-> np.array:
    return np.multiply(k,ent)

VBTSUM = vbt.IF(
      class_name='VBTSUM',
      short_name='vbt_sum',
      input_names=['ent'],
      param_names=['k'],
      output_names=["out"]
 ).with_apply_func(
      sum_ent, 
      takes_1d=True,  
 )      

@njit 
def min_max_sub(
        close: np.array,
        distance: numbers.Number,
        )-> np.array:
    minimum=np.full(close.shape, 0.0)
    maximum=np.full(close.shape, 0.0)
    for ii in range(len(close)-1):
        maximum[ii]=rel_dif(close[ii+1:ii+distance].max(),close[ii])*100
        minimum[ii]=rel_dif(close[ii+1:ii+distance].min(),close[ii])*100
        
    return minimum, maximum

VBTMINMAX = vbt.IF(
      class_name='VBTMinMax',
      short_name='vbt_min_max',
      input_names=['close'],
      param_names=['distance'],
      output_names=["minimum","maximum"]
 ).with_apply_func(
      min_max_sub, 
      distance=30,
      takes_1d=True,  
 ) 
     
@njit
def support_resistance_sub(
        kama: np.array, 
        threshold: numbers.Number, 
        )-> (np.array, np.array):
    '''
    Re-use the algorithm of major_int_sub to determine the distance from support and resistance
    Use the top and bottom from the KAMA function
    
    Note: we could maybe go faster by starting now and going backward, but I fear mistake

    Arguments
    ----------
        kama: smoothed price (KAMA method)
        threshold: threshold to determine when there is a top or a bottom
        last_v: last price
    '''
    init=len(kama[np.isnan(kama)])+2
    last_top_ind=last_bot_ind=init-2
    last_bot_ind=init-2
    last_top_v=last_bot_v=0
    pu_resistance= np.full(kama.shape, 0.0)
    pu_support= np.full(kama.shape, 0.0)

    #value max, value min, distance from max, distance from min
    for ii in range(init,len(kama)):
        #since last extrema
        last_extrema_ind=max(last_top_ind,last_bot_ind)
        maximum=np.max(kama[last_extrema_ind:ii])
        maximum_ind=last_extrema_ind+np.argmax(kama[last_extrema_ind:ii])

        #some checks without interest to avoid error
        if last_extrema_ind==maximum_ind:
            left_min=kama[last_extrema_ind]
        else:
            left_min=np.min(kama[last_extrema_ind:maximum_ind])
            
        if maximum_ind==ii:
            right_min=kama[ii]
        else:
            right_min=np.min(kama[maximum_ind:ii]) 

        minimum=np.min(kama[last_extrema_ind:ii])
        minimum_ind=last_extrema_ind+np.argmin(kama[last_extrema_ind:ii])
        
        #some checks without interest to avoid error
        if last_extrema_ind==minimum_ind:
            left_max=kama[last_extrema_ind]
        else:
            left_max=np.max(kama[last_extrema_ind:minimum_ind])
            
        if maximum_ind==ii:
            right_max=kama[ii]
        else:
            right_max=np.max(kama[minimum_ind:ii])       

        #detection major extrema
        if left_min < maximum* (1-threshold) and right_min < maximum* (1-threshold):
            if maximum_ind != last_top_ind:
                last_top_ind=maximum_ind
                last_top_v=maximum
        if left_max > minimum* (1+threshold) and right_max > minimum* (1+threshold):
            if minimum_ind !=last_bot_ind:
                last_bot_ind=minimum_ind  
                last_bot_v=minimum

        if last_top_v!=0:
            pu_resistance[ii]=kama[ii]/last_top_v #resistance reached by 1
    
        if last_bot_v!=0:
            pu_support[ii]=kama[ii]/last_bot_v #support reached by 1

    return pu_resistance, pu_support

def support_resistance(
        close: np.array,
        threshold: numbers.Number
        )-> (np.array, np.array):
    '''
    Determine the top and bottom from the KAMA function

    Arguments
    ----------
        close: close price
        threshold: threshold to determine when there is a top or a bottom
    '''
    kama=talib.KAMA(close,timeperiod=30)
    return support_resistance_sub(kama, threshold)  

VBTSUPPORTRESISTANCE = vbt.IF(
      class_name='VBTSupportResistance',
      short_name='vbt_support_resistance',
      input_names=['close'],
      param_names=['threshold'],
      output_names=["pu_resistance","pu_support"]
 ).with_apply_func(
      support_resistance, 
      threshold=0.03,
      takes_1d=True,  
 ) 