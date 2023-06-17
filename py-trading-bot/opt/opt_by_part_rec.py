#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jun  3 17:39:41 2023

@author: maxime
"""

from opt.opt_by_part import Opt as OptByPart
import numpy as np
from opt.opt_main import log
import vectorbtpro as vbt

#Try to optimize the strategy depending on the performance of the different symbols on a predefined strategy
#The process strategy to sort the symbols is regenerated each time the set of symbols changes

class OptRecursive(OptByPart):
    def __init__(self,period,**kwargs):
        super().__init__(period,**kwargs)
        self.period=period
        self.total_number_of_parts=kwargs.get("number_of_parts",10)
        self.test_window_start_fixed=self.test_window_start
        
    def perf_recursion(self,**kwargs):
        #origin_dic=kwargs.get("origin_dic","total")
        
        #remove last symbols
        for ii in range(1,self.total_number_of_parts):
            for ind in self.indexes:
                col_to_remove=self.close_dic[ind]["learn_part_0"].columns

                for dic in ["total","learn","test"]:
                    for d in ["close","open","low","high"]:
                        getattr(self,d+"_dic")[ind][dic]=getattr(self,d+"_dic")[ind][dic].drop(col_to_remove,axis=1)
                    self.macro_trend[ind][dic]=self.macro_trend[ind][dic].drop(col_to_remove,axis=1)
                    
            kwargs.update(number_of_parts=self.number_of_parts-1)
            super().__init__(self.period,test_window_start=self.test_window_start_fixed,no_reinit=True, **kwargs) 
            self.outer_perf(0) #always 0, we handle the first one

    def outer_perf(self,ii):
        log("Outer loop: "+str(ii),pr=True)

        for ind in self.indexes:
            log("symbols optimized: " + str(self.close_dic[ind]["learn_part_"+str(ii)].columns))

        self.defi_i("learn_part_"+str(ii))
        self.init_best_arr() #reinit
        self.perf(dic="learn_part_"+str(ii),dic_test="test_part_"+str(ii))