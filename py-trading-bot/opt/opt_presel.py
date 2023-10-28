from core import presel
from core.presel import PreselWQ

import vectorbtpro as vbt
from vectorbtpro.utils.config import Config
import numpy as np

from opt.opt_main import OptMain

'''
Script to optimize the underlying combination of patterns/signals used for a given preselection strategy

The optimization takes place on the actions from CAC40, DAX and Nasdaq
Parameters very good on some actions but very bad for others should not be selected

The optimization algorithm calculates one point, look for the points around it and select the best one
As it can obviously lead to local maximum, the starting point is selected in a random manner
'''

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

class Opt(OptMain):
    def __init__(
            self,
            class_name: str,
            period: str,
            filename:str="presel",
            **kwargs):
        super().__init__(period,filename=filename,
                         indexes=["CAC40","DAX","NASDAQ","FIN","HEALTHCARE","INDUSTRY"], #with only CAC40, DAX and Nasdaq it overfits
                         **kwargs)
        self.pr={}
        
        for ind in self.indexes:
            if class_name[6:8].lower()=="wq":
                nb=int(class_name[8:])
                self.pr[ind]=PreselWQ(period,nb=nb, symbol_index=ind)
            else:
                PR=getattr(presel,class_name)
                self.pr[ind]=PR(period, symbol_index=ind)
                
            #we create pr as an empty shell. The input comes from ust and are brought later in calculate_pf_sub

            #no run otherwise it will crash, as ust is not splited

    def calculate_eq_ret(self,pf,ind:str):
        '''
        Calculate an equivalent score for a portfolio  
        
        Arguments
        ----------
           pf: vbt portfolio
        ''' 
        m_rb=pf.total_market_return
        m_rr=pf.get_total_return()
        self.row["return_"+ind]=m_rr
        self.row["delta_"+ind]=m_rr-m_rb
        
        if abs(m_rb)<0.1: #avoid division by zero
            p=(m_rr)/ 0.1*np.sign(m_rb)   
        else:
            p=(m_rr- m_rb )/ abs(m_rb)

        self.row["surperf_factor_"+ind]=p
        return 4*p*(p<0) + p*(p>0) #wrong direction for the return are penalyzed
    
    def calculate_pf_sub(self,dic):
        pf_dic={}
        
        #perform all call for total and later get other dics
        self.defi_ent("total")
        self.defi_ex("total")
        self.macro_mode("total")
        
        for ind in self.indexes: #CAC, DAX, NASDAQ
            self.pr[ind].close=self.close_dic[ind]["total"]
            self.pr[ind].reinit() #in case the function was called ealier
            self.pr[ind].ust.entries=self.ents[ind]
            self.pr[ind].ust.exits=self.exs[ind]
            self.pr[ind].ust.entries_short=self.ents_short[ind]
            self.pr[ind].ust.exits_short=self.exs_short[ind]
            self.pr[ind].run(skip_underlying=True)

        for ind in self.indexes: #CAC, DAX, NASDAQ
            #restrain to size of total/learn/test
            i=self.close_dic[ind][dic].index
            self.ents[ind]=self.pr[ind].entries.loc[i]
            self.exs[ind]=self.pr[ind].exits.loc[i]
            self.ents_short[ind]=self.pr[ind].entries_short.loc[i]
            self.exs_short[ind]=self.pr[ind].exits_short.loc[i]
                            
            pf_dic[ind]=vbt.Portfolio.from_signals(self.data_dic[ind][dic],
                                          self.ents[ind],
                                          self.exs[ind],
                                          short_entries=self.ents_short[ind],
                                          short_exits=self.exs_short[ind],
                                          freq="1d",
                                          fees=self.fees,
                                          call_seq='auto',
                                          cash_sharing=True
                                          ) #stop_exit_price="close"
        
        return pf_dic
    
    def calculate_pf(
            self,
            dic: str="learn",
            verbose: bool=False,
            bypass_tested_arrs: bool=False
            )-> (list, list):
        '''
        To calculate a portfolio from strategy arrays
        
        Arguments
        ----------
           best_arrs_cand: table containing the best candidate by the strategy array presently tested
           best_ret_cand: table containing the return of the best candidate by the strategy array presently tested
           best_arrs_ret: table containing the return of the best candidate by the strategy array of the whole loop
        '''
        if not self.check_tested_arrs() and not "test" in dic and not bypass_tested_arrs:
            return 0
        
        #create the underlying strategy
        ret=0
        ret_arr=[]
        
        pf_dic=self.calculate_pf_sub(dic)

        for ind in self.indexes: #CAC, DAX, NASDAQ    
            ret_arr.append(self.calculate_eq_ret(pf_dic[ind],ind))
            
        ret=self.summarize_eq_ret(ret_arr)

        self.row["opt_return"]=ret

        self.trades=len(pf_dic[ind].get_trades().records_arr)
        del pf_dic

        self.append_row()
        return 1

           