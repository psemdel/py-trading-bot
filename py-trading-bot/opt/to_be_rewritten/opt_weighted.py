#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb  6 20:11:57 2023

@author: maxime
"""
import numpy as np
import copy
from opt.opt_strat import Opt as OptStrat

'''
Generate a strategy with a strategy array which has decimal coefficients
'''
class Opt(OptStrat):
    def random(self):
        '''
        Generate a random strategy array, here with decimal values
        ''' 
        arr=np.multiply(0.5,np.random.choice(2,self.len_ent+self.len_ex, p=[0.7, 0.3]))
        
        while np.sum(arr[0:self.len_ent] )==0 or np.sum(arr[self.len_ent:self.len_ent+self.len_ex])==0:#entries or exits must not be full 0
            arr=np.multiply(0.5,np.random.choice(2,self.len_ent+self.len_ex, p=[0.5, 0.5]))

        return arr            
    
    def variate(self, best_arrs_ret: list)-> (list, list):
        '''
        Variates the array, if it is better, the new array is returned otherwise the original one
        
        Arguments
        ----------
           best_arrs_ret: array of the best returns
        ''' 
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
                    best_arrs_cand, best_ret_cand=self.calculate_pf(best_arrs_cand, best_ret_cand, best_arrs_ret,"learn")

        return best_arrs_cand, best_ret_cand     
