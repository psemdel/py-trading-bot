import vectorbtpro as vbt
from vectorbtpro.utils.config import Config
import numpy as np
import pandas as pd
from opt.opt_main import OptMain

"""
Script to optimize the combination of patterns/signals used for a given strategy

The optimization takes place on the actions from CAC40, DAX and Nasdaq
Parameters very good on some actions but very bad for others should not be selected

The optimization algorithm calculates one point, look for the points around it and select the best one
As it can obviously lead to local maximum, the starting point is selected in a random manner
"""
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
    '''
    Class to optimize strategy
    '''

    def manual_calculate_pf(self,ind,dic,*args): #the order is bull/bear/uncertain
        '''
        To calculate a portfolio from strategy arrays in jupyter for instance
        
        Arguments
        ----------
           ind: index, for instance "CAC40"
           dic: total/learn/test
        '''  
        self.calc_arr=[]
        for arr in args:
            self.calc_arr.append(arr)
        
        self.defi_ent(dic)
        self.defi_ex(dic)
        self.macro_mode(dic)
        pf=vbt.Portfolio.from_signals(self.data_dic[ind]["learn"], 
                                      self.ents[ind]["learn"],
                                      self.exs[ind]["learn"],
                                      short_entries=self.ents_short[ind]["learn"],
                                      short_exits=self.exs_short[ind]["learn"],
                                      tsl_stop=self.tsl,
                                      sl_stop=self.sl,
                                      freq="1d",fees=self.fees)

        print("equivalent return " + str(self.calculate_eq_ret(pf)))
        return pf #for display for instance

    def calculate_pf(
            self,
            dic: str="learn",
            bypass_tested_arrs: bool=False
            ):
        '''
        To calculate a portfolio from strategy arrays
        
        Arguments
        ----------
           dic: key of the dictionnary to be called: "learning", "test", "total"...
           bypass_tested_arrs: should the function tested_arrs be bypassed
        '''
        if (not self.check_tested_arrs()) and not "test" in dic and not bypass_tested_arrs:
            return 0
   
        if self.it_is_index:
            ret_arr=[]
        else:
            ret=0
        
        pf_dic=self.calculate_pf_sub(dic) 

        for ind in self.indexes: #CAC, DAX, NASDAQ
            t=self.calculate_eq_ret(pf_dic[ind],ind)
            if self.it_is_index:
                ret_arr.append(t)
            else:
                ret+=self.calculate_eq_ret(pf_dic[ind],ind)
            self.row["trades_"+ind+"_"+dic]=len(pf_dic[ind].get_trades().records_arr)

        if self.it_is_index:
            self.row["mean_surperf_factor_w_"+ind+"_"+dic+"_raw"]=np.mean(ret_arr)
            while np.std(ret_arr)>10:
                 ii=np.argmax(ret_arr)
                 ret_arr=np.delete(ret_arr,ii,0)
         
            ret=np.mean(ret_arr)
            self.row["mean_surperf_factor_w_"+ind+"_"+dic+"_corrected"]=ret
        else:
            self.row["sum_surperf_factor_w_"+dic+"_all_indexes_corrected"]=ret

        self.row["opt_return"]=ret    #used for the optimization

        if "test" in dic:
            self.log("Overall perf, "+dic+": " + str(ret),pr=True)
        else:
            self.trades=self.row["trades_"+ind+"_"+dic] #arbitrary last
            
        self.append_row()
        del pf_dic
        return 1

            

     