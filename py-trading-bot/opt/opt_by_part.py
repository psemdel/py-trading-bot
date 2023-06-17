#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May 11 21:37:29 2023

@author: maxime
"""

from opt.opt_strat import Opt as OptStrat
import numpy as np
from opt.opt_main import log
import vectorbtpro as vbt

#Try to optimize the strategy depending on the performance of the different symbols on a predefined strategy

class Opt(OptStrat):
    def __init__(self,period,**kwargs):
        if not kwargs.get("no_reinit",False):
            super().__init__(period,split_learn_train="time",**kwargs)
            
        self.number_of_parts=kwargs.get("number_of_parts",10)
        self.starting_part=kwargs.get("starting_part",0) #to resume interrupted calc
        self.defi_i("learn")
        
        if kwargs.get("only_test",False):
            self.calc_arrs=self.predef() #to determine the original splitting of the symbols
            
            self.a_dicho={}
            for key in ["bull","bear","uncertain"]:
                self.a_dicho[key]=kwargs.get("dicho_"+key)
            self.calc_arrs_dicho=self.predef(dicho=True)
        else:
            self.perf()
        
        self.defi_ent("learn")
        self.defi_ex("learn")
        self.macro_mode("learn")

        self.selected_symbols={}
        perf_sorted={}
        sorted_symbols={}
        for ind in self.indexes:
            self.selected_symbols[ind]={}

        #calculation on the total
        for ind in self.indexes: #CAC, DAX, NASDAQ
            pf=vbt.Portfolio.from_signals(self.close_dic[ind]["learn"],#date needed for sl or tsl
                                          self.ents[ind],
                                          self.exs[ind],
                                          short_entries=self.ents_short[ind],
                                          short_exits=self.exs_short[ind],
                                          freq="1d",
                                          fees=self.fees,
                                          tsl_stop=self.tsl,
                                          sl_stop=self.sl,
                                          ) #stop_exit_price="close"
            self.symbols_append(pf,ind)
            perf_sorted[ind]=sorted(self.selected_symbols[ind].items(),key=lambda tup: tup[1],reverse=True)
            sorted_symbols[ind]=[s[0] for s in perf_sorted[ind]]

        self.tested_arrs=[]
        self.split_in_part(sorted_symbols=sorted_symbols,split="symbol",origin_dic="learn",**kwargs)
        self.split_in_part(sorted_symbols=sorted_symbols,split="symbol",origin_dic="test",**kwargs)
        
        if kwargs.get("only_test",False):
            self.calc_arrs=self.calc_arrs_dicho
        
    def outer_perf(self):
        for ii in range(self.starting_part,self.number_of_parts):
            log("Outer loop: "+str(ii),pr=True)

            for ind in self.indexes:
                log("symbols optimized: " + str(self.close_dic[ind]["learn_part_"+str(ii)].columns))

            self.defi_i("learn_part_"+str(ii))
            self.init_best_arr() #reinit
            self.perf(dic="learn_part_"+str(ii),dic_test="test_part_"+str(ii))

    def symbols_append(self,pf,ind):
        p=np.multiply(pf.get_total_return()-pf.total_market_return,1/abs(pf.total_market_return))
        for ii in range(len(p)):
            self.selected_symbols[ind][p.index[ii][-1]]=p.values[ii]





        
        
        

