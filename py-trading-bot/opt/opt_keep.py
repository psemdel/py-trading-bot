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

        
    def calculate_pf_sub(self,dic):
        pf_dic={}   
        self.defi_ent(dic)
        self.defi_ex(dic)
        self.macro_mode(dic)

        for ind in self.indexes: #CAC, DAX, NASDAQ
            self.tested_arrs=[] #reset after each loop
            
            #RetardMacro has no underlying
            if not self.initiated:
                self.pr[ind].close=self.close_dic[ind][dic]
                self.pr[ind].run()

            i=self.exs[ind].index #to filter by total/learn/check
            self.ents[ind]=self.pr[ind].exits.loc[i] #to be checked that it can only buy one...

            pf_dic[ind]=vbt.Portfolio.from_signals(self.data_dic[ind][dic],
                                          self.ents[ind],
                                          self.exs[ind],
                                          freq="1d",fees=self.fees,
                                          call_seq='auto',cash_sharing=True
                                          ) #stop_exit_price="close"
            self.calculate_eq_ret(pf_dic[ind],ind)
            
        self.initiated=True
            
        return pf_dic        