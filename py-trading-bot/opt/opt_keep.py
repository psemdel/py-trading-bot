#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 23 21:46:42 2023

@author: maxime
"""

from opt.opt_presel import Opt as OptPresel
import vectorbtpro as vbt
import numpy as np

class Opt(OptPresel):
    def __init__(
            self,
            period: str,
            filename:str="keep",
            **kwargs):
        super().__init__("PreselRetardMacro", period,filename=filename,**kwargs) 
        self.initiated=False

    #for keep the result of one presel is the entry of this presel 
    def calculate_pf_sub(self,dic):
        pf_dic={}   
        self.defi_ent("total")
        self.defi_ex("total")
        self.macro_mode("total")
        
        #here self.pr is RetardMacro
        if not self.initiated:
            for ind in self.indexes: #CAC, DAX, NASDAQ
                self.pr[ind].close=self.close_dic[ind]["total"]
                self.pr[ind].reinit() #in case the function was called ealier
                self.pr[ind].run()
            self.initiated=True
            
        for ind in self.indexes: #CAC, DAX, NASDAQ
            #restrain to size of total/learn/test
            i=self.close_dic[ind][dic].index
            self.ents[ind]=self.pr[ind].exits.loc[i] 
            self.exs[ind]=self.exs[ind].loc[i] #from ust to here
            
            pf_dic[ind]=vbt.Portfolio.from_signals(self.data_dic[ind][dic],
                                          self.ents[ind],
                                          self.exs[ind],
                                          freq="1d",fees=self.fees,
                                          call_seq='auto',
                                          cash_sharing=True
                                          ) #stop_exit_price="close"
            
            self.calculate_eq_ret(pf_dic[ind],ind)
           
        return pf_dic        