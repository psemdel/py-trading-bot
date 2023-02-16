#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb  6 20:11:57 2023

@author: maxime
"""
import vectorbtpro as vbt
#from opt.opt_main import OptMain
import numpy as np
import pandas as pd
from core.macro import VBTMACROTREND, VBTMACROMODE
from core import indicators as ic
import copy
from opt.opt_strat import Opt as OptStrat



def vbt_macro_filter(ent, macro_trend, mode): 
    out=np.full(ent.shape,0.0)
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
    
class Opt(OptStrat):
  
    def random(self):
        #choose randomly 0 and 1. All zeros is not accepted.
        arr=np.multiply(0.5,np.random.choice(2,self.len_ent+self.len_ex, p=[0.7, 0.3]))
        
        while np.sum(arr[0:self.len_ent] )==0 or np.sum(arr[self.len_ent:self.len_ent+self.len_ex])==0:#entries or exits must not be full 0
            arr=np.multiply(0.5,np.random.choice(2,self.len_ent+self.len_ex, p=[0.5, 0.5]))

        return arr            
    
    def variate(self, best_arrs_ret):
        step=0.5
        best_arrs_cand=[]
        best_ret_cand=self.init_threshold
            
        for nb_macro_mode in range(self.nb_macro_modes): 
            for ii in range(len(self.arrs[nb_macro_mode])):
                for add in [True, False]:
                    self.calc_arrs=copy.deepcopy(self.arrs)
                    
                    if add:
                        self.calc_arrs[nb_macro_mode][ii]+=step
                    else: 
                        self.calc_arrs[nb_macro_mode][ii]-=step
                
                    if self.calc_arrs[nb_macro_mode][ii]>1:
                        self.calc_arrs[nb_macro_mode][ii]=1.0
                    if self.calc_arrs[nb_macro_mode][ii]<0:
                        self.calc_arrs[nb_macro_mode][ii]=0.0                      

                if np.sum(self.calc_arrs[nb_macro_mode][0:self.len_ent] )!=0 and np.sum(self.calc_arrs[nb_macro_mode][self.len_ent:self.len_ent+self.len_ex])!=0:
                    best_arrs_cand, best_ret_cand=self.calculate_pf(best_arrs_cand, best_ret_cand, best_arrs_ret)

        return best_arrs_cand, best_ret_cand     
    
 
    
  #  def summarize_eq_ret(self,ret_arr):
  #      while np.std(ret_arr)>10:
  #          ii=np.argmax(ret_arr)
  #          ret_arr=np.delete(ret_arr,ii,0)
            
 #       return np.mean(ret_arr)    
 
 
"""
def defi(self,ent_or_ex):
    try:
        for ind in self.indexes: #CAC, DAX, NASDAQ
            for nb_macro_mode in range(self.nb_macro_modes): #bull, bear, uncertain
                ents_raw=None 
                calc_arr=self.calc_arrs[nb_macro_mode]

                if ent_or_ex=="ent":
                    arr=calc_arr[0:self.len_ent] 
                else:
                    arr=calc_arr[self.len_ent:self.len_ent+self.len_ex]  
            
                s=np.full(np.shape(self.all_t_ents[ind][0]),0.0)
                for ii in range(len(arr)):
                    #if arr[ii]:
                    if ent_or_ex=="ent":
                        t=self.all_t_ents[ind][ii]
                    else:
                        t=self.all_t_exs[ind][ii]
                
                    t2=ic.VBTSUM.run(t,arr=arr[ii]).out
                    #adapt the multiindex
                    multi=t2.columns
                    l=len(multi[0])

                    for ii in range(l-2,-1,-1):
                        multi=multi.droplevel(ii)
                    t2=pd.DataFrame(data=t2.values,index=t2.index,columns=multi)
                    s+=t2
                
                ents_raw=(s>0.5)
                
                if self.nb_macro_modes==1:
                    ent=ents_raw
                else:
                    if nb_macro_mode==0:
                        ent=VBTMACROFILTER.run(ents_raw,self.macro_trend[ind],-1).out
                    elif nb_macro_mode==1:
                        ents_raw=VBTMACROFILTER.run(ents_raw,self.macro_trend[ind],1).out
                        ent=ic.VBTOR.run(ent, ents_raw).out
                    else:
                        ents_raw=VBTMACROFILTER.run(ents_raw,self.macro_trend[ind],0).out
                        ent=ic.VBTOR.run(ent, ents_raw).out                    
            
            if ent_or_ex=="ent":
                self.ents[ind]=ent
            else:
                self.exs[ind]=ent
                
        #del t, arr
    except Exception as e:
        print(e)
"""