#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 24 19:54:29 2023

@author: maxime
"""

import vectorbtpro as vbt
#from opt.opt_main import OptMain
import numpy as np
from opt.opt_strat import Opt as OptStrat
from opt.opt_main import log

#to optimize the stop losses
class Opt(OptStrat):
    def calculate_pf(self, **kwargs):
        self.defi_ent()
        self.defi_ex()
        self.macro_mode()
         
        if self.index:
            ret_arr=[]
        else:
            ret=0
    
        for ind in self.indexes: #CAC, DAX, NASDAQ
            if kwargs.get("sl"):
                pf=vbt.Portfolio.from_signals(self.close_dic[ind], self.ents[ind],self.exs[ind],
                                              short_entries=self.ents_short[ind],
                                              short_exits=self.exs_short[ind],
                                              freq="1d",fees=self.fees,tsl_stop=kwargs.get("sl"),stop_exit_price="close")
            else:
                pf=vbt.Portfolio.from_signals(self.close_dic[ind], self.ents[ind],self.exs[ind],
                                              short_entries=self.ents_short[ind],
                                             short_exits=self.exs_short[ind],
                                               freq="1d",fees=self.fees)
             
            if self.index:
                ret_arr.append(self.calculate_eq_ret(pf))
            else:
                ret+=self.calculate_eq_ret(pf)
    
        if self.index:
            while np.std(ret_arr)>10:
                 ii=np.argmax(ret_arr)
                 ret_arr=np.delete(ret_arr,ii,0)
          
            ret=np.mean(ret_arr)
    
        trades =len(pf.get_trades().records_arr)
        del pf

          
        if ret> self.best_ret and trades>50:
            self.best_ret=ret
            self.best_sl=kwargs.get("sl",0)
    
    def perf(self):
        self.calc_arrs=self.predef()
        self.best_ret=self.init_threshold
        #self.calculate_pf()

        for ii in range(1,30):#30
            self.calculate_pf(sl=0.005*ii)

        print("best sl: "+str(self.best_sl) + " score: "+str(self.best_ret))
        log("best sl: "+str(self.best_sl) + " score: "+str(self.best_ret))
