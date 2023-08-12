#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Aug 18 21:02:05 2022

@author: maxime
"""
from core.common import VBTfunc
from core.macro import VBTMACROTREND, VBTMACROVIS
import vectorbtpro as vbt
from vectorbtpro.utils.config import Config
import numpy as np
'''
Script to optimize the parameters of macro_trend
So to detect when the trend is bull/bear or uncertain

The optimization takes place on the actions from CAC40, DAX and Nasdaq
Criteria is that during bull the return should be positive
During bear the return should be negative
There is no criteria on uncertain which is a degree of freedom
Parameters very good on some actions but very bad for others should not be selected

The optimization algorithm calculates one point, look for the points around it and select the best one
As it can obviously lead to local maximum, the starting point is selected in a random manner
'''
import os
vbt.settings['caching']=Config(
    disable=True,
    disable_whitelist=True,
    disable_machinery=True,
    silence_warnings=False,
    register_lazily=True,
    ignore_args=[
        'jitted',
        'chunked'
    ],
    use_cached_accessors=True
)

class Opt(VBTfunc):
    def __init__(
            self,
            period: str,
            it_is_index:bool=False,
            loops:int=3,
            filename:str="macro",
            testing: bool=False,
            ):
        '''
        Arguments
        ----------
           period: period of time in year for which we shall retrieve the data
           it_is_index: if True, it will select only the index to make the optimization
           loops: maximum number of loops to be performed (to limit the total computing time before having a result)
           testing: set to True to perform unittest on the function
        '''
        self.filename=filename
        for key in ["close","open","low","high","data"]:
            setattr(self,key+"_dic",{})
        self.indexes=["CAC40", "DAX", "NASDAQ"]
        
        for ind in self.indexes:
            super().__init__(ind,period)
            
            for key in ["close","open","low","high","data"]:
                if it_is_index:
                    getattr(self,key+"_dic")[ind]=getattr(self,key+"_ind")
                else:
                    getattr(self,key+"_dic")[ind]=getattr(self,key)
        
        self.macro_trend={}
        self.tested_arrs={} #the algorithm should calculate one point only once
        
        self.loops=loops
        self.arr=[] #arr of the last step, variation are performed afterwards
        self.calc_arr=[] #for calculation in pf
        self.init_threshold=-1000 
        self.best_arrs=[]
        self.best_arrs_ret=[]
        self.best_end_arrs=[]
        self.best_all=[]
        self.best_all_ret=self.init_threshold
        
    def log(
            self,
            text: str,
            pr: bool=False
            ):
        '''
        Write a log file

        Arguments
        ----------
           text: text to be added to the log file
           pr: print it in the console
        '''
        if not "filename" in self.__dir__():
            self.filename="strat"
        
        with open(os.path.join(os.path.dirname(__file__), "output/"+ self.filename+".txt"), "a") as f:
            f.write("\n"+str(text))  
            
        if pr:
            print(text) 
            
    def calculate_eq_ret(self,pf,mode: int):
        '''
        Calculate an equivalent score for a portfolio  
        
        Arguments
        ----------
           pf: vbt portfolio
        '''  
        rb=pf.total_market_return.values
        rr=pf.get_total_return().values
        delta=rr-rb
        
        #check that there is no extrem value that bias the whole result
        #if it the case, this value is not considered in the calculation of the score
        while np.std(delta)>10:
            ii=np.argmax(delta)
            delta=np.delete(delta,ii,0)
            rb=np.delete(rb,ii,0)
            rr=np.delete(rr,ii,0)
        
        m_rb=np.mean(rb)
        m_rr=np.mean(rr)
        if abs(m_rb)<0.1: #avoid division by zero
            p=(m_rr)/ 0.1*np.sign(m_rb)   
        else:
            p=(m_rr)/ abs(m_rb)
            
        if mode==-1:
            return 2*p*(p<0) + p*(p>0) #wrong direction for the return are penalyzed
        elif mode==1:
            return -2*p*(p>0) -p*(p<0) 

    def variate(self, best_arrs_ret: list):
        '''
        Variates the threshold
        
        Arguments
        ----------
           best_arrs_ret: array of the best returns
        ''' 
        best_arrs_cand=[]
        best_ret_cand=self.init_threshold
        
        for nb in range(3): #
            for var in range(-10,11):
                self.calc_arr=self.arr.copy()
                if not (nb==1 and self.calc_arr[nb]*(1+var*0.01)>self.calc_arr[0]): #uncertain above threshold makes no sense
                    self.calc_arr[nb]=self.calc_arr[nb]*(1+var*0.01)
                    best_arrs_cand, best_ret_cand=self.calculate_pf(best_arrs_cand, best_ret_cand, best_arrs_ret)

        return best_arrs_cand, best_ret_cand                

    def random(self):
        '''
        Generate random thresholds
        ''' 
        arr=[]
        threshold=np.random.rand(1)*5*0.01
        uncertain=1000
        arr.append(threshold) #threshold, range 0-5
        
        while uncertain>threshold:
            uncertain=np.random.rand(1)*5*0.01  #threshold uncertain, range 0-5
            
        arr.append(uncertain)
        arr.append(np.random.rand(1)*15*0.01) #deadband
        return arr
    
    def macro_mode(self,mode_to_vis:int):
        '''
        Set an entry, when a macro mode is entered, and an exit, when it is exited
        
        Arguments
        ----------
           mode_to_vis: selected macro_mode
        '''
        self.ents={}
        self.exs={}

        for ind in self.indexes:
            t=VBTMACROTREND.run(self.close_dic[ind],
                           threshold=self.calc_arr[0],
                           threshold_uncertain=self.calc_arr[1],
                           deadband=self.calc_arr[2]
                           )
            t=VBTMACROVIS.run(t.macro_trend,mode_to_vis=mode_to_vis)
            self.ents[ind]=t.entries
            self.exs[ind]=t.exits

    def calculate_pf(
            self,
            best_arrs_cand,
            best_ret_cand,
            best_arrs_ret):
        '''
        To calculate a portfolio from strategy arrays
        
        Arguments
        ----------
           best_arrs_cand: table containing the best candidate by the strategy array presently tested
           best_ret_cand: table containing the return of the best candidate by the strategy array presently tested
           best_arrs_ret: table containing the return of the best candidate by the strategy array of the whole loop
        '''  
        ret=0
       
        for mode in [-1,1]:
            self.macro_mode(mode)
            for ind in self.indexes:
                pf=vbt.Portfolio.from_signals(self.close_dic[ind], self.ents[ind],self.exs[ind],
                                          freq="1d")
                ret+=self.calculate_eq_ret(pf,mode)
        
        if ret> best_arrs_ret and ret>best_ret_cand:
            return self.calc_arr, ret
        
        return best_arrs_cand, best_ret_cand   
 
    def perf(self):
        '''
        Main fonction to optimize a strategy
        '''  
        for jj in range(self.loops):
            print("loop " + str(jj))
            self.log("loop " + str(jj))
            
            #new start point
            self.arr=self.random()
            self.calc_arr=self.arr.copy()
            
            best_arrs_cand, best_ret_cand=self.calculate_pf([],self.init_threshold,self.init_threshold) #reset 
            if best_ret_cand>self.init_threshold: #normally true
                self.best_arrs.append(best_arrs_cand)
                self.best_arrs_ret.append(best_ret_cand)
            
            #start divergence
            calc=True
            
            while calc:
                print("next calc")
                last_best_ret_cand=best_ret_cand
                best_arrs_cand, best_ret_cand=self.variate(best_ret_cand)
                if best_ret_cand>self.init_threshold:
                    self.best_arrs.append(best_arrs_cand)
                    self.best_arrs_ret.append(best_ret_cand)
                    self.log(best_arrs_cand)
                    self.log(best_ret_cand)
                    
                    #next step
                    self.arr=best_arrs_cand
                else:
                    calc=False
                    if last_best_ret_cand>self.init_threshold:
                        self.best_arrs.append(best_arrs_cand)
                        self.best_arrs_ret.append(last_best_ret_cand)
                        
                        if self.best_all_ret==self.init_threshold or self.best_arrs_ret[-1]>self.best_all_ret:
                            self.best_all=self.best_arrs[-2]
                            self.best_all_ret=self.best_arrs_ret[-1]
                        
            self.log("algorithm completed")                        
            self.log("best of all")
            self.log({'arr':self.best_all})
            self.log("return : " + str(self.best_all_ret))
            