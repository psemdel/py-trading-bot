#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 24 19:54:29 2023

@author: maxime
"""
import numbers
import vectorbtpro as vbt
import numpy as np
from opt.opt_strat import Opt as OptStrat

class Opt(OptStrat):
    '''
    to optimize the stop losses
    '''
    def calculate_pf(
            self, 
            sl: numbers.Number=None,
            **kwargs
            ):
        self.defi_ent("learn")
        self.defi_ex("learn")
        self.macro_mode("learn")
         
        if self.it_is_index:
            ret_arr=[]
        else:
            ret=0
    
        for ind in self.indexes: #CAC, DAX, NASDAQ
            pf=vbt.Portfolio.from_signals(self.data_dic[ind]["learn"], self.ents[ind],self.exs[ind],
                                          short_entries=self.ents_short[ind],
                                          short_exits=self.exs_short[ind],
                                          freq="1d",fees=self.fees,tsl_stop=sl) #,stop_exit_price="close", should be data

            if self.it_is_index:
                ret_arr.append(self.calculate_eq_ret(pf))
            else:
                ret+=self.calculate_eq_ret(pf)
    
        if self.it_is_index:
            while np.std(ret_arr)>10:
                 ii=np.argmax(ret_arr)
                 ret_arr=np.delete(ret_arr,ii,0)
          
            ret=np.mean(ret_arr)
    
        trades =len(pf.get_trades().records_arr)
        del pf
          
        if ret> self.best_ret and trades>50:
            self.best_ret=ret
            if sl is None:
                self.best_sl=0
            else:
                self.best_sl=sl
    
    def perf(self):
        '''
        Main fonction to optimize a strategy
        '''
        self.calc_arrs=self.predef()
        self.best_ret=self.init_threshold
        #self.calculate_pf()

        for ii in range(1,30):#30
            self.calculate_pf(sl=0.005*ii)

        print("best sl: "+str(self.best_sl) + " score: "+str(self.best_ret))
        self.log("best sl: "+str(self.best_sl) + " score: "+str(self.best_ret))
