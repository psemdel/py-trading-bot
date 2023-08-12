#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May 11 21:37:29 2023

@author: maxime
"""

from opt.opt_strat import Opt as OptStrat
import numpy as np
import vectorbtpro as vbt

class Opt(OptStrat):
    def __init__(
            self,
            period:str,
            no_reinit: bool=False,
            number_of_parts:int=10,
            starting_part: int=0,
            filename:str="by_part",
            **kwargs):
        '''
        Try to optimize the strategy depending on the performance of the different symbols on a predefined strategy
        
        Arguments
        ----------
           period: period of time in year for which we shall retrieve the data
           no_reinit: avoid reinitition of array at each round
           number_of_parts: Number of parts in which the total set must be divided
           starting_part: index of the part with which the process should start
        '''
        if not no_reinit:
            super().__init__(period,split_learn_train="time",filename=filename,**kwargs)
            
        self.number_of_parts=number_of_parts
        self.starting_part=starting_part #to resume interrupted calc
        self.defi_i("learn")
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
        
        self.split_in_part(sorted_symbols=sorted_symbols,split="symbol",origin_dic="learn",number_of_parts=number_of_parts)
        self.split_in_part(sorted_symbols=sorted_symbols,split="symbol",origin_dic="test",number_of_parts=number_of_parts)
        
    def outer_perf(self):
        '''
        Method to perform the optimization, within it, perf is called several times
        '''
        for ii in range(self.starting_part,self.number_of_parts):
            self.log("Outer loop: "+str(ii),pr=True)

            for ind in self.indexes:
                self.log("symbols optimized: " + str(self.close_dic[ind]["learn_part_"+str(ii)].columns))

            self.defi_i("learn_part_"+str(ii))
            self.init_best_arr() #reinit
            self.perf(dic="learn_part_"+str(ii),dic_test="test_part_"+str(ii))

    def symbols_append(self,pf,ind:str):
        '''
        Add the symbols to selected_symbols
        
        Arguments
        ----------
           pf: vbt portfolio
           ind: index
        '''
        p=np.multiply(pf.get_total_return()-pf.total_market_return,1/abs(pf.total_market_return))
        for ii in range(len(p)):
            self.selected_symbols[ind][p.index[ii][-1]]=p.values[ii]





        
        
        

